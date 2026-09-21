# Design Spec: Inbound Production & Inventory Costing (Gói 3)

- **Date:** 2026-09-21
- **Author:** Antigravity Agent
- **Target Branch:** `dev`
- **Scope:** E-commerce API (`services/ecommerce-api`) & Storefront UI (`apps/storefront`)
- **Status:** Approved / In Review

---

## 1. Executive Summary & Business Goals

Hệ thống **Inbound Production & Inventory Costing (Gói 3)** phục vụ mô hình kinh doanh thời trang tự sản xuất (In-house Manufacturing / Brand Owner D2C - Direct to Consumer), loại bỏ các thủ tục trung gian cồng kềnh của mô hình đại lý/nhà cung cấp bên ngoài. Hệ thống cho phép xưởng may/nhà xưởng nội bộ bàn giao thành phẩm trực tiếp vào Kho tổng trung tâm với số lượng linh hoạt, tự động tính toán và cập nhật Giá vốn hàng bán (COGS) theo phương pháp **Bình quân gia quyền di động (Moving Weighted Average Cost)**, đồng thời đóng băng (snapshot) giá vốn tại thời điểm bán hàng cho cả kênh Online và POS.

### Mục tiêu chính:
1. **Quy trình Nhập kho Sản xuất tinh gọn:** Cho phép lập phiếu nhập kho thành phẩm từ xưởng sản xuất, nhập số lượng không giới hạn kèm chi phí sản xuất xuất xưởng (`unit_cost_vnd`).
2. **Tính toán Giá vốn Bình quân Gia quyền Di động (Moving Weighted Average Costing):** Mỗi lần nhập lô hàng mới với chi phí may khác nhau, hệ thống tự động tái tính toán giá vốn của sản phẩm (`product_variants.cost_price_vnd`) dựa trên tỷ trọng giữa tồn kho cũ và lô hàng mới.
3. **Đóng băng Giá vốn Lịch sử (COGS Snapshotting):** Cập nhật cả Online Checkout và POS Checkout để lưu trực tiếp `order_items.cost_price_vnd = variant.cost_price_vnd` tại thời điểm mua, bảo toàn giá vốn lịch sử để tính chính xác Lợi nhuận gộp (Gross Profit) ở Gói 4.
4. **Audit Trail & Tính nhất quán Tồn kho:** Tự động tăng tồn kho nguyên tử (`on_hand += quantity` và `opening_on_hand += quantity`) đảm bảo tuân thủ check constraint `on_hand <= opening_on_hand` của database, đồng thời ghi log giao dịch `inventory_transactions` với `movement_type='inbound'`.
5. **Giao diện Quản trị Trực quan:** Trang `/admin/inbound` theo dõi lịch sử các đợt nhập kho, modal tạo phiếu nhập có tính năng **Xem trước Giá vốn mới theo thời gian thực (Live Costing Preview)**, và hiển thị cột Giá vốn (COGS) trên danh sách sản phẩm `/admin/products`.

---

## 2. Database Models & Schema Specifications

### 2.1. Bảng Phiếu Nhập Kho Sản Xuất (`inbound_receipts`)
- `receipt_id`: BIGINT UNSIGNED, PK, AUTO_INCREMENT
- `public_id`: UUID / GUID, Unique
- `receipt_code`: VARCHAR(64), Unique (Định dạng: `INB-YYYYMMDD-XXXXXX`)
- `batch_name`: VARCHAR(255), Tên đợt sản xuất / xưởng may (Ví dụ: *"Xưởng may 1 - Lô sơ mi Thu Đông đợt 2"*).
- `status`: VARCHAR(24), `'completed'` (xác nhận nhập kho thành công).
- `total_items_count`: INT UNSIGNED, Tổng số lượng thành phẩm nhập trong phiếu ($> 0$).
- `total_cost_vnd`: BIGINT UNSIGNED, Tổng chi phí sản xuất của cả phiếu ($\sum quantity \times unit\_cost\_vnd$).
- `notes`: TEXT, Ghi chú chất lượng may/tiến độ xưởng.
- `created_by_customer_id`: BIGINT UNSIGNED, FK `customers.customer_id` (Admin/Thủ kho thực hiện).
- `created_at`: DATETIME(6), DEFAULT CURRENT_TIMESTAMP(6)
- `updated_at`: DATETIME(6), ON UPDATE CURRENT_TIMESTAMP(6)

