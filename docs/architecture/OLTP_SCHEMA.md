# OLTP Schema Reference

Tài liệu tham chiếu schema OLTP MySQL của hệ thống D&K E-Commerce (TLCN).
Kết hợp thiết kế logic, column-level reference, transaction catalog và reconciliation.

---

## 1. Phạm vi và quy tắc thiết kế

Schema tuân theo `skills/oltp-design/SKILL.md`: grain rõ ràng, chuẩn hóa dữ liệu ghi, snapshot dữ liệu giao dịch, transaction ngắn, khóa theo thứ tự ổn định và invariant được bảo vệ ở tầng thấp nhất phù hợp.

Hệ thống có **25 bảng nghiệp vụ** (sau Migration `0014_logistics_returns_inbound_cogs.py`). Pipeline Lakehouse DE trích xuất **24 bảng**; bảng `customer_credentials` bị loại bỏ vì chứa thông tin xác thực nhạy cảm. Không có bảng analytics/star schema nằm trong MySQL ecommerce (toàn bộ phân tích nằm trên Lakehouse Iceberg / Trino).

### Quy tắc thiết kế cốt lõi

- Checkout yêu cầu đăng nhập và active cart có hàng hợp lệ. Hỗ trợ phương thức thanh toán `vietqr` và `cod`.
- Add-to-cart không giữ hàng; checkout kiểm tra và trừ `inventory.on_hand` atomically, đồng thời ghi nhận 1 transaction `movement_type = 'outbound_order'` trong `inventory_transactions`.
- Với đơn `vietqr`, thanh toán thành công ngay khi checkout hợp lệ; với đơn `cod`, đơn được tạo với trạng thái ban đầu `confirmed` chờ điều phối giao vận.
- POS (Point of Sale): nhân viên bán hàng tại quầy, tạo đơn `completed` ngay, trừ `store_inventory` (kho cửa hàng), ghi nhận transaction `outbound_pos`.
- Giao vận nội bộ D&K: Mỗi đơn hàng online đi qua đội ngũ shipper nội bộ (`delivery_staff`) thông qua phiếu giao hàng (`shipments`).
- State machine mở rộng của đơn hàng:

```text
[Online VietQR] paid ────> confirmed ────> shipping ────> delivered ────> completed
                         │               │             │               │
                         │               │             └──> returned <─┘
                         │               └──> failed_delivery (boom COD)
                         └──> cancelled

[Online COD]    confirmed ──> shipping ──> delivered (thu tiền COD) ──> completed
                            │           │
                            │           └──> failed_delivery (boom COD / bom hàng)
                            └──> cancelled
```

- **Xử lý Boom hàng COD**: Khi đơn hàng bị boom (`failed_delivery`), hệ thống ghi nhận lý do thất bại trong `shipments`, hoàn trả tồn kho (`movement_type = 'return_boom'`), tự động tăng `customers.boom_count`. Nếu `boom_count >= 3`, khách hàng tự động bị gắn cờ `is_cod_blocked = TRUE` (chặn thanh toán COD ở các lần mua sau).
- **Chính sách Đổi/Trả hàng 7 ngày**: Sau khi đơn hàng `delivered`/`completed`, khách hàng có quyền tạo `return_requests` với 2 nhánh nghiệp vụ:
  - `exchange`: Đổi size/màu (tạo yêu cầu kiểm hàng `return_items`, khi duyệt thì xuất hàng đổi `exchange_out`).
  - `refund`: Trả hàng hoàn tiền (khi duyệt và nhận lại hàng thì hoàn tiền `refund_amount_vnd` và nhập kho `return_customer`, trạng thái đơn chuyển sang `returned`).
- **Mô hình Kho tập trung**: 1 Kho trung tâm duy nhất nhập hàng từ xưởng (`movement_type = 'inbound'`) và phân bổ điều phối cho các chi nhánh cửa hàng (`transfer_to_store` / `transfer_received`). Mọi biến động được lưu vết bất biến trong `inventory_transactions`.
- **Giá vốn hàng bán (COGS)**: Ghi nhận giá vốn tại từng biến thể `product_variants.cost_price_vnd` và snapshot cố định bất biến vào từng dòng `order_items.cost_price_vnd` tại thời điểm phát sinh giao dịch.

---

## 2. Quy ước chung

- **PK**: `BIGINT UNSIGNED` auto-increment surrogate key
- **Public ID**: `BINARY(16)` UUIDv5 deterministic — lộ qua API, không lộ PK
- **Tiền**: số nguyên VND (`BIGINT UNSIGNED`), không dùng FLOAT/DOUBLE
- **Thời gian**: UTC `DATETIME(6)` — microsecond precision
- **Bảng mutable**: có `updated_at` + composite cursor `(updated_at, PK)`
- **Bảng append-only**: có `created_at` + composite cursor `(created_at, PK)`
- **FK lịch sử**: `ON DELETE RESTRICT` — giữ audit trail
- **Engine**: InnoDB `READ COMMITTED`
- Giao dịch write dùng `SELECT ... FOR UPDATE` khi quyết định dựa trên dữ liệu mutable.
- Không giữ transaction mở khi gọi dịch vụ ngoài.

---

## 3. Tổng quan 25 bảng

| # | Bảng | Nhóm | Grain | Mutability | Extract cursor |
|---|------|------|-------|------------|----------------|
| 1 | `customers` | Customer | Một customer | Mutable/anonymizable | `(updated_at, customer_id)` |
| 2 | `customer_credentials` | Auth | Một credential/customer | Mutable, không extract | — |
| 3 | `categories` | Catalog | Một category | Mutable/inactive | `(updated_at, category_id)` |
| 4 | `products` | Catalog | Một product | Mutable/archive terminal | `(updated_at, product_id)` |
| 5 | `product_variants` | Catalog | Một tổ hợp size-color/product | Mutable/inactive | `(updated_at, variant_id)` |
| 6 | `inventory` | Inventory | Một balance/variant (kho tổng) | Mutable, khóa khi checkout/cancel | `(updated_at, variant_id)` |
| 7 | `cities` | Location | Một thành phố | Mutable | `(updated_at, city_id)` |
| 8 | `stores` | Location | Một cửa hàng | Mutable | `(updated_at, store_id)` |
| 9 | `store_inventory` | Inventory | Một balance/variant/store | Mutable, khóa khi POS/cancel | `(updated_at, store_id, variant_id)` |
| 10 | `carts` | Cart | Một chu kỳ cart/customer | Mutable lifecycle | `(updated_at, cart_id)` |
| 11 | `cart_items` | Cart | Một variant/cart | Mutable/logical removal | `(updated_at, cart_item_id)` |
| 12 | `wishlist_items` | Wishlist | Một product từng wishlist/customer | Mutable presence | `(updated_at, wishlist_item_id)` |
| 13 | `coupons` | Promotion | Một coupon code | Mutable/archive terminal | `(updated_at, coupon_id)` |
| 14 | `coupon_redemptions` | Promotion | Một redemption/order | Mutable redeemed/released | `(updated_at, coupon_redemption_id)` |
| 15 | `orders` | Order | Một kết quả checkout/POS | Mutable state, snapshot amount | `(updated_at, order_id)` |
| 16 | `order_items` | Order | Một variant line/order | Append-only snapshot | `(created_at, order_item_id)` |
| 17 | `payments` | Payment | Một payment/order | Append-only | `(created_at, payment_id)` |
| 18 | `refunds` | Refund | Một full refund/payment | Append-only | `(created_at, refund_id)` |
| 19 | `order_status_history` | History | Một transition/order | Append-only | `(created_at, order_status_history_id)` |
| 20 | `product_reviews` | Review | Một review/order_item | Mutable visibility | `(updated_at, review_id)` |
| 21 | `delivery_staff` | Logistics | Một nhân viên giao vận shipper D&K | Mutable/anonymizable | `(updated_at, staff_id)` |
| 22 | `shipments` | Logistics | Một phiếu giao hàng nội bộ | Mutable lifecycle & COD | `(updated_at, shipment_id)` |
| 23 | `return_requests` | Returns | Một yêu cầu đổi trả sau mua 7 ngày | Mutable workflow | `(updated_at, return_id)` |
| 24 | `return_items` | Returns | Một món hàng trong yêu cầu đổi trả | Append-only / inspection | `(created_at, return_item_id)` |
| 25 | `inventory_transactions` | Inventory | Một biến động kho (inbound/outbound/...) | Append-only ledger | `(created_at, transaction_id)` |

### Chiến lược định danh

- PK/FK vật lý trong OLTP dùng `BIGINT UNSIGNED` surrogate key để giữ index nhỏ, join nhanh và phù hợp import hàng triệu dòng.
- Thực thể đi qua API dùng `public_id BINARY(16)` chứa UUID; API không để lộ surrogate key nội bộ.
- Generator dùng UUIDv5 deterministic cho `public_id`, `logical_identity`, `generation_run_id` và các khóa kỹ thuật/idempotency.
- `order_number`, SKU, slug, `shipment_code`, `return_code` và coupon code là business key có ý nghĩa hiển thị, nên giữ định dạng nghiệp vụ thay vì biến thành UUID.
- Trong SQL export, UUID được biểu diễn bằng `UUID_TO_BIN('<uuid>')`; Lakehouse chuẩn hóa lại thành chuỗi UUID canonical ở Silver nếu cần.

---

## 4. Quan hệ tổng quát

```text
customers 1───1 customer_credentials
customers 1───n carts 1───n cart_items n───1 product_variants
customers 1───n wishlist_items n───1 products
categories 1───n categories (self-ref)
categories 1───n products 1───n product_variants 1───1 inventory
carts 1───0..1 orders 1───n order_items
orders 1───1 payments 1───0..1 refunds
orders 1───n order_status_history
orders n───0..1 coupons (nullable FK)
coupons 1───n coupon_redemptions n───1 orders
order_items 1───0..1 product_reviews
customers 1───n product_reviews
cities 1───n stores
stores 1───n store_inventory n───1 product_variants
customers n───0..1 stores (store_manager assigned store)

[Logistics & Shipping]
orders 1───0..1 shipments n───1 delivery_staff

[Returns & Exchanges]
orders 1───n return_requests 1───n return_items n───1 order_items
customers 1───n return_requests
return_items n───0..1 product_variants (exchange_variant_id)

[Inventory Transactions Ledger]
product_variants 1───n inventory_transactions
stores 1───n inventory_transactions (nullable store_id cho store transfers/POS)
```


---

## 5. Chi tiết từng bảng

### 5.1. `customers`

**Mục đích**: Identity nghiệp vụ, profile, role và trạng thái account.

| Cột | Kiểu | Constraint | Mô tả |
|-----|------|-----------|-------|
| `customer_id` | `BIGINT UNSIGNED` | PK, auto-increment | Surrogate key nội bộ |
| `public_id` | `BINARY(16)` | UK, NOT NULL | UUIDv5 — public identifier |
| `display_name` | `VARCHAR(120)` | NOT NULL | Tên hiển thị |
| `role` | `VARCHAR(16)` | NOT NULL, DEFAULT `'customer'` | `customer`, `admin`, `store_manager` |
| `status` | `VARCHAR(16)` | NOT NULL, DEFAULT `'active'` | `active` hoặc `inactive` |
| `city_id` | `BIGINT UNSIGNED` | FK → `cities.city_id`, NULLABLE, ON DELETE SET NULL | Thành phố được assign |
| `store_id` | `BIGINT UNSIGNED` | FK → `stores.store_id`, NULLABLE, ON DELETE SET NULL | Cửa hàng được assign (store_manager) |
| `data_origin` | `VARCHAR(16)` | NOT NULL, DEFAULT `'manual'` | `manual` hoặc `synthetic` |
| `generation_run_id` | `VARCHAR(64)` | NULLABLE | ID lần generate (synthetic data) |
| `anonymized_at` | `DATETIME(6)` | NULLABLE | Thời điểm PII bị ẩn danh hóa |
| `is_cod_blocked` | `BOOLEAN` | NOT NULL, DEFAULT `FALSE` | Cờ chặn thanh toán COD khi boom hàng nhiều lần |
| `boom_count` | `INT UNSIGNED` | NOT NULL, DEFAULT `0` | Số lần đặt hàng COD nhưng từ chối nhận (boom hàng) |
| `created_at` | `DATETIME(6)` | NOT NULL, DEFAULT NOW(6) | Thời gian tạo |
| `updated_at` | `DATETIME(6)` | NOT NULL, DEFAULT NOW(6) ON UPDATE | Thời gian cập nhật cuối |

**Check constraints**:
- `status IN ('active', 'inactive')`
- `role IN ('customer', 'admin', 'store_manager')`
- `data_origin IN ('manual', 'synthetic')`

**Indexes**:
- `uq_customers_public_id` — UK trên `public_id`
- `ix_customers_role_status_id` — `(role, status, customer_id)`
- `ix_customers_updated_at_customer_id` — extraction cursor

**Invariant**: Anonymize không xóa PK/FK. `store_manager` phải có `store_id`. Khi `boom_count >= 3`, hệ thống tự động bật `is_cod_blocked = TRUE` để ngăn chặn rủi ro bom hàng COD.


---

### 5.2. `customer_credentials`

**Mục đích**: Password hash cho đúng một customer.

| Cột | Kiểu | Constraint | Mô tả |
|-----|------|-----------|-------|
| `customer_id` | `BIGINT UNSIGNED` | PK/FK → `customers.customer_id`, ON DELETE RESTRICT | 1:1 với customer |
| `email_normalized` | `VARCHAR(320)` | UK, NOT NULL | Email đã normalize |
| `password_hash` | `VARCHAR(255)` | NOT NULL | Bcrypt password hash |
| `is_enabled` | `BOOLEAN` | NOT NULL, DEFAULT `TRUE` | Bật/tắt credential |
| `password_changed_at` | `DATETIME(6)` | NOT NULL, DEFAULT NOW(6) | Lần đổi password cuối |
| `created_at` | `DATETIME(6)` | NOT NULL, DEFAULT NOW(6) | |
| `updated_at` | `DATETIME(6)` | NOT NULL, DEFAULT NOW(6) ON UPDATE | |

**Indexes**:
- `uq_customer_credentials_email_normalized` — UK trên `email_normalized`

**Invariant**: 1:1 với customer. Không cấp quyền cho DE reader và không đưa vào lakehouse.

---

### 5.3. `categories`

**Mục đích**: Phân cấp sản phẩm dạng tree. Product chỉ thuộc category lá.

| Cột | Kiểu | Constraint | Mô tả |
|-----|------|-----------|-------|
| `category_id` | `BIGINT UNSIGNED` | PK, auto-increment | Surrogate key |
| `public_id` | `BINARY(16)` | UK, NOT NULL | UUIDv5 |
| `parent_category_id` | `BIGINT UNSIGNED` | FK → `categories.category_id`, NULLABLE, ON DELETE RESTRICT | Self-reference tạo hierarchy |
| `code` | `VARCHAR(64)` | UK, NOT NULL | Business key (VD: `'AOLOTRINH'`) |
| `name` | `VARCHAR(160)` | NOT NULL | Tên danh mục |
| `is_active` | `BOOLEAN` | NOT NULL, DEFAULT `TRUE` | Bật/tắt tạm thời |
| `created_at` | `DATETIME(6)` | NOT NULL, DEFAULT NOW(6) | |
| `updated_at` | `DATETIME(6)` | NOT NULL, DEFAULT NOW(6) ON UPDATE | |

**Indexes**:
- `uq_categories_code` — UK trên `code`
- `uq_categories_public_id` — UK trên `public_id`
- `ix_categories_parent_is_active_id` — `(parent_category_id, is_active, category_id)`
- `ix_categories_updated_at_category_id` — extraction cursor

**Invariant**: Không tạo chu trình hierarchy. Category lá = không có child.

---

### 5.4. `products`

**Mục đích**: Thông tin chung sản phẩm. Size/color/SKU/giá nằm ở variant.

| Cột | Kiểu | Constraint | Mô tả |
|-----|------|-----------|-------|
| `product_id` | `BIGINT UNSIGNED` | PK, auto-increment | Surrogate key |
| `public_id` | `BINARY(16)` | UK, NOT NULL | UUIDv5 |
| `category_id` | `BIGINT UNSIGNED` | FK → `categories.category_id`, NOT NULL, ON DELETE RESTRICT | Danh mục cha |
| `slug` | `VARCHAR(180)` | UK, NOT NULL | SEO-friendly URL slug |
| `name` | `VARCHAR(200)` | NOT NULL | Tên sản phẩm |
| `description` | `TEXT` | NULLABLE | Mô tả chi tiết |
| `image_url` | `VARCHAR(1024)` | NULLABLE | URL hình ảnh chính |
| `is_active` | `BOOLEAN` | NOT NULL, DEFAULT `TRUE` | Bật/tắt tạm thời |
| `archived_at` | `DATETIME(6)` | NULLABLE | Thời điểm archive (terminal) |
| `archived_by_customer_id` | `BIGINT UNSIGNED` | FK → `customers.customer_id`, NULLABLE, ON DELETE RESTRICT | Admin thực hiện archive |
| `archive_reason` | `VARCHAR(500)` | NULLABLE | Lý do archive (≥3 ký tự) |
| `created_at` | `DATETIME(6)` | NOT NULL, DEFAULT NOW(6) | |
| `updated_at` | `DATETIME(6)` | NOT NULL, DEFAULT NOW(6) ON UPDATE | |

**Check constraints**:
- `archived_at IS NULL AND archived_by_customer_id IS NULL AND archive_reason IS NULL`
  **OR** `archived_at IS NOT NULL AND archived_by_customer_id IS NOT NULL AND archive_reason IS NOT NULL AND LENGTH(TRIM(archive_reason)) >= 3`
- `archived_at IS NULL OR is_active = FALSE` — archive buộc inactive

**Indexes**:
- `uq_products_slug` — UK trên `slug`
- `uq_products_public_id` — UK trên `public_id`
- `ix_products_category_id_is_active_product_id` — `(category_id, is_active, product_id)`
- `ix_products_is_active_product_id` — `(is_active, product_id)`
- `ix_products_updated_at_product_id` — extraction cursor
- `ix_products_archived_at_product_id` — `(archived_at, product_id)`

**Invariant**: Archive là terminal — không cascade sang variant, wishlist hay order item. FK actor dùng `ON DELETE RESTRICT` để giữ audit.

---

### 5.5. `product_variants`

**Mục đích**: Tổ hợp size-color-SKU-giá cho mỗi product.

| Cột | Kiểu | Constraint | Mô tả |
|-----|------|-----------|-------|
| `variant_id` | `BIGINT UNSIGNED` | PK, auto-increment | Surrogate key |
| `public_id` | `BINARY(16)` | UK, NOT NULL | UUIDv5 |
| `product_id` | `BIGINT UNSIGNED` | FK → `products.product_id`, NOT NULL, ON DELETE RESTRICT | Product cha |
| `sku` | `VARCHAR(64)` | UK, NOT NULL | Mã SKU duy nhất |
| `size_code` | `VARCHAR(32)` | NOT NULL | Mã size (VD: `'M'`, `'XL'`) |
| `color_code` | `VARCHAR(64)` | NOT NULL | Mã màu (VD: `'DEN'`) |
| `price_vnd` | `BIGINT UNSIGNED` | NOT NULL | Giá bán niêm yết (VND, integer) |
| `cost_price_vnd` | `BIGINT UNSIGNED` | NOT NULL, DEFAULT `0` | Giá vốn hàng bán (COGS, VND, integer) |
| `is_active` | `BOOLEAN` | NOT NULL, DEFAULT `TRUE` | Bật/tắt |
| `created_at` | `DATETIME(6)` | NOT NULL, DEFAULT NOW(6) | |
| `updated_at` | `DATETIME(6)` | NOT NULL, DEFAULT NOW(6) ON UPDATE | |

**Check constraints**:
- `price_vnd >= 0`
- `cost_price_vnd >= 0`
- `UNIQUE (product_id, size_code, color_code)` — ngăn trùng tổ hợp


**Indexes**:
- `uq_product_variants_sku` — UK trên `sku`
- `uq_product_variants_public_id` — UK trên `public_id`
- `uq_product_variants_product_size_color` — composite UK
- `ix_product_variants_product_id_is_active_variant_id` — `(product_id, is_active, variant_id)`
- `ix_product_variants_updated_at_variant_id` — extraction cursor

---

### 5.6. `inventory`

**Mục đích**: Số dư tồn kho kho tổng cho mỗi variant. Khóa row khi checkout/cancel.