### 2.2. Bảng Chi Tiết Mặt Hàng Nhập (`inbound_receipt_items`)
- `item_id`: BIGINT UNSIGNED, PK, AUTO_INCREMENT
- `public_id`: UUID / GUID, Unique
- `receipt_id`: BIGINT UNSIGNED, FK `inbound_receipts.receipt_id` ON DELETE CASCADE
- `variant_id`: BIGINT UNSIGNED, FK `product_variants.variant_id` ON DELETE RESTRICT
- `quantity`: INT UNSIGNED, Số lượng thành phẩm nhập ($quantity > 0$).
- `unit_cost_vnd`: BIGINT UNSIGNED, Chi phí sản xuất xuất xưởng cho 1 đơn vị ($unit\_cost\_vnd \ge 0$).
- `total_cost_vnd`: BIGINT UNSIGNED, Thành tiền dòng ($quantity \times unit\_cost\_vnd$).
- `previous_cost_price_vnd`: BIGINT UNSIGNED, Giá vốn của variant trước khi nhập phiếu này.
- `new_cost_price_vnd`: BIGINT UNSIGNED, Giá vốn bình quân mới của variant sau khi nhập phiếu này.
- `created_at`: DATETIME(6)

### 2.3. Bảng Tồn Kho (`inventory`) & Giao Dịch Kho (`inventory_transactions`)
- **`inventory`**:
  - Khi nhập kho lô sản xuất mới:
    - Tăng tồn kho khả dụng: `inventory.on_hand += quantity`
    - Tăng tồn kho lũy kế: `inventory.opening_on_hand += quantity` *(đảm bảo ràng buộc `on_hand <= opening_on_hand` luôn thỏa mãn)*
    - Tăng phiên bản lạc quan: `inventory.version += 1`
    - Cập nhật thời gian: `inventory.updated_at = now()`
- **`inventory_transactions`**:
  - Thêm một bản ghi chuyển động kho:
    - `variant_id`: `item.variant_id`
    - `location_type`: `'central_warehouse'`
    - `movement_type`: `'inbound'`
    - `quantity_delta`: `+item.quantity`
    - `reference_code`: `receipt_code`
    - `notes`: `f"Nhập kho thành phẩm: {batch_name}"`

---

## 3. Costing & Business Logic Algorithms

### 3.1. Thuật toán Moving Weighted Average Costing
Mỗi khi có một lô hàng thành phẩm mới từ xưởng nhập vào Kho tổng trung tâm:

- Ký hiệu:
  - $Q_{\text{current}}$: Số lượng tồn kho thực tế hiện có trong Kho tổng (`inventory.on_hand`).
  - $C_{\text{current}}$: Giá vốn hiện tại của sản phẩm (`variant.cost_price_vnd`).
  - $Q_{\text{inbound}}$: Số lượng thành phẩm nhập thêm từ xưởng (`item.quantity`).
  - $C_{\text{inbound}}$: Chi phí sản xuất xuất xưởng của lô mới (`item.unit_cost_vnd`).

- **Công thức tính Giá vốn mới ($C_{\text{new}}$):**
  $$\text{Nếu } Q_{\text{current}} + Q_{\text{inbound}} > 0:$$
  $$C_{\text{new}} = \text{round}\left(\frac{(Q_{\text{current}} \times C_{\text{current}}) + (Q_{\text{inbound}} \times C_{\text{inbound}})}{Q_{\text{current}} + Q_{\text{inbound}}}\right)$$

- **Xử lý trường hợp biên (Edge cases):**
  1. Sản phẩm mới sản xuất lần đầu hoặc đã bán sạch tồn kho ($Q_{\text{current}} = 0$):
     $$C_{\text{new}} = C_{\text{inbound}}$$
  2. $C_{\text{inbound}} = 0$: Giá vốn được pha loãng tương ứng với số lượng nhập miễn phí/thành phẩm tồn đọng.
  3. Giá trị $C_{\text{new}}$ được lưu trực tiếp vào `product_variants.cost_price_vnd`.

### 3.2. Đóng Băng Giá Vốn Khi Bán Hàng (COGS Snapshotting)
Để phục vụ việc tính toán Lợi nhuận gộp chính xác cho Gói 4:
- **Online Checkout (`services/ecommerce-api/app/modules/checkout/service.py`)**:
  Khi khởi tạo danh sách `OrderItem`:
  ```python
  OrderItem(
      ...,
      unit_price_vnd=variant.price_vnd,
      cost_price_vnd=variant.cost_price_vnd, # Snapshot giá vốn tại thời điểm bán
      quantity=quantity,
      line_total_vnd=line_total,
  )
  ```