| Cột | Kiểu | Constraint | Mô tả |
|-----|------|-----------|-------|
| `variant_id` | `BIGINT UNSIGNED` | PK/FK → `product_variants.variant_id`, ON DELETE RESTRICT | 1:1 với variant |
| `opening_on_hand` | `BIGINT UNSIGNED` | NOT NULL | Số lượng tồn đầu kỳ |
| `on_hand` | `BIGINT UNSIGNED` | NOT NULL | Số lượng tồn hiện tại |
| `version` | `BIGINT UNSIGNED` | NOT NULL, DEFAULT `0` |乐观锁 — tăng khi checkout/cancel |
| `updated_at` | `DATETIME(6)` | NOT NULL, DEFAULT NOW(6) ON UPDATE | |

**Check constraints**:
- `opening_on_hand >= 0`
- `on_hand >= 0`
- `on_hand <= opening_on_hand` — không có reservation/backorder

**Indexes**:
- `ix_inventory_updated_at_variant_id` — extraction cursor

**Invariant**: `0 <= on_hand <= opening_on_hand`. Version tăng khi có thay đổi để detect conflict và hỗ trợ extraction. Online checkout chỉ trừ `inventory`; POS chỉ trừ `store_inventory`.

---

### 5.7. `cities`

**Mục đích**: Danh sách thành phố nơi có cửa hàng.

| Cột | Kiểu | Constraint | Mô tả |
|-----|------|-----------|-------|
| `city_id` | `BIGINT UNSIGNED` | PK, auto-increment | Surrogate key |
| `code` | `VARCHAR(32)` | UK, NOT NULL | Mã thành phố (VD: `'HCM'`, `'HN'`, `'DN'`) |
| `name` | `VARCHAR(120)` | NOT NULL | Tên thành phố |
| `is_active` | `BOOLEAN` | NOT NULL, DEFAULT `TRUE` | Bật/tắt |
| `created_at` | `DATETIME(6)` | NOT NULL, DEFAULT NOW(6) | |
| `updated_at` | `DATETIME(6)` | NOT NULL, DEFAULT NOW(6) ON UPDATE | |

**Indexes**:
- `uq_cities_code` — UK trên `code`
- `ix_cities_updated_at_city_id` — extraction cursor

**Invariant**: `code` unique. City inactive không tạo store mới.

---

### 5.8. `stores`

**Mục đích**: Cửa hàng vật lý trong thành phố.

| Cột | Kiểu | Constraint | Mô tả |
|-----|------|-----------|-------|
| `store_id` | `BIGINT UNSIGNED` | PK, auto-increment | Surrogate key |
| `city_id` | `BIGINT UNSIGNED` | FK → `cities.city_id`, NOT NULL, ON DELETE RESTRICT | Thành phố |
| `code` | `VARCHAR(32)` | UK, NOT NULL | Mã cửa hàng |
| `name` | `VARCHAR(120)` | NOT NULL | Tên cửa hàng |
| `address` | `VARCHAR(500)` | NOT NULL | Địa chỉ |
| `phone` | `VARCHAR(32)` | NOT NULL | Số điện thoại |
| `is_active` | `BOOLEAN` | NOT NULL, DEFAULT `TRUE` | Bật/tắt |
| `created_at` | `DATETIME(6)` | NOT NULL, DEFAULT NOW(6) | |
| `updated_at` | `DATETIME(6)` | NOT NULL, DEFAULT NOW(6) ON UPDATE | |

**Indexes**:
- `uq_stores_code` — UK trên `code`
- `ix_stores_city_id_store_id` — `(city_id, store_id)`
- `ix_stores_updated_at_store_id` — extraction cursor

**Invariant**: `code` unique. Store thuộc đúng một city. Store inactive không nhận đơn mới.

---

### 5.9. `store_inventory`

**Mục đích**: Tồn kho tại từng cửa hàng, song song với `inventory` (kho tổng). POS chỉ trừ `store_inventory`.

| Cột | Kiểu | Constraint | Mô tả |
|-----|------|-----------|-------|
| `store_inventory_id` | `BIGINT UNSIGNED` | UK, auto-increment, NOT NULL | Khóa đơn surrogate phục vụ tracking đơn lẻ |
| `store_id` | `BIGINT UNSIGNED` | PK/FK → `stores.store_id`, ON DELETE RESTRICT | Cửa hàng |
| `variant_id` | `BIGINT UNSIGNED` | PK/FK → `product_variants.variant_id`, ON DELETE RESTRICT | Variant |
| `on_hand` | `BIGINT UNSIGNED` | NOT NULL | Số lượng tồn hiện tại |
| `opening_on_hand` | `BIGINT UNSIGNED` | NOT NULL | Số lượng tồn đầu kỳ |
| `version` | `BIGINT UNSIGNED` | NOT NULL, DEFAULT `0` | 乐观锁 — tăng khi POS/cancel |
| `updated_at` | `DATETIME(6)` | NOT NULL, DEFAULT NOW(6) ON UPDATE | |

**Check constraints**:
- `opening_on_hand >= 0`
- `on_hand >= 0`
- `on_hand <= opening_on_hand`

**Indexes**:
- `uq_store_inventory_store_id_variant_id` — composite UK
- `ix_store_inventory_updated_at_store_id` — extraction cursor

**Invariant**: `0 <= on_hand <= opening_on_hand`. `version` tăng khi POS transaction hoặc cancel. POS order trừ `store_inventory` (kho cửa hàng); online checkout trừ `inventory` (kho tổng).

---

### 5.10. `carts`

**Mục đích**: Chu kỳ shopping cart. Một customer tối đa một cart `active`.

| Cột | Kiểu | Constraint | Mô tả |
|-----|------|-----------|-------|
| `cart_id` | `BIGINT UNSIGNED` | PK, auto-increment | Surrogate key |
| `public_id` | `BINARY(16)` | UK, NOT NULL | UUIDv5 |
| `customer_id` | `BIGINT UNSIGNED` | FK → `customers.customer_id`, NOT NULL, ON DELETE RESTRICT | Owner |
| `status` | `VARCHAR(16)` | NOT NULL, DEFAULT `'active'` | `active` hoặc `checked_out` |
| `active_customer_guard` | `BIGINT UNSIGNED` | COMPUTED `(CASE WHEN status='active' THEN customer_id ELSE NULL END)`, UK | Guard unique cho active cart |
| `created_at` | `DATETIME(6)` | NOT NULL, DEFAULT NOW(6) | |
| `updated_at` | `DATETIME(6)` | NOT NULL, DEFAULT NOW(6) ON UPDATE | |
| `checked_out_at` | `DATETIME(6)` | NULLABLE | Thời điểm checkout |

**Check constraints**:
- `status IN ('active', 'checked_out')`

**Indexes**:
- `uq_carts_public_id` — UK trên `public_id`
- `uq_carts_active_customer_guard` — UK trên `active_customer_guard` (thực thi 1 active cart/customer)
- `ix_carts_customer_id_created_at_cart_id` — `(customer_id, created_at, cart_id)`
- `ix_carts_updated_at_cart_id` — extraction cursor

**Invariant**: Cart đã checkout không tái sử dụng. `active_customer_guard` là computed column dùng làm arbiter cho unique constraint.

---

### 5.11. `cart_items`

**Mục đích**: Một variant trong cart. Logical removal giữ lịch sử.

| Cột | Kiểu | Constraint | Mô tả |
|-----|------|-----------|-------|
| `cart_item_id` | `BIGINT UNSIGNED` | PK, auto-increment | Surrogate key |
| `cart_id` | `BIGINT UNSIGNED` | FK → `carts.cart_id`, NOT NULL, ON DELETE RESTRICT | Cart cha |
| `variant_id` | `BIGINT UNSIGNED` | FK → `product_variants.variant_id`, NOT NULL, ON DELETE RESTRICT | Variant được thêm |
| `quantity` | `INT UNSIGNED` | NOT NULL | Số lượng |
| `is_present` | `BOOLEAN` | NOT NULL, DEFAULT `TRUE` | `TRUE`=đang trong cart, `FALSE`=đã xóa logic |
| `first_added_at` | `DATETIME(6)` | NOT NULL, DEFAULT NOW(6) | Lần đầu thêm vào cart |
| `removed_at` | `DATETIME(6)` | NULLABLE | Thời điểm xóa logic |
| `updated_at` | `DATETIME(6)` | NOT NULL, DEFAULT NOW(6) ON UPDATE | |

**Check constraints**:
- `quantity > 0`
- `(is_present = TRUE AND removed_at IS NULL) OR (is_present = FALSE AND removed_at IS NOT NULL)`

**Unique**: `(cart_id, variant_id)` — mỗi variant chỉ có một dòng trong cart

**Indexes**:
- `uq_cart_items_cart_id_variant_id` — composite UK
- `ix_cart_items_variant_id_cart_item_id` — `(variant_id, cart_item_id)`
- `ix_cart_items_updated_at_cart_item_id` — extraction cursor

**Invariant**: Add/update cart không thay đổi inventory.

---

### 5.12. `wishlist_items`

**Mục đích**: Sản phẩm customer đã lưu. Logical removal giữ lịch sử.

| Cột | Kiểu | Constraint | Mô tả |
|-----|------|-----------|-------|
| `wishlist_item_id` | `BIGINT UNSIGNED` | PK, auto-increment | Surrogate key |
| `customer_id` | `BIGINT UNSIGNED` | FK → `customers.customer_id`, NOT NULL, ON DELETE RESTRICT | Owner |
| `product_id` | `BIGINT UNSIGNED` | FK → `products.product_id`, NOT NULL, ON DELETE RESTRICT | Sản phẩm được lưu |
| `is_present` | `BOOLEAN` | NOT NULL, DEFAULT `TRUE` | Đang hiển thị hay đã xóa |
| `first_added_at` | `DATETIME(6)` | NOT NULL, DEFAULT NOW(6) | Lần đầu thêm |
| `last_added_at` | `DATETIME(6)` | NOT NULL, DEFAULT NOW(6) | Lần thêm lại sau khi xóa |
| `removed_at` | `DATETIME(6)` | NULLABLE | Thời điểm xóa logic |
| `updated_at` | `DATETIME(6)` | NOT NULL, DEFAULT NOW(6) ON UPDATE | |

**Check constraints**:
- `(is_present = TRUE AND removed_at IS NULL) OR (is_present = FALSE AND removed_at IS NOT NULL)`
- `last_added_at >= first_added_at`
- `removed_at IS NULL OR removed_at >= last_added_at`

**Unique**: `(customer_id, product_id)` — mỗi product chỉ có một wishlist item/customer

**Indexes**:
- `uq_wishlist_items_customer_id_product_id` — composite UK
- `ix_wishlist_items_customer_present_last_added_id` — `(customer_id, is_present, last_added_at, wishlist_item_id)`
- `ix_wishlist_items_product_id_wishlist_item_id` — `(product_id, wishlist_item_id)`
- `ix_wishlist_items_updated_at_wishlist_item_id` — extraction cursor

---

### 5.13. `coupons`

**Mục đích**: Cấu hình mã giảm giá và counter sử dụng hiện hành.

| Cột | Kiểu | Constraint | Mô tả |
|-----|------|-----------|-------|
| `coupon_id` | `BIGINT UNSIGNED` | PK, auto-increment | Surrogate key |
| `public_id` | `BINARY(16)` | UK, NOT NULL | UUIDv5 |
| `code_normalized` | `VARCHAR(64)` | UK, NOT NULL | Business key (viết hoa, không dấu cách) |
| `discount_type` | `VARCHAR(24)` | NOT NULL | `percentage` hoặc `fixed_amount` |
| `discount_value` | `BIGINT UNSIGNED` | NOT NULL | % (1–100) hoặc VND (>0) |
| `minimum_subtotal_vnd` | `BIGINT UNSIGNED` | NOT NULL, DEFAULT `0` | Đơn tối thiểu để áp dụng |
| `starts_at` | `DATETIME(6)` | NOT NULL | Thời điểm bắt đầu hiệu lực |
| `ends_at` | `DATETIME(6)` | NOT NULL | Thời điểm hết hiệu lực |
| `is_active` | `BOOLEAN` | NOT NULL, DEFAULT `TRUE` | Bật/tắt tạm thời |
| `archived_at` | `DATETIME(6)` | NULLABLE | Thời điểm archive (terminal) |
| `archived_by_customer_id` | `BIGINT UNSIGNED` | FK → `customers.customer_id`, NULLABLE, ON DELETE RESTRICT | Admin archive |
| `archive_reason` | `VARCHAR(500)` | NULLABLE | Lý do archive (≥3 ký tự) |
| `total_usage_limit` | `BIGINT UNSIGNED` | NULLABLE | Giới hạn tổng lần dùng (NULL = vô hạn) |
| `per_customer_usage_limit` | `INT UNSIGNED` | NULLABLE | Giới hạn mỗi customer |
| `used_count` | `BIGINT UNSIGNED` | NOT NULL, DEFAULT `0` | Số lần đã dùng |
| `created_at` | `DATETIME(6)` | NOT NULL, DEFAULT NOW(6) | |
| `updated_at` | `DATETIME(6)` | NOT NULL, DEFAULT NOW(6) ON UPDATE | |

**Check constraints**:
- `discount_type IN ('percentage', 'fixed_amount')`
- `(discount_type = 'percentage' AND discount_value BETWEEN 1 AND 100) OR (discount_type = 'fixed_amount' AND discount_value > 0)`
- `starts_at < ends_at`
- `total_usage_limit IS NULL OR total_usage_limit > 0`
- `per_customer_usage_limit IS NULL OR per_customer_usage_limit > 0`
- `total_usage_limit IS NULL OR used_count <= total_usage_limit`
- Archive metadata consistency: ba archive field cùng null hoặc cùng có giá trị
- `archived_at IS NULL OR is_active = FALSE`

**Concurrency**: Checkout khóa row coupon trước khi kiểm tra `used_count`. Tăng counter và insert redemption atomically trong cùng transaction. Cancel khóa coupon và redemption, release đúng một lần rồi giảm counter.

**Indexes**:
- `uq_coupons_public_id` — UK trên `public_id`
- `uq_coupons_code_normalized` — UK trên `code_normalized`
- `ix_coupons_archived_at_coupon_id` — `(archived_at, coupon_id)`
- `ix_coupons_updated_at_coupon_id` — extraction cursor

---

### 5.14. `coupon_redemptions`

**Mục đích**: Chứng minh một order đã chiếm usage coupon. Cho phép release khi hủy.

| Cột | Kiểu | Constraint | Mô tả |
|-----|------|-----------|-------|
| `coupon_redemption_id` | `BIGINT UNSIGNED` | PK, auto-increment | Surrogate key |
| `coupon_id` | `BIGINT UNSIGNED` | FK → `coupons.coupon_id`, NOT NULL, ON DELETE RESTRICT | Coupon được dùng |
| `order_id` | `BIGINT UNSIGNED` | FK → `orders.order_id`, UK, NOT NULL, ON DELETE RESTRICT | Order chiếm usage |
| `customer_id` | `BIGINT UNSIGNED` | FK → `customers.customer_id`, NOT NULL, ON DELETE RESTRICT | Customer dùng coupon |
| `status` | `VARCHAR(16)` | NOT NULL | `redeemed` hoặc `released` |
| `redeemed_at` | `DATETIME(6)` | NOT NULL | Thời điểm redeem |
| `released_at` | `DATETIME(6)` | NULLABLE | Thời điểm release (khi hủy) |
| `created_at` | `DATETIME(6)` | NOT NULL, DEFAULT NOW(6) | |
| `updated_at` | `DATETIME(6)` | NOT NULL, DEFAULT NOW(6) ON UPDATE | |

**Check constraints**:
- `status IN ('redeemed', 'released')`
- `(status = 'redeemed' AND released_at IS NULL) OR (status = 'released' AND released_at IS NOT NULL)`

**Unique**: `order_id` — mỗi order tối đa một redemption

**Indexes**:
- `uq_coupon_redemptions_order_id` — UK trên `order_id`
- `ix_coupon_redemptions_coupon_customer_status` — `(coupon_id, customer_id, status)` — per-customer limit check
- `ix_coupon_redemptions_updated_at_id` — `(updated_at, coupon_redemption_id)` — extraction cursor

---

### 5.15. `orders`

**Mục đích**: Kết quả checkout (online) hoặc POS transaction. State machine: `paid → confirmed → completed`, `paid → cancelled`.

| Cột | Kiểu | Constraint | Mô tả |
|-----|------|-----------|-------|
| `order_id` | `BIGINT UNSIGNED` | PK, auto-increment | Surrogate key |
| `order_number` | `VARCHAR(32)` | UK, NOT NULL | Mã đơn hàng hiển thị |
| `cart_id` | `BIGINT UNSIGNED` | FK → `carts.cart_id`, UK, NOT NULL | Cart đã checkout (1:1 online) |
| `customer_id` | `BIGINT UNSIGNED` | FK → `customers.customer_id`, NOT NULL, ON DELETE RESTRICT | Chủ đơn |
| `checkout_idempotency_key` | `VARCHAR(64)` | UK, NOT NULL | Idempotency key cho checkout (NULL cho POS) |
| `coupon_id` | `BIGINT UNSIGNED` | FK → `coupons.coupon_id`, NULLABLE, ON DELETE RESTRICT | Coupon đã áp dụng |
| `status` | `VARCHAR(24)` | NOT NULL | Trạng thái hiện tại |
| `payment_method` | `VARCHAR(16)` | NOT NULL, DEFAULT `'vietqr'` | Phương thức thanh toán (`vietqr` hoặc `cod`) |
| `currency_code` | `CHAR(3)` | NOT NULL, DEFAULT `'VND'` | Luôn VND |
| `subtotal_vnd` | `BIGINT UNSIGNED` | NOT NULL | Tổng tiền hàng (trước giảm giá) |
| `coupon_code_snapshot` | `VARCHAR(64)` | NULLABLE | Snapshot mã coupon |
| `coupon_type_snapshot` | `VARCHAR(24)` | NULLABLE | Snapshot loại giảm giá |
| `coupon_value_snapshot` | `BIGINT UNSIGNED` | NULLABLE | Snapshot giá trị giảm |
| `discount_amount_vnd` | `BIGINT UNSIGNED` | NOT NULL, DEFAULT `0` | Số tiền giảm giá |
| `shipping_fee_vnd` | `BIGINT UNSIGNED` | NOT NULL | Phí vận chuyển |
| `total_vnd` | `BIGINT UNSIGNED` | NOT NULL | Tổng thanh toán |
| `receiver_name` | `VARCHAR(160)` | NOT NULL | Tên người nhận |
| `receiver_phone` | `VARCHAR(32)` | NOT NULL | SĐT người nhận |
| `shipping_address_text` | `VARCHAR(1000)` | NOT NULL | Địa chỉ giao hàng |
| `data_origin` | `VARCHAR(16)` | NOT NULL, DEFAULT `'manual'` | `manual` hoặc `synthetic` |
| `generation_run_id` | `VARCHAR(64)` | NULLABLE | ID lần generate |
| `created_at` | `DATETIME(6)` | NOT NULL, DEFAULT NOW(6) | |
| `updated_at` | `DATETIME(6)` | NOT NULL, DEFAULT NOW(6) ON UPDATE | |
| `paid_at` | `DATETIME(6)` | NULLABLE | Thời điểm thanh toán (online VietQR hoặc khi COD thu tiền) |
| `confirmed_at` | `DATETIME(6)` | NULLABLE | Thời điểm admin xác nhận |
| `completed_at` | `DATETIME(6)` | NULLABLE | Thời điểm hoàn tất |
| `cancelled_at` | `DATETIME(6)` | NULLABLE | Thời điểm hủy |
| `store_id` | `BIGINT UNSIGNED` | FK → `stores.store_id`, NULLABLE | Cửa hàng liên kết (allocation hoặc POS) |
| `channel` | `VARCHAR(16)` | NOT NULL, DEFAULT `'online'` | Kênh bán: `online` hoặc `pos` |
| `staff_id` | `BIGINT UNSIGNED` | FK → `customers.customer_id`, NULLABLE | Nhân viên xử lý (POS) |

**Check constraints**:
- `status IN ('pending_payment', 'paid', 'payment_failed', 'confirmed', 'shipping', 'delivered', 'completed', 'cancelled', 'failed_delivery', 'returned')`
- `payment_method IN ('vietqr', 'cod')`
- `currency_code = 'VND'`
- `subtotal_vnd >= 0`
- `shipping_fee_vnd >= 0`
- `discount_amount_vnd <= subtotal_vnd`
- `total_vnd = subtotal_vnd - discount_amount_vnd + shipping_fee_vnd`
- Coupon snapshot consistency: Toàn bộ coupon fields NULL + discount=0, HOẶC tất cả NOT NULL + discount>0
- `coupon_type_snapshot` value: `percentage` (1–100) hoặc `fixed_amount` (>0)
- `data_origin IN ('manual', 'synthetic')`