- **POS Checkout (`services/ecommerce-api/app/modules/pos/service.py`)**:
  Khi nhân viên tạo đơn tại quầy:
  ```python
  OrderItem(
      ...,
      unit_price_vnd=item_data["unit_price_vnd"],
      cost_price_vnd=variant.cost_price_vnd, # Snapshot giá vốn tại thời điểm bán POS
      quantity=item_data["quantity"],
      line_total_vnd=item_data["line_total_vnd"],
  )
  ```

---

## 4. Backend REST API Specification

Module `services/ecommerce-api/app/modules/inbound/` (`schemas.py`, `service.py`, `router.py`):

### 4.1. `POST /api/v1/admin/inbound/receipts`
- **Mục đích:** Tạo phiếu nhập kho và hoàn tất nhập hàng vào Kho tổng ngay lập tức.
- **Headers:** `Idempotency-Key` (bắt buộc, 1-64 ký tự).
- **Yêu cầu bảo mật:** `get_current_admin`, `verify_csrf`.
- **Request Body (`CreateInboundReceiptPayload`):**
  ```json
  {
    "batch_name": "Lô sản xuất Đợt 3 Thu Đông - Xưởng 1",
    "notes": "Kiểm đếm 100% đạt chuẩn chất lượng may xuất xưởng",
    "items": [
      {
        "variant_id": 12,
        "quantity": 50,
        "unit_cost_vnd": 120000
      },
      {
        "variant_id": 13,
        "quantity": 100,
        "unit_cost_vnd": 135000
      }
    ]
  }
  ```
- **Xác thực dữ liệu (Validation):**
  - `batch_name`: chuỗi từ 3 đến 255 ký tự.
  - `items`: danh sách từ 1 đến 200 mục.
  - Chặn trùng lặp `variant_id` trong cùng một phiếu nhập (HTTP 422).
  - `quantity >= 1`, `unit_cost_vnd >= 0`.
  - Tất cả các `variant_id` phải tồn tại trong cơ sở dữ liệu.
- **Thực thi trong một Database Transaction:**
  - Khóa dòng `Inventory` bằng `with_for_update()` theo `variant_id`. Nếu chưa có bản ghi tồn kho, tự động tạo mới `Inventory(opening_on_hand=0, on_hand=0)`.
  - Khóa dòng `ProductVariant` bằng `with_for_update()` để cập nhật giá vốn.
  - Tính `new_cost_price_vnd` cho từng item.
  - Cập nhật `variant.cost_price_vnd = new_cost_price_vnd`.
  - Cập nhật `inventory.on_hand += item.quantity`, `inventory.opening_on_hand += item.quantity`.
  - Thêm bản ghi `InventoryTransaction(movement_type='inbound')`.
  - Lưu `InboundReceipt` và `InboundReceiptItem`.
- **Response:** `InboundReceiptDetailResponse` (Mã HTTP 201 Created).

### 4.2. `GET /api/v1/admin/inbound/receipts`
- **Mục đích:** Lấy danh sách lịch sử các phiếu nhập kho.
- **Query Parameters:** `search` (mã phiếu, tên đợt), `limit` (mặc định 20, max 100), `offset` (mặc định 0).
- **Response:** `InboundReceiptListResponse`:
  ```json
  {
    "items": [
      {
        "receipt_id": 1,
        "receipt_code": "INB-20260921-A1B2C3",
        "batch_name": "Lô sản xuất Đợt 3 Thu Đông - Xưởng 1",
        "status": "completed",
        "total_items_count": 150,
        "total_cost_vnd": 19500000,
        "created_by_name": "Admin Tran",
        "created_at": "2026-09-21T15:30:00Z"
      }
    ],
    "total": 1
  }
  ```

### 4.3. `GET /api/v1/admin/inbound/receipts/{receipt_code}`
- **Mục đích:** Xem chi tiết một phiếu nhập kho và bảng đối chiếu giá vốn trước/sau nhập.
- **Response:** `InboundReceiptDetailResponse` gồm danh sách đầy đủ các items kèm `previous_cost_price_vnd` và `new_cost_price_vnd`.

### 4.4. Cập nhật `AdminVariantResponse` trong `/api/v1/admin/products`
- Bổ sung trường `cost_price_vnd: int = 0` trong `AdminVariantResponse` để hiển thị trên bảng danh sách sản phẩm Admin.

---