**Indexes**:
- `uq_orders_order_number` — UK trên `order_number`
- `uq_orders_cart_id` — UK trên `cart_id` (1 cart → 1 order)
- `uq_orders_checkout_idempotency_key` — UK trên `checkout_idempotency_key`
- `ix_orders_payment_method` — `(payment_method)`
- `ix_orders_customer_id_created_at_order_id` — customer history
- `ix_orders_status_created_at_order_id` — admin queue
- `ix_orders_updated_at_order_id` — extraction cursor
- `ix_orders_coupon_id_order_id` — coupon lineage


**State machine**:
```text
paid --admin xác nhận--> confirmed --admin hoàn tất--> completed
paid --customer/admin hủy--> cancelled
```
Chỉ order `paid` được hủy. `confirmed` và `completed` không được hủy.

**Channel invariants**:
- `channel='online'`: `cart_id` NOT NULL, `checkout_idempotency_key` NOT NULL, `staff_id` NULL (hoặc allocation store)
- `channel='pos'`: `store_id` NOT NULL, `staff_id` NOT NULL, `cart_id=NULL`, `checkout_idempotency_key=NULL`, status mặc định `completed`

---

### 5.16. `order_items`

**Mục đích**: Snapshot dòng hàng trong order. Append-only — master data thay đổi không làm đổi lịch sử.

| Cột | Kiểu | Constraint | Mô tả |
|-----|------|-----------|-------|
| `order_item_id` | `BIGINT UNSIGNED` | PK, auto-increment | Surrogate key |
| `public_id` | `BINARY(16)` | UK, NOT NULL | UUIDv5 |
| `order_id` | `BIGINT UNSIGNED` | FK → `orders.order_id`, NOT NULL, ON DELETE RESTRICT | Order cha |
| `variant_id` | `BIGINT UNSIGNED` | FK → `product_variants.variant_id`, NOT NULL, ON DELETE RESTRICT | Variant được mua |
| `product_public_id_snapshot` | `BINARY(16)` | NOT NULL | Snapshot product public_id |
| `category_code_snapshot` | `VARCHAR(64)` | NOT NULL | Snapshot mã danh mục |
| `category_name_snapshot` | `VARCHAR(160)` | NOT NULL | Snapshot tên danh mục |
| `product_name_snapshot` | `VARCHAR(200)` | NOT NULL | Snapshot tên sản phẩm |
| `sku_snapshot` | `VARCHAR(64)` | NOT NULL | Snapshot SKU |
| `size_code_snapshot` | `VARCHAR(32)` | NOT NULL | Snapshot size |
| `color_code_snapshot` | `VARCHAR(64)` | NOT NULL | Snapshot màu |
| `unit_price_vnd` | `BIGINT UNSIGNED` | NOT NULL | Đơn giá tại thời điểm mua |
| `cost_price_vnd` | `BIGINT UNSIGNED` | NOT NULL, DEFAULT `0` | Snapshot giá vốn hàng bán tại thời điểm mua |
| `quantity` | `INT UNSIGNED` | NOT NULL | Số lượng |
| `line_total_vnd` | `BIGINT UNSIGNED` | NOT NULL | `unit_price_vnd × quantity` |
| `created_at` | `DATETIME(6)` | NOT NULL, DEFAULT NOW(6) | |

**Check constraints**:
- `unit_price_vnd >= 0`
- `cost_price_vnd >= 0`
- `quantity > 0`
- `line_total_vnd = unit_price_vnd * quantity`

**Unique**: `(order_id, variant_id)` — mỗi variant chỉ có một dòng trong order

**Indexes**:
- `uq_order_items_public_id` — UK trên `public_id`
- `uq_order_items_order_id_variant_id` — composite UK
- `ix_order_items_variant_id_order_item_id` — `(variant_id, order_item_id)`
- `ix_order_items_created_at_order_item_id` — extraction cursor

---

### 5.17. `payments`

**Mục đích**: Ghi nhận thanh toán cho order. Trong TLCN luôn `succeeded` tại checkout.

| Cột | Kiểu | Constraint | Mô tả |
|-----|------|-----------|-------|
| `payment_id` | `BIGINT UNSIGNED` | PK, auto-increment | Surrogate key |
| `payment_reference` | `VARCHAR(64)` | UK, NOT NULL | Mã tham chiếu thanh toán |
| `order_id` | `BIGINT UNSIGNED` | FK → `orders.order_id`, UK, NOT NULL, ON DELETE RESTRICT | Order liên kết (1:1) |
| `payment_idempotency_key` | `VARCHAR(64)` | UK, NOT NULL | Idempotency key |
| `status` | `VARCHAR(16)` | NOT NULL | `succeeded` hoặc `failed` |
| `currency_code` | `CHAR(3)` | NOT NULL, DEFAULT `'VND'` | Luôn VND |
| `amount_vnd` | `BIGINT UNSIGNED` | NOT NULL | Số tiền thanh toán |
| `failure_code` | `VARCHAR(64)` | NULLABLE | Mã lỗi (chỉ khi `failed`) |
| `attempted_at` | `DATETIME(6)` | NOT NULL | Thời điểm thử thanh toán |
| `created_at` | `DATETIME(6)` | NOT NULL, DEFAULT NOW(6) | |

**Check constraints**:
- `status IN ('succeeded', 'failed')`
- `currency_code = 'VND'`
- `amount_vnd >= 0`
- `(status = 'succeeded' AND failure_code IS NULL) OR (status = 'failed' AND failure_code IS NOT NULL)`

**Unique**: `order_id` — mỗi order chỉ có một payment

**Indexes**:
- `uq_payments_payment_reference` — UK trên `payment_reference`
- `uq_payments_order_id` — UK trên `order_id`
- `uq_payments_payment_idempotency_key` — UK trên `payment_idempotency_key`
- `ix_payments_created_at_payment_id` — extraction cursor

**Invariant**: Amount/currency phải khớp order. `failed` chỉ giữ cho tương thích dữ liệu lịch sử.

---

### 5.18. `refunds`

**Mục đích**: Full refund khi hủy order đã paid. Không phải return hàng hóa.

| Cột | Kiểu | Constraint | Mô tả |
|-----|------|-----------|-------|
| `refund_id` | `BIGINT UNSIGNED` | PK, auto-increment | Surrogate key |
| `public_id` | `BINARY(16)` | UK, NOT NULL | UUIDv5 |
| `payment_id` | `BIGINT UNSIGNED` | FK → `payments.payment_id`, UK, NOT NULL, ON DELETE RESTRICT | Payment được refund (1:1) |
| `refund_idempotency_key` | `VARCHAR(64)` | UK, NOT NULL | Idempotency key |
| `status` | `VARCHAR(16)` | NOT NULL | `succeeded` hoặc `failed` |
| `currency_code` | `CHAR(3)` | NOT NULL, DEFAULT `'VND'` | Luôn VND |
| `amount_vnd` | `BIGINT UNSIGNED` | NOT NULL | Số tiền refund (bằng payment amount) |
| `reason` | `VARCHAR(500)` | NOT NULL | Lý do hủy/refund |
| `requested_by_customer_id` | `BIGINT UNSIGNED` | FK → `customers.customer_id`, NOT NULL, ON DELETE RESTRICT | Customer yêu cầu |
| `created_at` | `DATETIME(6)` | NOT NULL, DEFAULT NOW(6) | |
| `completed_at` | `DATETIME(6)` | NULLABLE | Thời điểm refund hoàn tất |

**Check constraints**:
- `status IN ('succeeded', 'failed')`
- `currency_code = 'VND'`
- `amount_vnd >= 0`
- `(status = 'succeeded' AND completed_at IS NOT NULL) OR (status = 'failed' AND completed_at IS NULL)`

**Unique**: `payment_id` — mỗi payment tối đa một refund

**Indexes**:
- `uq_refunds_public_id` — UK trên `public_id`
- `uq_refunds_payment_id` — UK trên `payment_id`
- `uq_refunds_refund_idempotency_key` — UK trên `refund_idempotency_key`
- `ix_refunds_created_at_refund_id` — extraction cursor

---

### 5.19. `order_status_history`

**Mục đích**: Ghi lại mỗi transition trạng thái của order. Append-only — không update/delete.

| Cột | Kiểu | Constraint | Mô tả |
|-----|------|-----------|-------|
| `order_status_history_id` | `BIGINT UNSIGNED` | PK, auto-increment | Surrogate key |
| `order_id` | `BIGINT UNSIGNED` | FK → `orders.order_id`, NOT NULL, ON DELETE RESTRICT | Order liên kết |
| `from_status` | `VARCHAR(24)` | NULLABLE | Trạng thái trước (NULL khi tạo mới) |
| `to_status` | `VARCHAR(24)` | NOT NULL | Trạng thái đích |
| `transition_source` | `VARCHAR(32)` | NOT NULL | Nguồn transition |
| `reason` | `VARCHAR(500)` | NULLABLE | Lý do (bắt buộc khi hủy) |
| `transition_idempotency_key` | `VARCHAR(64)` | UK, NOT NULL | Idempotency key |
| `transitioned_at` | `DATETIME(6)` | NOT NULL | Thời điểm transition |
| `created_at` | `DATETIME(6)` | NOT NULL, DEFAULT NOW(6) | |

**Check constraints** — Valid transitions:
- `from_status IS NULL AND to_status IN ('pending_payment', 'paid', 'payment_failed', 'confirmed')` — tạo mới
- `from_status = 'pending_payment' AND to_status IN ('paid', 'payment_failed', 'cancelled')`
- `from_status = 'paid' AND to_status IN ('confirmed', 'cancelled')`
- `from_status = 'confirmed' AND to_status IN ('shipping', 'completed', 'cancelled', 'failed_delivery')`
- `from_status = 'shipping' AND to_status IN ('delivered', 'failed_delivery', 'returned')`
- `from_status = 'delivered' AND to_status IN ('completed', 'returned')`
- `from_status = 'completed' AND to_status = 'returned'`

**Check constraints** — Other:
- `transition_source IN ('checkout', 'internal_endpoint', 'generator', 'system', 'admin', 'customer')`
- `to_status <> 'cancelled' OR reason IS NOT NULL` — hủy bắt buộc lý do

**Unique**: `(order_id, to_status)` — ngăn transition đích lặp

**Indexes**:
- `uq_order_status_history_transition_idempotency_key` — UK trên `transition_idempotency_key`
- `uq_order_status_history_order_id_to_status` — composite UK
- `ix_order_status_history_order_id_transitioned_at_id` — `(order_id, transitioned_at, order_status_history_id)`
- `ix_order_status_history_created_at_id` — `(created_at, order_status_history_id)`

---

### 5.20. `product_reviews`

**Mục đích**: Review có verified purchase. Tự động hiển thị (`approved`), admin hậu kiểm để ẩn (`rejected`).

| Cột | Kiểu | Constraint | Mô tả |
|-----|------|-----------|-------|
| `review_id` | `BIGINT UNSIGNED` | PK, auto-increment | Surrogate key |
| `public_id` | `BINARY(16)` | UK, NOT NULL | UUIDv5 |
| `order_item_id` | `BIGINT UNSIGNED` | FK → `order_items.order_item_id`, UK, NOT NULL, ON DELETE RESTRICT | Order item được review (1:1) |
| `customer_id` | `BIGINT UNSIGNED` | FK → `customers.customer_id`, NOT NULL, ON DELETE RESTRICT | Customer viết review |
| `product_id` | `BIGINT UNSIGNED` | FK → `products.product_id`, NOT NULL, ON DELETE RESTRICT | Sản phẩm được review |
| `rating` | `INT UNSIGNED` | NOT NULL | Điểm 1–5 |
| `content` | `TEXT` | NULLABLE | Nội dung review |
| `status` | `VARCHAR(16)` | NOT NULL, DEFAULT `'approved'` | `approved` (hiển thị) hoặc `rejected` (ẩn) |
| `moderation_reason` | `VARCHAR(500)` | NULLABLE | Lý do ẩn (≥3 ký tự khi rejected) |
| `moderated_by_customer_id` | `BIGINT UNSIGNED` | FK → `customers.customer_id`, NULLABLE, ON DELETE RESTRICT | Admin thực hiện moderation |
| `moderated_at` | `DATETIME(6)` | NULLABLE | Thời điểm moderation |
| `created_at` | `DATETIME(6)` | NOT NULL, DEFAULT NOW(6) | |
| `updated_at` | `DATETIME(6)` | NOT NULL, DEFAULT NOW(6) ON UPDATE | |

**Check constraints**:
- `rating BETWEEN 1 AND 5`
- `status IN ('approved', 'rejected')`
- Post-publication moderation consistency:
  - `approved`: `moderation_reason` NULL; moderation fields đều NULL hoặc đều NOT NULL
  - `rejected`: `moderated_by_customer_id` + `moderated_at` + `moderation_reason` đều NOT NULL, reason ≥3 ký tự

**Unique**: `order_item_id` — mỗi order_item chỉ có một review

**Indexes**:
- `uq_product_reviews_public_id` — UK trên `public_id`
- `uq_product_reviews_order_item_id` — UK trên `order_item_id`
- `ix_product_reviews_product_status_created_at_id` — `(product_id, status, created_at, review_id)` — trang sản phẩm
- `ix_product_reviews_customer_created_at_id` — `(customer_id, created_at, review_id)` — lịch sử review
- `ix_product_reviews_updated_at_review_id` — extraction cursor

**Invariant**: Transaction tạo review phải chứng minh order thuộc customer và status `completed`. Review mới tự động `approved`. Endpoint public chỉ đọc `approved`.

---

### 5.21. `delivery_staff`

**Mục đích**: Quản lý hồ sơ và trạng thái hoạt động của đội ngũ nhân viên giao hàng (shipper) nội bộ D&K.

| Cột | Kiểu | Constraint | Mô tả |
|-----|------|-----------|-------|
| `staff_id` | `BIGINT UNSIGNED` | PK, auto-increment | Surrogate key |
| `public_id` | `BINARY(16)` | UK, NOT NULL | UUIDv5 |
| `full_name` | `VARCHAR(100)` | NOT NULL | Họ và tên nhân viên giao hàng |
| `phone` | `VARCHAR(20)` | UK, NOT NULL | Số điện thoại liên lạc |
| `vehicle_plate` | `VARCHAR(30)` | NULLABLE | Biển số phương tiện giao hàng |
| `is_active` | `BOOLEAN` | NOT NULL, DEFAULT `TRUE` | Trạng thái sẵn sàng nhận đơn |
| `created_at` | `DATETIME(6)` | NOT NULL, DEFAULT NOW(6) | |
| `updated_at` | `DATETIME(6)` | NOT NULL, DEFAULT NOW(6) ON UPDATE | |

**Indexes**:
- `uq_delivery_staff_public_id` — UK trên `public_id`
- `uq_delivery_staff_phone` — UK trên `phone`
- `ix_delivery_staff_updated_at_staff_id` — extraction cursor

**Invariant**: D&K vận hành 100% đội ngũ giao hàng in-house, không tích hợp API 3PL bên thứ ba. Trường `phone` và `full_name` phải được pseudonymize (ẩn danh hóa) khi đồng bộ sang tầng Silver của Lakehouse.

---

### 5.22. `shipments`

**Mục đích**: Phiếu giao hàng nội bộ liên kết 1 đơn hàng online với 1 nhân viên giao hàng, theo dõi vòng đời phát hàng và dòng tiền COD thu hộ.

| Cột | Kiểu | Constraint | Mô tả |
|-----|------|-----------|-------|
| `shipment_id` | `BIGINT UNSIGNED` | PK, auto-increment | Surrogate key |
| `public_id` | `BINARY(16)` | UK, NOT NULL | UUIDv5 |
| `shipment_code` | `VARCHAR(64)` | UK, NOT NULL | Mã vận đơn nội bộ (VD: `'SHP-...'`) |
| `order_id` | `BIGINT UNSIGNED` | FK → `orders.order_id`, NOT NULL, ON DELETE RESTRICT | Đơn hàng được giao (1:1 online) |
| `delivery_staff_id` | `BIGINT UNSIGNED` | FK → `delivery_staff.staff_id`, NULLABLE, ON DELETE SET NULL | Shipper phụ trách giao |
| `status` | `VARCHAR(32)` | NOT NULL, DEFAULT `'assigned'` | Trạng thái vận đơn |
| `attempt_count` | `INT UNSIGNED` | NOT NULL, DEFAULT `1` | Số lần thử giao hàng |
| `cod_amount_vnd` | `BIGINT UNSIGNED` | NOT NULL, DEFAULT `0` | Tiền COD cần thu theo đơn hàng |
| `cod_collected_vnd` | `BIGINT UNSIGNED` | NOT NULL, DEFAULT `0` | Tiền COD thực tế shipper đã thu |
| `dispatched_at` | `DATETIME(6)` | NULLABLE | Thời điểm xuất kho giao hàng |
| `delivered_at` | `DATETIME(6)` | NULLABLE | Thời điểm giao hàng thành công |
| `failed_at` | `DATETIME(6)` | NULLABLE | Thời điểm giao thất bại (boom hàng) |
| `failure_reason` | `VARCHAR(255)` | NULLABLE | Lý do không giao được (khách không nghe máy, đổi ý,...) |
| `notes` | `TEXT` | NULLABLE | Ghi chú vận hành giao hàng |
| `created_at` | `DATETIME(6)` | NOT NULL, DEFAULT NOW(6) | |
| `updated_at` | `DATETIME(6)` | NOT NULL, DEFAULT NOW(6) ON UPDATE | |

**Check constraints**:
- `status IN ('assigned', 'picked_up', 'in_transit', 'delivered', 'failed', 'returned_to_warehouse')`
- `attempt_count >= 1`
- `cod_amount_vnd >= 0`
- `cod_collected_vnd >= 0`

**Indexes**:
- `uq_shipments_public_id` — UK trên `public_id`
- `uq_shipments_code` — UK trên `shipment_code`
- `ix_shipments_order_id` — `(order_id)`
- `ix_shipments_delivery_staff_id` — `(delivery_staff_id)`
- `ix_shipments_status` — `(status)`
- `ix_shipments_updated_at_shipment_id` — extraction cursor

**Invariant**: 
- Nếu đơn thanh toán `cod`: `cod_amount_vnd = orders.total_vnd`. Khi giao thành công (`delivered`), `cod_collected_vnd = cod_amount_vnd`.
- Nếu giao thất bại (`failed`), `cod_collected_vnd = 0`, đơn hàng chuyển sang `failed_delivery`, tăng `boom_count` của khách hàng và hoàn trả hàng về kho tổng qua `inventory_transactions`.

---

### 5.23. `return_requests`

**Mục đích**: Ghi nhận và quản lý quy trình yêu cầu đổi / trả hàng trong vòng 7 ngày sau khi nhận hàng của khách hàng.

| Cột | Kiểu | Constraint | Mô tả |
|-----|------|-----------|-------|
| `return_id` | `BIGINT UNSIGNED` | PK, auto-increment | Surrogate key |
| `public_id` | `BINARY(16)` | UK, NOT NULL | UUIDv5 |
| `return_code` | `VARCHAR(64)` | UK, NOT NULL | Mã yêu cầu đổi trả (VD: `'RET-...'`) |
| `order_id` | `BIGINT UNSIGNED` | FK → `orders.order_id`, NOT NULL, ON DELETE RESTRICT | Đơn hàng gốc phát sinh đổi trả |
| `customer_id` | `BIGINT UNSIGNED` | FK → `customers.customer_id`, NOT NULL, ON DELETE RESTRICT | Khách hàng yêu cầu |
| `action_type` | `VARCHAR(16)` | NOT NULL | Loại yêu cầu: `exchange` (đổi size/màu) hoặc `refund` (trả hàng hoàn tiền) |
| `status` | `VARCHAR(32)` | NOT NULL, DEFAULT `'pending_review'` | Trạng thái phê duyệt và xử lý |
| `customer_reason` | `TEXT` | NOT NULL | Lý do đổi/trả từ phía khách hàng |
| `image_urls` | `JSON` | NULLABLE | Danh sách ảnh đính kèm minh chứng |
| `admin_note` | `TEXT` | NULLABLE | Ghi chú xử lý của nhân viên CSKH/Kho |
| `reviewed_at` | `DATETIME(6)` | NULLABLE | Thời điểm CSKH tiếp nhận phê duyệt |
| `resolved_at` | `DATETIME(6)` | NULLABLE | Thời điểm xử lý hoàn tất đổi/hoàn tiền |
| `created_at` | `DATETIME(6)` | NOT NULL, DEFAULT NOW(6) | |
| `updated_at` | `DATETIME(6)` | NOT NULL, DEFAULT NOW(6) ON UPDATE | |