## 5. Frontend Storefront & Admin Portal Architecture

### 5.1. API Client Functions & Types (`apps/storefront/src/lib/commerce.ts` & `api.ts`)
- Thêm types: `InboundReceiptSummary`, `InboundReceiptItemDetail`, `InboundReceiptDetail`, `CreateInboundReceiptInput`.
- Thêm functions:
  - `getAdminInboundReceipts(params?: { search?: string; limit?: number; offset?: number })`
  - `getAdminInboundReceiptDetail(receiptCode: string)`
  - `createAdminInboundReceipt(input: CreateInboundReceiptInput, idempotencyKey: string)`

### 5.2. Thanh Điều Hướng (`apps/storefront/src/components/AdminNav.tsx`)
- Thêm tab: `{ href: "/admin/inbound", label: "Nhập kho sản xuất", icon: "box" }`.

### 5.3. Trang Quản Lý Nhập Kho (`apps/storefront/src/app/admin/inbound/page.tsx`)
- Thẻ thống kê: Tổng số đợt nhập xưởng, Tổng sản phẩm nhập kho, Tổng chi phí sản xuất tích lũy.
- Thanh tìm kiếm và nút bấm mở modal **"Tạo phiếu nhập mới"**.
- Bảng danh sách phiếu nhập kho: Mã phiếu (link đến chi tiết), Tên lô sản xuất, Số lượng sản phẩm, Tổng chi phí thành phẩm, Ngày nhập, Người thực hiện.

### 5.4. Modal Tạo Phiếu Nhập Kho (`apps/storefront/src/components/admin/CreateInboundModal.tsx`)
- Nhập Tên đợt may / xưởng sản xuất và Ghi chú.
- Danh sách chọn sản phẩm:
  - Tìm kiếm sản phẩm theo tên hoặc SKU.
  - Hiển thị Tồn kho hiện tại & Giá vốn hiện tại.
  - Ô nhập Số lượng thành phẩm ($quantity > 0$) và Đơn giá xuất xưởng ($unit\_cost\_vnd \ge 0$).
  - **Tính năng Live Costing Preview:** Tự động tính trước Giá vốn bình quân dự kiến sau khi nhập để quản trị viên đối soát trước khi duyệt.
- Nút "Xác nhận Nhập kho" sinh `Idempotency-Key` ngẫu nhiên và gửi API.

### 5.5. Trang Chi Tiết Phiếu Nhập (`apps/storefront/src/app/admin/inbound/[receiptCode]/page.tsx`)
- Card thông tin chung về đợt sản xuất.
- Bảng chi tiết sản phẩm: Tên sản phẩm, SKU, Size, Màu, Số lượng, Đơn giá xưởng, Cột biến động **Giá vốn cũ $\rightarrow$ Giá vốn mới**, Thành tiền.

### 5.6. Bảng Quản Lý Sản Phẩm (`apps/storefront/src/app/admin/products/page.tsx`)
- Bổ sung cột **Giá vốn (COGS)** cạnh Giá bán trong bảng biến thể sản phẩm.

---

## 6. Testing & Verification Strategy

1. **Backend Tests (`services/ecommerce-api/tests/test_inbound_costing_api.py`):**
   - Test tạo phiếu nhập kho thành công:
     - Tồn kho `on_hand` và `opening_on_hand` tăng chính xác.
     - `InventoryTransaction(movement_type='inbound')` được tạo đầy đủ.
     - Giá vốn `ProductVariant.cost_price_vnd` cập nhật đúng theo công thức Weighted Average.
     - Bảng `inbound_receipt_items` lưu đúng `previous_cost_price_vnd` và `new_cost_price_vnd`.
   - Test trường hợp tồn kho cũ = 0: Giá vốn mới = Đơn giá nhập mới.
   - Test validation: Chặn trùng lặp `variant_id`, chặn $quantity \le 0$, chặn $unit\_cost < 0$.
   - Test COGS Snapshot:
     - Test Online Checkout lưu đúng `OrderItem.cost_price_vnd = variant.cost_price_vnd`.
     - Test POS Checkout lưu đúng `OrderItem.cost_price_vnd = variant.cost_price_vnd`.
   - Đảm bảo 146 backend tests hiện có tiếp tục pass 100% (0 regression).
2. **Frontend Typecheck & Build:**
   - Chạy `npm --prefix apps/storefront run typecheck` (0 errors).
   - Chạy `npm --prefix apps/storefront run build` (26/26 routes build pass).