**Check constraints**:
- `action_type IN ('exchange', 'refund')`
- `status IN ('pending_review', 'approved', 'rejected', 'goods_received', 'completed', 'cancelled')`

**Indexes**:
- `uq_return_requests_public_id` — UK trên `public_id`
- `uq_return_requests_code` — UK trên `return_code`
- `ix_return_requests_order_id` — `(order_id)`
- `ix_return_requests_customer_id` — `(customer_id)`
- `ix_return_requests_status` — `(status)`
- `ix_return_requests_updated_at_return_id` — extraction cursor

**Invariant**: Khách hàng chỉ được gửi yêu cầu đổi/trả cho đơn hàng ở trạng thái `delivered` hoặc `completed` trong vòng 7 ngày kể từ `delivered_at`.

---

### 5.24. `return_items`

**Mục đích**: Chi tiết từng món hàng cần đổi hoặc trả trong một yêu cầu đổi trả, phục vụ khâu kiểm định chất lượng sản phẩm (inspection).

| Cột | Kiểu | Constraint | Mô tả |
|-----|------|-----------|-------|
| `return_item_id` | `BIGINT UNSIGNED` | PK, auto-increment | Surrogate key |
| `public_id` | `BINARY(16)` | UK, NOT NULL | UUIDv5 |
| `return_id` | `BIGINT UNSIGNED` | FK → `return_requests.return_id`, NOT NULL, ON DELETE CASCADE | Yêu cầu đổi trả cha |
| `order_item_id` | `BIGINT UNSIGNED` | FK → `order_items.order_item_id`, NOT NULL, ON DELETE RESTRICT | Dòng món hàng gốc trong đơn |
| `variant_id` | `BIGINT UNSIGNED` | FK → `product_variants.variant_id`, NOT NULL, ON DELETE RESTRICT | Biến thể sản phẩm khách trả lại |
| `quantity` | `INT UNSIGNED` | NOT NULL, DEFAULT `1` | Số lượng đổi hoặc trả |
| `exchange_variant_id` | `BIGINT UNSIGNED` | FK → `product_variants.variant_id`, NULLABLE, ON DELETE RESTRICT | Biến thể mới muốn đổi lấy (chỉ khi `action_type='exchange'`) |
| `refund_amount_vnd` | `BIGINT UNSIGNED` | NOT NULL, DEFAULT `0` | Số tiền hoàn lại cho món này (chỉ khi `action_type='refund'`) |
| `inspection_status` | `VARCHAR(16)` | NOT NULL, DEFAULT `'pending'` | Kết quả kiểm định (`pending`, `passed`, `failed`) |
| `created_at` | `DATETIME(6)` | NOT NULL, DEFAULT NOW(6) | |
| `updated_at` | `DATETIME(6)` | NOT NULL, DEFAULT NOW(6) ON UPDATE | |

**Check constraints**:
- `quantity > 0`
- `inspection_status IN ('pending', 'passed', 'failed')`
- `refund_amount_vnd >= 0`

**Indexes**:
- `uq_return_items_public_id` — UK trên `public_id`
- `ix_return_items_return_id` — `(return_id)`
- `ix_return_items_variant_id` — `(variant_id)`
- `ix_return_items_updated_at_item_id` — extraction cursor

**Invariant**: Nếu `action_type = 'exchange'`, `exchange_variant_id` phải có giá trị và `refund_amount_vnd = 0`. Nếu `action_type = 'refund'`, `exchange_variant_id` là NULL và `refund_amount_vnd` tối đa bằng `order_items.line_total_vnd`.

---

### 5.25. `inventory_transactions`

**Mục đích**: Sổ cái ghi nhận bất biến mọi giao dịch biến động số lượng tồn kho (nhập xưởng, xuất bán, chuyển cửa hàng, hoàn hàng boom, đổi trả). Không dùng bảng `suppliers` mà giả lập nhập kho trực tiếp qua giao dịch `inbound`.

| Cột | Kiểu | Constraint | Mô tả |
|-----|------|-----------|-------|
| `transaction_id` | `BIGINT UNSIGNED` | PK, auto-increment | Surrogate key |
| `public_id` | `BINARY(16)` | UK, NOT NULL | UUIDv5 |
| `variant_id` | `BIGINT UNSIGNED` | FK → `product_variants.variant_id`, NOT NULL, ON DELETE RESTRICT | Biến thể sản phẩm biến động tồn kho |
| `location_type` | `VARCHAR(24)` | NOT NULL | Loại địa điểm: `central_warehouse` (kho tổng) hoặc `store` (cửa hàng chi nhánh) |
| `store_id` | `BIGINT UNSIGNED` | FK → `stores.store_id`, NULLABLE, ON DELETE RESTRICT | Cửa hàng liên quan (NULL nếu là kho tổng) |
| `movement_type` | `VARCHAR(32)` | NOT NULL | Loại giao dịch biến động |
| `quantity_delta` | `INT` | NOT NULL | Số lượng biến động (+ tăng tồn, - giảm tồn) |
| `reference_code` | `VARCHAR(64)` | NULLABLE | Mã chứng từ liên quan (mã đơn, mã phiếu nhập, mã đổi trả) |
| `notes` | `VARCHAR(255)` | NULLABLE | Ghi chú chi tiết biến động |
| `created_at` | `DATETIME(6)` | NOT NULL, DEFAULT NOW(6) | Thời điểm ghi nhận giao dịch |

**Check constraints**:
- `location_type IN ('central_warehouse', 'store')`
- `movement_type IN ('inbound', 'outbound_order', 'outbound_pos', 'transfer_to_store', 'transfer_received', 'return_boom', 'return_customer', 'exchange_out', 'adjustment')`
- `(location_type = 'central_warehouse' AND store_id IS NULL) OR (location_type = 'store' AND store_id IS NOT NULL)`

**Indexes**:
- `uq_inventory_tx_public_id` — UK trên `public_id`
- `ix_inv_tx_variant_id` — `(variant_id)`
- `ix_inv_tx_store_id` — `(store_id)`
- `ix_inv_tx_movement_type` — `(movement_type)`
- `ix_inv_tx_created_at_tx_id` — extraction cursor

**Audit & Ledger Invariant**: Bảng hoàn toàn append-only. Không bao giờ được sửa đổi hoặc xóa các dòng trong `inventory_transactions`. Tổng đại số $\sum \text{quantity\_delta}$ qua mọi thời kỳ của 1 biến thể tại kho tổng phải khớp đúng với `inventory.on_hand`.

---

## 6. Transaction catalogue


### TX-01 — Checkout có coupon tùy chọn

Isolation: `READ COMMITTED`.

1. Replay order nếu `checkout_idempotency_key` đã tồn tại.
2. Khóa customer và active cart.
3. Khóa cart items và product/variant theo ID tăng dần.
4. Kiểm tra catalog active và quantity; nếu có coupon, khóa coupon và kiểm tra window/subtotal/limit.
5. Khóa inventory theo variant ID tăng dần rồi kiểm tra `on_hand`.
6. Tính server-side snapshot subtotal, discount, shipping và total.
7. Insert order `paid`, order items, payment `succeeded`, initial history và redemption.
8. Conditional decrement inventory, tăng `version`, đóng cart.
9. Commit; mọi lỗi rollback toàn bộ.

Không có external call và không random payment.

### TX-02 — Admin xác nhận order

1. Khóa order theo `order_id`.
2. Chỉ chấp nhận `paid`; replay nếu idempotency key đã commit đúng transition.
3. Update `status = confirmed`, set `confirmed_at`.
4. Insert immutable history `paid -> confirmed`.
5. Commit.

### TX-03 — Admin hoàn tất order

Giống TX-02 nhưng chỉ `confirmed -> completed`, set `completed_at` và insert history.

### TX-04 — Customer/admin hủy order

Isolation: `READ COMMITTED`. Lock order là điểm tuần tự hóa.

1. Khóa order; xác minh customer ownership hoặc admin role.
2. Chỉ `paid` được hủy; replay idempotent nếu đã cancelled bằng cùng key.
3. Khóa payment; nếu có coupon, khóa redemption rồi coupon.
4. Đọc order items, khóa inventory theo variant ID tăng dần.
5. Restore inventory theo từng order item và tăng `version`.
6. Insert full refund `succeeded` với unique payment/idempotency key.
7. Release redemption và giảm `coupons.used_count` đúng một lần.
8. Update order `cancelled`, set `cancelled_at`; insert history kèm actor/reason.
9. Commit atomically.

### TX-05 — Tạo review

1. Khóa/đọc `order_item -> order` và xác minh ownership.
2. Chỉ order `completed`.
3. Insert review `approved`, không có moderation metadata; unique `order_item_id` xử lý race.
4. Commit.

### TX-06 — Hậu kiểm review

1. Khóa review.
2. `approved -> rejected` bắt buộc lý do; set moderator/time và ẩn khỏi public query.
3. `rejected -> approved` xóa lý do, set moderator/time mới và hiển thị lại.
4. Request trùng desired state là idempotent và giữ audit gần nhất.

### TX-07 — Admin tạo/bật tắt/archive coupon

- Tạo: normalize code, validate window/value/limits, insert; unique code xử lý race.
- Toggle: khóa coupon; chỉ update `is_active` khi chưa archive.
- Archive: khóa coupon; lần đầu set inactive và đủ ba archive field trong cùng transaction. Request lặp là no-op và giữ audit đầu tiên.
- Không sửa snapshot trên order cũ.

### TX-08 — Admin archive product

- Khóa product; lần đầu set inactive và đủ ba archive field trong cùng transaction.
- Request lặp là no-op và giữ audit đầu tiên; product archive không thể tái kích hoạt.
- Không cascade sang variant, wishlist hoặc order item để giữ tham chiếu và snapshot lịch sử.

### TX-09 — POS transaction (bán tại quầy)

Isolation: `READ COMMITTED`.

1. Validate store active và staff có quyền truy cập store.
2. Với mỗi variant: kiểm tra tồn kho cửa hàng (`store_inventory.on_hand >= quantity`).
3. Tính server-side subtotal, total (không shipping fee, không coupon).
4. Insert order `completed` với `channel='pos'`, `store_id`, `staff_id`, `paid_at=now`, `completed_at=now`, `cart_id=null`, `checkout_idempotency_key=null`.
5. Insert order items, payment `succeeded`, status history `paid -> completed` với `transition_source='admin'` (giới hạn DB constraint).
6. Giảm `store_inventory.on_hand`, tăng `version`.
7. Commit; mọi lỗi rollback toàn bộ.

### TX-10 — Điều phối giao vận nội bộ & Ghi nhận kết quả giao (Delivered hoặc Boom COD)

Isolation: `READ COMMITTED`. Lock order và shipment là điểm tuần tự hóa.

1. **Xuất kho giao hàng**:
   - Khóa order theo `order_id` (trạng thái `confirmed`).
   - Gán `delivery_staff_id`, tạo/cập nhật `shipments` với `status = 'in_transit'`, `dispatched_at = now`.
   - Cập nhật order `status = 'shipping'`, ghi lịch sử `confirmed -> shipping`.
2. **Kịch bản A — Giao hàng thành công (`delivered`)**:
   - Khóa order và shipment; cập nhật `shipments.status = 'delivered'`, `delivered_at = now`.
   - Nếu đơn hàng thanh toán COD: cập nhật `shipments.cod_collected_vnd = shipments.cod_amount_vnd`, cập nhật `orders.paid_at = now`.
   - Cập nhật order `status = 'delivered'`, ghi nhận lịch sử `shipping -> delivered`.
   - Admin/hệ thống có thể chuyển tiếp sang `completed`.
3. **Kịch bản B — Giao hàng thất bại / Boom hàng (`failed_delivery`)**:
   - Shipper ghi nhận giao thất bại qua 3 lần không thành công (`attempt_count >= 3`).
   - Cập nhật `shipments.status = 'failed'`, `failed_at = now`, `failure_reason`, `cod_collected_vnd = 0`.
   - Cập nhật order `status = 'failed_delivery'`, ghi nhận lịch sử `shipping -> failed_delivery`.
   - **Hoàn tồn kho**: Ghi 1 bản ghi vào `inventory_transactions` với `movement_type = 'return_boom'`, `quantity_delta = +quantity`, đồng thời hoàn lại `inventory.on_hand`.
   - **Cảnh báo rủi ro**: Tăng `customers.boom_count = boom_count + 1`. Nếu `boom_count >= 3`, bật cờ `customers.is_cod_blocked = TRUE` để chặn thanh toán COD ở các đơn sau.

### TX-11 — Quy trình Đổi / Trả hàng sau 7 ngày

Isolation: `READ COMMITTED`.

1. **Khách hàng tạo yêu cầu**:
   - Kiểm tra đơn hàng thuộc khách hàng, trạng thái `delivered` hoặc `completed` và thời gian trong vòng 7 ngày kể từ `delivered_at`.
   - Insert `return_requests` với `status = 'pending_review'`, `action_type IN ('exchange', 'refund')`, lý do và ảnh đính kèm.
   - Insert chi tiết các dòng món hàng trong `return_items`.
2. **CSKH & Kho thẩm định (`inspection`)**:
   - Khi nhận hàng về kho, kiểm định tình trạng sản phẩm (`return_items.inspection_status = 'passed'`).
3. **Kịch bản A — Đổi size (`exchange`)**:
   - Khóa variant mới muốn đổi, kiểm tra tồn kho.
   - Trừ kho sản phẩm mới xuất đi (`inventory_transactions` với `movement_type = 'exchange_out'`).
   - Nhập lại sản phẩm cũ về kho (`inventory_transactions` với `movement_type = 'return_customer'`).
   - Đánh dấu `return_requests.status = 'completed'`.
4. **Kịch bản B — Trả hàng hoàn tiền (`refund`)**:
   - Nhập sản phẩm đã kiểm định lại vào kho (`inventory_transactions` với `movement_type = 'return_customer'`).
   - Thực hiện hoàn tiền cho khách (`refund_amount_vnd`), ghi nhận refund.
   - Cập nhật order `status = 'returned'`, ghi nhận lịch sử sang `returned`.
   - Đánh dấu `return_requests.status = 'completed'`.

### TX-12 — Nhập hàng từ xưởng vào Kho trung tâm (Inbound Restock)

Isolation: `READ COMMITTED`.

1. Khóa các biến thể sản phẩm cần nhập theo `variant_id` tăng dần.
2. Tăng tồn kho `inventory.on_hand = on_hand + quantity`, tăng `inventory.opening_on_hand` (nếu đầu kỳ) và tăng `version`.
3. Ghi nhận sổ cái `inventory_transactions`:
   - `location_type = 'central_warehouse'`, `store_id = NULL`
   - `movement_type = 'inbound'`
   - `quantity_delta = +quantity`
   - `reference_code = 'PO-...'` (mã phiếu nhập hàng từ xưởng)
4. Commit atomically.

---

## 7. Lock ordering và xử lý race

Thứ tự chuẩn khi transaction chạm nhiều aggregate:

```text
customer -> cart -> cart_item -> catalog/variant -> coupon -> inventory -> order children (payments, history, shipments, return_requests) -> inventory_transactions
```

Cancel bắt đầu từ order rồi khóa children theo ID ổn định. Không transaction nào khóa ngược từ coupon/inventory sang order đang tồn tại.

| Race | Cơ chế bảo vệ |
|---|---|
| Hai checkout cùng key | UK `orders.checkout_idempotency_key` + replay |
| Hai checkout tranh last item | row lock/conditional inventory update |
| Vượt coupon total limit | lock `coupons` + check/increment counter |
| Vượt coupon/customer limit | serialized coupon row + indexed redemption count |
| Hai actor cùng hủy | lock order + state check + UK refund/history |
| Hủy và admin confirm đồng thời | cùng lock order; chỉ transaction commit trước hợp lệ |
| Hai shipper nhận cùng đơn | UK `shipments.order_id` (1 đơn chỉ có 1 shipment) |
| Cùng yêu cầu đổi trả 1 món hàng | Kiểm tra tổng số lượng đã yêu cầu return $\le$ số lượng trong `order_items` |
| Nhập xuất kho tranh chấp | Khóa theo thứ tự `variant_id` tăng dần + optimistic version |
| Review hai request | UK `product_reviews.order_item_id` |
| Hai admin đổi visibility review | row lock + current-state check; request cùng state idempotent |
| Transition lặp | UK history idempotency và `(order_id, to_status)` |
| Hai admin cùng archive | row lock + archive idempotent, giữ audit đầu tiên |

Deadlock vẫn có thể xảy ra; application chỉ retry transaction khi lỗi được xác định là deadlock/serialization và request idempotent.

---

## 8. OLAP readiness và reconciliation

Hệ thống trích xuất **24 bảng** sang hồ dữ liệu Lakehouse (toàn bộ trừ `customer_credentials`). Extraction cursor cho các bảng mới:

| Bảng | Cursor | Mutability |
|---|---|---|
| `products` | `(updated_at, product_id)` | Mutable/current archive state |
| `coupons` | `(updated_at, coupon_id)` | Mutable |
| `coupon_redemptions` | `(updated_at, coupon_redemption_id)` | Mutable |
| `refunds` | `(created_at, refund_id)` | Append-only |
| `product_reviews` | `(updated_at, review_id)` | Mutable current visibility/moderation |
| `delivery_staff` | `(updated_at, staff_id)` | Mutable/anonymizable |
| `shipments` | `(updated_at, shipment_id)` | Mutable |
| `return_requests` | `(updated_at, return_id)` | Mutable |
| `return_items` | `(created_at, return_item_id)` | Append-only |
| `inventory_transactions` | `(created_at, transaction_id)` | Append-only ledger |

### Reconciliation rules

- `orders.total_vnd = subtotal_vnd - discount_amount_vnd + shipping_fee_vnd`
- Succeeded payment amount = order total (cho đơn VietQR)
- Đơn COD giao thành công: `orders.status = 'delivered'` và `shipments.cod_collected_vnd = shipments.cod_amount_vnd`
- Đơn boom COD: `orders.status = 'failed_delivery'`, `shipments.status = 'failed'`, `shipments.cod_collected_vnd = 0`, doanh thu thuần trên Lakehouse = 0
- Succeeded refund amount = payment amount và order cancelled
- Cancelled order phải có history, refund và inventory đã restore
- Active redeemed count theo coupon = `coupons.used_count`
- `archived_at IS NOT NULL` thì entity inactive và đủ actor/reason; order/order item lịch sử vẫn join được đến product/coupon archive
- Mọi review phải trỏ đến completed purchased order item
- Review `approved` auto-publish có thể không có moderator; review `rejected` phải đủ moderator/time/reason
- `inventory.on_hand = opening_on_hand + SUM(inventory_transactions.quantity_delta)` tại kho tổng
- `SUM(store_inventory.on_hand) <= inventory.on_hand`
- POS order: `channel='pos'`, `store_id` NOT NULL, `staff_id` NOT NULL, status=`completed`

PII ở `customers` (tên, email, phone) và `delivery_staff` (tên, phone) phải được hash/pseudonymize ở downstream Silver & Gold. OLTP là source of truth; lakehouse chỉ dẫn xuất.

---

## 9. Định hướng Mở rộng tiếp theo (KLTN)

Trong phạm vi TLCN hiện tại, hệ thống đã hoàn thiện đầy đủ mô hình CSDL OLTP 25 bảng cùng luồng nghiệp vụ giao vận nội bộ, xử lý boom hàng COD, đổi trả 7 ngày và sổ cái biến động kho. Nếu phát triển tiếp thành Khóa luận Tốt nghiệp (KLTN), các hạng mục mở rộng kiến trúc bao gồm:
1. **Change Data Capture (CDC)**: Thay thế batch extraction định kỳ bằng Debezium đọc MySQL binlog truyền qua Apache Kafka vào Lakehouse theo thời gian thực (Streaming Ingestion).
2. **Transactional Outbox Pattern**: Đảm bảo tính nhất quán tuyệt đối giữa thay đổi dữ liệu OLTP và phát sinh sự kiện phân tán.
3. **Cổng thanh toán thực tế**: Tích hợp webhook xác thực thanh toán thời gian thực từ VietQR / MoMo / ZaloPay.
4. **Machine Learning Feature Store**: Khai thác dữ liệu từ tầng Gold (RFM customer, hành vi clickstream logs) để huấn luyện mô hình dự đoán khách hàng có nguy cơ boom hàng và mô hình gợi ý sản phẩm cá nhân hóa.

