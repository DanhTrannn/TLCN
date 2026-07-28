# THIẾT KẾ LOGICAL SCHEMA OLTP CHO TLCN

## 0. Phạm vi và trạng thái tài liệu

Tài liệu này thiết kế schema MySQL `ecommerce` cho phần source website của Tiểu luận chuyên ngành (TLCN), dựa trên:

- `remake.md`: nguồn yêu cầu chức năng và phạm vi TLCN;
- `skills/oltp-design.md`: nguyên tắc correctness, invariant, transaction, concurrency, index và OLAP-readiness.

Đây là **logical design**, chưa phải DDL, migration hoặc code ORM. Tên kiểu dữ liệu và constraint chỉ mô tả ý định triển khai trên MySQL 8.4/InnoDB.

Schema giữ đúng 13 bảng nghiệp vụ đã chốt trong `remake.md`:

1. `customers`;
2. `customer_credentials`;
3. `categories`;
4. `products`;
5. `product_variants`;
6. `carts`;
7. `cart_items`;
8. `orders`;
9. `order_items`;
10. `payments`;
11. `order_status_history`;
12. `inventory`;
13. `wishlist_items`.

Các bảng Airflow, pipeline audit, Bronze, Silver, Gold và MySQL `analytics` không thuộc schema OLTP này.

---

## 1. Các quyết định nghiệp vụ đã chốt

### 1.1. Có trong TLCN

- Customer phải đăng nhập trước khi thao tác cart và checkout.
- Catalog có category phân cấp, product và variant theo size/color.
- Catalog hỗ trợ search tên/mô tả và filter category, size, color, khoảng giá, tồn kho mà không tạo search-history table trong OLTP.
- Mỗi customer có một wishlist mặc định chứa nhiều product; cùng product chỉ có một row/customer.
- Mỗi variant có SKU và giá riêng.
- Mỗi customer có tối đa một active cart.
- Add-to-cart không giữ tồn kho.
- Storefront checkout không nhận kịch bản payment và không random kết quả.
- Checkout hợp lệ tạo payment `succeeded`, order `paid` và giảm tồn kho trong cùng transaction.
- Checkout không hợp lệ rollback, giữ cart active và không tạo order/payment.
- Một cart chỉ tạo tối đa một order.
- Một order có đúng một payment row.
- Paid order có thể chuyển một lần sang `completed`.
- Inventory được khởi tạo khi tạo variant và chỉ giảm bởi succeeded checkout; TLCN không có restock/adjustment cho row hiện hữu.
- Order, order item, payment và status history giữ lịch sử phục vụ DE/OLAP.

### 1.2. Không có trong TLCN

- Anonymous cart và cart merge.
- Coupon, promotion, tax module.
- Reservation, `reserved`, backorder và nhiều warehouse.
- External payment provider và nhiều payment attempt.
- Refund, return, review, shipment module.
- Partial fulfillment hoặc partial payment.
- Admin portal đầy đủ.
- Transactional outbox, Kafka, Redis, event sourcing và microservice.

### 1.3. Giả định thiết kế

- Một product thuộc đúng một category hiện hành; TLCN không bắt buộc product chỉ được gắn vào category lá.
- Size và color là thuộc tính chuỗi đã chuẩn hóa ở application; chưa tạo master table riêng.
- Shipping fee được tính từ cấu hình application và snapshot vào order; schema không lưu bảng shipping rule.
- Chỉ dùng VND; tiền lưu theo đơn vị đồng bằng số nguyên chính xác.
- Catalog và variant không hard delete sau khi đã được tham chiếu; dùng trạng thái active/inactive.
- Cart item dùng logical removal thay vì hard delete để trạng thái removed có thể được incremental extraction quan sát; nếu remove rồi re-add giữa hai batch thì downstream chỉ nhận trạng thái cuối như các mutable row khác.
- Các thay đổi nhiều lần trên mutable master data giữa hai batch có thể được Silver nhận dưới dạng trạng thái cuối; lịch sử bắt buộc chỉ được bảo tồn đầy đủ cho order status và transaction order/payment.

---

## 2. Quy ước dữ liệu chung

### 2.1. Định danh

- Internal PK dùng số nguyên 64-bit tăng dần để có clustered-key locality tốt trên InnoDB.
- Customer, cart, category, product và variant có `public_id` ổn định để tham chiếu kỹ thuật/API/downstream.
- Route thân thiện có thể dùng business key: category `code`, product `slug`, variant `sku`.
- Order dùng `order_number`; payment dùng `payment_reference` làm public/business identifier.
- Public UUID nên dùng UUIDv7 và lưu dạng binary 16 byte khi triển khai; API biểu diễn ở dạng chuỗi chuẩn.
- Không dùng email, SKU hoặc order number làm physical primary key.

### 2.2. Thời gian

- Tất cả timestamp lưu UTC với độ chính xác microsecond.
- `created_at`: thời điểm row được ghi vào OLTP.
- `updated_at`: thời điểm material state gần nhất thay đổi; phải do database quản lý hoặc được application cập nhật bắt buộc trong cùng statement.
- `occurred_at`/`transitioned_at`/`attempted_at`: business event time.
- Dashboard mới chuyển sang `Asia/Ho_Chi_Minh` ở serving/presentation layer.
- Client timestamp không được dùng làm nguồn chính thức cho transaction time.

### 2.3. Tiền và số lượng

- `*_vnd` dùng số nguyên 64-bit; không dùng `FLOAT`/`DOUBLE`.
- Giá và amount không âm.
- Quantity của cart/order dương.
- `inventory.opening_on_hand` không âm và immutable sau seed.
- `inventory.on_hand` không âm.

### 2.4. Status và enum

- Dùng code string ngắn kết hợp `CHECK`, không dùng MySQL native `ENUM` để giảm chi phí schema evolution.
- Application phải dùng cùng một danh sách giá trị với database constraint.
- Chuyển trạng thái được kiểm tra trong transaction; không chỉ kiểm tra ở UI.

### 2.5. Delete semantics

- `inactive`: master data không còn phục vụ giao dịch mới nhưng vẫn giữ lịch sử.
- `checked_out`, `payment_failed`, `completed`: trạng thái nghiệp vụ, không phải soft delete.
- `is_present = false` ở cart item hoặc wishlist item: item bị loại khỏi current state nhưng row được giữ cho extraction.
- `anonymized_at`: PII customer đã được thay thế; không đồng nghĩa hard delete.
- Order, order item, payment và status history không hard delete.
- Mọi FK từ transaction về master data dùng semantics `RESTRICT`, không cascade xóa lịch sử.

### 2.6. Batch extraction metadata

- Mutable table có `updated_at` và stable PK.
- Append-only table có business event time, `created_at` và stable PK.
- Index extraction dùng cặp `(updated_at, internal_pk)` hoặc `(created_at, internal_pk)`.
- `customer_credentials` không được extract sang lakehouse.

---

## 3. Mô hình quan hệ tổng thể

```text
customers 1 ─── 1 customer_credentials
    │
    ├── 1 ─── N wishlist_items N ─── 1 products
    ├── 1 ─── N carts 1 ─── N cart_items N ─── 1 product_variants
    │                 │
    │                 └── 0..1 orders
    │
    └── 1 ─── N orders 1 ─── N order_items N ─── 1 product_variants
                         │
                         ├── 1 ─── 1 payments
                         └── 1 ─── N order_status_history

categories 1 ─── N categories
    │
    └── 1 ─── N products 1 ─── N product_variants
                                      │
                                      ├── 1 ─── 1 inventory
                                      ├── 1 ─── N cart_items
                                      └── 1 ─── N order_items

products 1 ─── N wishlist_items N ─── 1 customers
```

### 3.1. Aggregate boundary

| Aggregate | Root | Thành phần | Invariant được bảo vệ trong aggregate transaction |
|---|---|---|---|
| Customer identity | `customers` | `customer_credentials` | Một credential/customer, email normalized unique |
| Catalog product | `products` | `product_variants` | SKU unique và tổ hợp size/color unique/product |
| Cart | `carts` | `cart_items` | Một active cart/customer, một variant/cart, chỉ sửa active cart |
| Wishlist | `customers` | `wishlist_items` | Một product/customer, desired-state mutation và logical removal |
| Order | `orders` | `order_items`, `payments`, `order_status_history` | Một order/cart, một payment/order, snapshot amount và state hợp lệ |
| Inventory | `inventory` | — | Opening balance immutable sau khi tạo variant; current balance chỉ giảm bởi succeeded checkout |

Category hierarchy là master-data aggregate nhỏ. Checkout là transaction phối hợp Cart, Order và Inventory nhưng không biến chúng thành một bảng hoặc một aggregate dài hạn.

---

## 4. Danh mục bảng và grain

| Bảng | Grain | Loại dữ liệu | Mutable | Chính thức cho OLAP |
|---|---|---|---|---|
| `customers` | Một customer | Master/current state | Có | Có, bỏ/tokenize PII |
| `customer_credentials` | Một credential/customer | Security data | Có | Không extract |
| `categories` | Một category | Master/current state | Có | Có |
| `products` | Một product | Master/current state | Có | Có |
| `product_variants` | Một tổ hợp product-size-color | Master/current state | Có | Có |
| `carts` | Một chu kỳ mua sắm/customer | Transaction/current state | Có | Có |
| `cart_items` | Một variant từng xuất hiện/cart | Transaction/current state | Có | Có |
| `wishlist_items` | Một product từng được wishlist/customer | Transaction/current state | Có | Có |
| `orders` | Một kết quả checkout/cart | Transaction + snapshot | Chỉ status/timestamps | Có |
| `order_items` | Một variant line/order | Immutable snapshot | Không | Có |
| `payments` | Một kết quả payment/order | Immutable transaction | Không | Có |
| `order_status_history` | Một state transition/order | Immutable history | Không | Có |
| `inventory` | Một opening/current balance/variant | Current state + seed baseline | Chỉ `on_hand` | Có |

---

## 5. Thiết kế chi tiết từng bảng

### 5.1. `customers`

**Mục đích:** lưu customer profile tối thiểu và identity ổn định cho giao dịch.

**Grain:** một row đại diện cho một customer.

| Cột | Kiểu logical | Null | Key/constraint | Ý nghĩa nghiệp vụ |
|---|---|---:|---|---|
| `customer_id` | BIGINT UNSIGNED | Không | PK | Internal surrogate key, không lộ ra API |
| `public_id` | UUID binary | Không | UNIQUE | Public stable identifier |
| `role` | VARCHAR(16) | Không | CHECK `customer`, `admin` | Phân quyền storefront hoặc admin tối thiểu |
| `display_name` | VARCHAR(120) | Không | Trimmed, không rỗng | Tên hiển thị tối thiểu |
| `status` | VARCHAR(16) | Không | CHECK `active`, `inactive` | Khả năng đăng nhập/giao dịch |
| `data_origin` | VARCHAR(16) | Không | CHECK `manual`, `synthetic` | Phân biệt dữ liệu demo/generator |
| `generation_run_id` | VARCHAR(64) | Có | CHECK theo origin | Run generator tạo customer nếu synthetic |
| `anonymized_at` | DATETIME(6) UTC | Có | Invariant với status | Thời điểm PII được anonymize |
| `created_at` | DATETIME(6) UTC | Không | Immutable | Commit time tạo customer |
| `updated_at` | DATETIME(6) UTC | Không | Monotonic theo row | Cursor cho mutable extraction |

**Business key:** `public_id`.

**Invariant:**

- `anonymized_at` có giá trị thì `status = inactive`.
- `data_origin = synthetic` thì `generation_run_id` bắt buộc có; manual thì để null.
- Không hard delete customer đã có cart/order.

**Index mục tiêu:**

- unique `public_id`: lookup customer từ API token;
- `(role, status, customer_id)`: authorization và danh sách vận hành admin;
- `(updated_at, customer_id)`: incremental extraction.

---

### 5.2. `customer_credentials`

**Mục đích:** cô lập authentication secret và PII khỏi customer domain/extraction.

**Grain:** một row đại diện cho credential đăng nhập duy nhất của một customer.

| Cột | Kiểu logical | Null | Key/constraint | Ý nghĩa nghiệp vụ |
|---|---|---:|---|---|
| `customer_id` | BIGINT UNSIGNED | Không | PK, FK → `customers` | Quan hệ one-to-one |
| `email_normalized` | VARCHAR(320) | Không | UNIQUE | Email lowercase/normalized dùng đăng nhập |
| `password_hash` | VARCHAR(255) | Không | Không được log/extract | Adaptive password hash và parameters |
| `is_enabled` | BOOLEAN | Không | Default true | Có cho phép xác thực hay không |
| `password_changed_at` | DATETIME(6) UTC | Không | — | Hỗ trợ invalidation/security audit tối thiểu |
| `created_at` | DATETIME(6) UTC | Không | Immutable | Thời điểm tạo credential |
| `updated_at` | DATETIME(6) UTC | Không | — | Thời điểm material state thay đổi |

**Business key:** `email_normalized`.

**Invariant:**

- Một customer có tối đa một credential.
- Hai customer không dùng cùng email normalized.
- Customer inactive hoặc anonymized không được đăng nhập dù credential còn row.
- Anonymization thay email bằng giá trị không thể suy ngược và unique, thay display name, disable credential; không xóa customer key.

**Index mục tiêu:** unique `email_normalized` phục vụ login point lookup. Không tạo index extraction vì bảng bị loại khỏi pipeline.

---

### 5.3. `categories`

**Mục đích:** lưu cây category để filter catalog.

**Grain:** một row đại diện cho một category.

| Cột | Kiểu logical | Null | Key/constraint | Ý nghĩa nghiệp vụ |
|---|---|---:|---|---|
| `category_id` | BIGINT UNSIGNED | Không | PK | Internal key |
| `public_id` | UUID binary | Không | UNIQUE | Stable public/analytics reference |
| `parent_category_id` | BIGINT UNSIGNED | Có | FK self, RESTRICT | Category cha; null là root |
| `code` | VARCHAR(64) | Không | UNIQUE | Business key ổn định |
| `name` | VARCHAR(160) | Không | Trimmed, không rỗng | Tên hiển thị hiện tại |
| `is_active` | BOOLEAN | Không | — | Có hiển thị/nhận product mới hay không |
| `created_at` | DATETIME(6) UTC | Không | Immutable | Commit time tạo category |
| `updated_at` | DATETIME(6) UTC | Không | — | Cursor current-state extraction |

**Business key:** `code`.

**Invariant:**

- Category không được là parent của chính nó.
- Cây không được có cycle; constraint đơn-row không đủ, application phải kiểm tra ancestor path trong transaction cập nhật hierarchy.
- Category đã được product hoặc category con tham chiếu không hard delete.
- Deactivate category không tự động rewrite lịch sử order.

**Index mục tiêu:**

- unique `code`, unique `public_id`;
- `(parent_category_id, is_active, category_id)` để đọc children có keyset;
- `(updated_at, category_id)` cho extraction.

---

### 5.4. `products`

**Mục đích:** lưu thông tin chung không phụ thuộc size/color.

**Grain:** một row đại diện cho một product.

| Cột | Kiểu logical | Null | Key/constraint | Ý nghĩa nghiệp vụ |
|---|---|---:|---|---|
| `product_id` | BIGINT UNSIGNED | Không | PK | Internal product key |
| `public_id` | UUID binary | Không | UNIQUE | Stable analytics/API reference |
| `category_id` | BIGINT UNSIGNED | Không | FK → `categories`, RESTRICT | Category hiện hành |
| `slug` | VARCHAR(180) | Không | UNIQUE | URL/business key |
| `name` | VARCHAR(200) | Không | Trimmed, không rỗng | Tên product hiện tại |
| `description` | TEXT | Có | — | Mô tả ngắn/dài tùy UI |
| `image_url` | VARCHAR(1024) | Có | — | URL ảnh demo; không lưu binary trong DB |
| `is_active` | BOOLEAN | Không | — | Product có xuất hiện trong catalog mới |
| `created_at` | DATETIME(6) UTC | Không | Immutable | Commit time tạo product |
| `updated_at` | DATETIME(6) UTC | Không | — | Cursor current-state extraction |

**Business key:** `slug`; `public_id` là stable technical public key.

**Invariant:**

- Product thuộc đúng một category.
- Product chỉ được bán khi product, category và variant đều active.
- Product đã phát sinh order item không hard delete; deactivate để ngừng bán.
- Việc đổi tên/category không làm thay đổi order item snapshot cũ.

**Index mục tiêu:**

- unique `slug`, unique `public_id`;
- `(category_id, is_active, product_id)` cho listing/filter/keyset pagination;
- `(is_active, product_id)` cho listing toàn catalog;
- `(updated_at, product_id)` cho extraction.

Search TLCN dùng bounded `LIKE` trên catalog nhỏ và luôn kết hợp active/category/variant filter. Chưa thêm FULLTEXT; chỉ bổ sung sau `EXPLAIN`/performance experiment chứng minh `LIKE` không đạt latency.

---

### 5.5. `product_variants`

**Mục đích:** lưu tổ hợp size/color cụ thể, SKU và giá bán hiện tại.

**Grain:** một row đại diện cho một tổ hợp `(product, size, color)`.

| Cột | Kiểu logical | Null | Key/constraint | Ý nghĩa nghiệp vụ |
|---|---|---:|---|---|
| `variant_id` | BIGINT UNSIGNED | Không | PK | Internal variant key |
| `public_id` | UUID binary | Không | UNIQUE | Stable API/analytics reference |
| `product_id` | BIGINT UNSIGNED | Không | FK → `products`, RESTRICT | Product sở hữu variant |
| `sku` | VARCHAR(64) | Không | UNIQUE | Business key bán hàng |
| `size_code` | VARCHAR(32) | Không | Composite UNIQUE | Size đã chuẩn hóa |
| `color_code` | VARCHAR(64) | Không | Composite UNIQUE | Color đã chuẩn hóa |
| `price_vnd` | BIGINT UNSIGNED | Không | CHECK `>= 0` | Giá hiện hành theo đơn vị đồng |
| `is_active` | BOOLEAN | Không | — | Variant có thể được add/checkout mới |
| `created_at` | DATETIME(6) UTC | Không | Immutable | Commit time tạo variant |
| `updated_at` | DATETIME(6) UTC | Không | — | Cursor current-state extraction |

**Business key:** `sku`.

**Invariant:**

- Unique `(product_id, size_code, color_code)` ngăn hai variant trùng tổ hợp.
- SKU unique toàn hệ thống và không tái sử dụng sau khi variant inactive.
- `product_id` của variant không được đổi sau khi đã có transaction reference.
- Giá client gửi lên không bao giờ là nguồn tính tiền; checkout đọc giá từ row đã khóa/được revalidate.
- Variant active phải có một inventory row trước khi được bán.

**Index mục tiêu:**

- unique `sku`, unique `public_id`;
- unique `(product_id, size_code, color_code)`;
- `(product_id, is_active, variant_id)` cho product detail;
- `(updated_at, variant_id)` cho extraction.

---

### 5.6. `carts`

**Mục đích:** biểu diễn một chu kỳ mua sắm của customer.

**Grain:** một row đại diện cho một cart thuộc một customer.

| Cột | Kiểu logical | Null | Key/constraint | Ý nghĩa nghiệp vụ |
|---|---|---:|---|---|
| `cart_id` | BIGINT UNSIGNED | Không | PK | Internal cart key |
| `public_id` | UUID binary | Không | UNIQUE | Cart identifier dùng qua API |
| `customer_id` | BIGINT UNSIGNED | Không | FK → `customers`, RESTRICT | Owner bắt buộc đã đăng nhập |
| `status` | VARCHAR(16) | Không | CHECK `active`, `checked_out` | Cart state |
| `active_customer_guard` | Derived BIGINT | Có | UNIQUE enforcement key | Bằng `customer_id` khi active, null khi checked out |
| `created_at` | DATETIME(6) UTC | Không | Immutable | Bắt đầu chu kỳ mua sắm |
| `updated_at` | DATETIME(6) UTC | Không | — | Lần mutation/state change gần nhất |
| `checked_out_at` | DATETIME(6) UTC | Có | State invariant | Thời điểm cart đóng bởi checkout |

`active_customer_guard` là cột enforcement-only sinh từ state. Nó cho phép nhiều cart `checked_out` nhưng chỉ một cart `active` trên mỗi customer; unique `(customer_id, status)` không được dùng vì sẽ cấm nhiều cart lịch sử cùng trạng thái.

**Business key:** `public_id`.

**Invariant:**

- Mỗi customer có tối đa một active cart, được bảo vệ bằng unique guard tại database.
- Active cart có `checked_out_at = null`.
- Checked-out cart có `checked_out_at` khác null.
- Checked-out cart và items không được sửa hoặc tái sử dụng.
- Customer phải active khi tạo/mutate/checkout cart.

**Index mục tiêu:**

- unique `public_id`;
- unique `active_customer_guard`;
- `(customer_id, created_at DESC, cart_id DESC)` cho cart history;
- `(updated_at, cart_id)` cho extraction.

---

### 5.7. `cart_items`

**Mục đích:** lưu variant và quantity hiện hành trong cart, đồng thời giữ dấu vết logical removal cho batch extraction.

**Grain:** một row đại diện cho một variant từng xuất hiện trong một cart.

| Cột | Kiểu logical | Null | Key/constraint | Ý nghĩa nghiệp vụ |
|---|---|---:|---|---|
| `cart_item_id` | BIGINT UNSIGNED | Không | PK | Stable extraction key |
| `cart_id` | BIGINT UNSIGNED | Không | FK → `carts`, RESTRICT | Cart chứa item |
| `variant_id` | BIGINT UNSIGNED | Không | FK → `product_variants`, RESTRICT | Variant được chọn |
| `quantity` | INT UNSIGNED | Không | CHECK `> 0` | Quantity cuối cùng được chọn |
| `is_present` | BOOLEAN | Không | — | Item có đang nằm trong cart hay không |
| `first_added_at` | DATETIME(6) UTC | Không | Immutable | Lần đầu variant được thêm vào cart |
| `removed_at` | DATETIME(6) UTC | Có | State invariant | Lần loại item gần nhất |
| `updated_at` | DATETIME(6) UTC | Không | — | Cursor cho mọi add/update/remove/re-add |

**Business key:** unique `(cart_id, variant_id)`.

**Invariant:**

- Một cart không có hai row cho cùng variant.
- `is_present = true` tương ứng `removed_at = null`.
- `is_present = false` tương ứng `removed_at` khác null.
- Mutation chỉ được thực hiện khi cart active.
- Add/update dùng **absolute desired quantity**, không dùng blind increment; retry cùng request vì vậy không nhân quantity.
- Add-to-cart không kiểm tra rồi giữ inventory; chỉ có thể giới hạn quantity theo cấu hình UX và checkout sẽ revalidate.
- Cart checked out làm toàn bộ item row trở thành immutable.

**Index mục tiêu:**

- unique `(cart_id, variant_id)` đồng thời phục vụ đọc toàn bộ item theo cart;
- `(variant_id, cart_item_id)` hỗ trợ FK/reverse lookup khi cần deactivate hoặc kiểm tra reference;
- `(updated_at, cart_item_id)` cho extraction;
- không thêm index riêng cho `is_present` vì selectivity thấp và luôn query trong một cart.

---

### 5.8. `orders`

**Mục đích:** lưu kết quả chính thức của một checkout và snapshot tổng tiền/địa chỉ.

**Grain:** một row đại diện cho một kết quả checkout của một cart.

| Cột | Kiểu logical | Null | Key/constraint | Ý nghĩa nghiệp vụ |
|---|---|---:|---|---|
| `order_id` | BIGINT UNSIGNED | Không | PK | Internal order key |
| `order_number` | VARCHAR(32) | Không | UNIQUE | Public/business order identifier |
| `cart_id` | BIGINT UNSIGNED | Không | UNIQUE, FK → `carts` | Một cart tạo tối đa một order |
| `customer_id` | BIGINT UNSIGNED | Không | FK → `customers`, RESTRICT | Owner snapshot/reference |
| `checkout_idempotency_key` | VARCHAR(64) | Không | UNIQUE | Deduplicate checkout/unknown commit |
| `status` | VARCHAR(24) | Không | CHECK state set | `paid`, `payment_failed`, `completed` |
| `currency_code` | CHAR(3) | Không | CHECK `VND` | Currency snapshot |
| `subtotal_vnd` | BIGINT UNSIGNED | Không | CHECK `>= 0` | Tổng line subtotal |
| `shipping_fee_vnd` | BIGINT UNSIGNED | Không | CHECK `>= 0` | Shipping fee thực tế |
| `total_vnd` | BIGINT UNSIGNED | Không | CHECK arithmetic | `subtotal_vnd + shipping_fee_vnd` |
| `receiver_name` | VARCHAR(160) | Không | Không rỗng | Shipping snapshot, không join customer profile |
| `receiver_phone` | VARCHAR(32) | Không | Không rỗng | Phone snapshot, lưu dạng chuỗi |
| `shipping_address_text` | VARCHAR(1000) | Không | Không rỗng | Address snapshot tối giản |
| `data_origin` | VARCHAR(16) | Không | CHECK `manual`, `synthetic` | Phân biệt source flow |
| `generation_run_id` | VARCHAR(64) | Có | CHECK theo origin | Generator run nếu có |
| `created_at` | DATETIME(6) UTC | Không | Immutable | Order creation/checkout business time |
| `updated_at` | DATETIME(6) UTC | Không | — | Thay đổi status gần nhất |
| `paid_at` | DATETIME(6) UTC | Có | State invariant | Payment success time |
| `completed_at` | DATETIME(6) UTC | Có | State invariant | Completion time |

**Business key:** `order_number`; `checkout_idempotency_key` là request identity.

**Invariant:**

- Unique `cart_id`: một cart không thể tạo hai order kể cả khi request dùng key khác.
- Unique `checkout_idempotency_key`: retry cùng logical checkout trả cùng order.
- `total_vnd = subtotal_vnd + shipping_fee_vnd`.
- `subtotal_vnd` bằng tổng `order_items.line_total_vnd`; bảo vệ trong checkout transaction và reconciliation.
- Customer của order phải bằng owner của cart; bảo vệ trong transaction.
- `paid`: `paid_at` khác null, `completed_at` null.
- `payment_failed`: cả `paid_at` và `completed_at` null.
- `completed`: cả `paid_at` và `completed_at` khác null, `completed_at >= paid_at`.
- Order amount, address, customer và cart reference không được sửa sau insert; chỉ state/timestamps được đổi theo state machine.

**Index mục tiêu:**

- unique `order_number`, `cart_id`, `checkout_idempotency_key`;
- `(customer_id, created_at DESC, order_id DESC)` cho order history keyset pagination;
- `(status, created_at, order_id)` cho internal completion/generator lookup;
- `(updated_at, order_id)` cho mutable extraction.

---

### 5.9. `order_items`

**Mục đích:** lưu line giao dịch và snapshot catalog tại checkout để lịch sử không phụ thuộc master data hiện tại.

**Grain:** một row đại diện cho một variant line trong một order.

| Cột | Kiểu logical | Null | Key/constraint | Ý nghĩa nghiệp vụ |
|---|---|---:|---|---|
| `order_item_id` | BIGINT UNSIGNED | Không | PK | Stable line identity |
| `order_id` | BIGINT UNSIGNED | Không | FK → `orders`, RESTRICT | Order chứa line |
| `variant_id` | BIGINT UNSIGNED | Không | FK → `product_variants`, RESTRICT | Stable source lineage |
| `product_public_id_snapshot` | UUID binary | Không | Snapshot | Product identity tại checkout |
| `category_code_snapshot` | VARCHAR(64) | Không | Snapshot | Category business key tại checkout |
| `category_name_snapshot` | VARCHAR(160) | Không | Snapshot | Category label tại checkout |
| `product_name_snapshot` | VARCHAR(200) | Không | Snapshot | Product name tại checkout |
| `sku_snapshot` | VARCHAR(64) | Không | Snapshot | SKU tại checkout |
| `size_code_snapshot` | VARCHAR(32) | Không | Snapshot | Size tại checkout |
| `color_code_snapshot` | VARCHAR(64) | Không | Snapshot | Color tại checkout |
| `unit_price_vnd` | BIGINT UNSIGNED | Không | CHECK `>= 0` | Giá bán thực tế/đơn vị |
| `quantity` | INT UNSIGNED | Không | CHECK `> 0` | Số lượng mua |
| `line_total_vnd` | BIGINT UNSIGNED | Không | CHECK arithmetic | `unit_price_vnd * quantity` |
| `created_at` | DATETIME(6) UTC | Không | Immutable | Cùng transaction với order |

**Business key:** unique `(order_id, variant_id)` vì cart đã aggregate quantity theo variant.

**Invariant:**

- Mọi field là immutable sau insert.
- `line_total_vnd = unit_price_vnd * quantity`.
- Line snapshot lấy từ catalog row trong checkout transaction, không lấy từ client.
- Tổng line của order bằng `orders.subtotal_vnd`.
- `variant_id` giữ lineage; snapshot name/SKU/category giữ historical truth nếu master data đổi.

**Index mục tiêu:**

- unique `(order_id, variant_id)` phục vụ order detail;
- `(variant_id, order_item_id)` hỗ trợ FK và kiểm tra historical reference của variant;
- `(created_at, order_item_id)` cho append-only extraction;
- không thêm analytical index theo category/product trên OLTP; Spark/Gold xử lý workload đó.

---

### 5.10. `payments`

**Mục đích:** lưu payment snapshot gắn với order; runtime storefront chỉ tạo payment thành công sau khi checkout validation đạt.

**Grain:** một row đại diện cho một payment outcome của một order.

| Cột | Kiểu logical | Null | Key/constraint | Ý nghĩa nghiệp vụ |
|---|---|---:|---|---|
| `payment_id` | BIGINT UNSIGNED | Không | PK | Internal payment key |
| `payment_reference` | VARCHAR(64) | Không | UNIQUE | Public payment identifier |
| `order_id` | BIGINT UNSIGNED | Không | UNIQUE, FK → `orders` | Đúng một payment/order |
| `payment_idempotency_key` | VARCHAR(64) | Không | UNIQUE | Stable identity của payment tạo bởi checkout |
| `status` | VARCHAR(16) | Không | CHECK `succeeded`, `failed` | Final payment outcome |
| `currency_code` | CHAR(3) | Không | CHECK `VND` | Currency snapshot |
| `amount_vnd` | BIGINT UNSIGNED | Không | CHECK `>= 0` | Amount attempted/collected |
| `failure_code` | VARCHAR(64) | Có | Status invariant | Lý do failure machine-readable |
| `attempted_at` | DATETIME(6) UTC | Không | Business event time | Thời điểm payment outcome có hiệu lực |
| `created_at` | DATETIME(6) UTC | Không | Immutable | Commit time ghi payment |

**Business key:** `payment_reference`.

**Invariant:**

- Unique `order_id`: một order đúng một payment row.
- Payment row là immutable/final, không có pending state trong TLCN.
- `amount_vnd = orders.total_vnd` và currency bằng order; bảo vệ trong checkout transaction/reconciliation.
- Runtime storefront chỉ insert `succeeded`, tương ứng order initial status `paid` và `failure_code = null`.
- `failed`/`payment_failed` chỉ phục vụ dữ liệu synthetic có chủ đích hoặc lịch sử cũ; `failure_code` bắt buộc có.
- Checkout không gọi payment service, không nhận scenario và không random outcome.

**Index mục tiêu:**

- unique `payment_reference`, `order_id`, `payment_idempotency_key`;
- `(created_at, payment_id)` cho append-only extraction;
- không cần index `status` chỉ để dashboard vì analytics không đọc OLTP.

---

### 5.11. `order_status_history`

**Mục đích:** giữ immutable history cho mọi order state transition.

**Grain:** một row đại diện cho một transition của một order.

| Cột | Kiểu logical | Null | Key/constraint | Ý nghĩa nghiệp vụ |
|---|---|---:|---|---|
| `order_status_history_id` | BIGINT UNSIGNED | Không | PK | Stable transition identity |
| `order_id` | BIGINT UNSIGNED | Không | FK → `orders`, RESTRICT | Order được chuyển trạng thái |
| `from_status` | VARCHAR(24) | Có | Transition CHECK | Null cho initial state |
| `to_status` | VARCHAR(24) | Không | Transition CHECK | State sau transition |
| `transition_source` | VARCHAR(32) | Không | Bounded code | `checkout`, `internal_endpoint`, `generator`, `system`, `admin` |
| `reason` | VARCHAR(500) | Có | — | Mô tả bổ sung nếu có |
| `transition_idempotency_key` | VARCHAR(64) | Không | UNIQUE | Deduplicate transition request |
| `transitioned_at` | DATETIME(6) UTC | Không | Business event time | Thời điểm transition có hiệu lực |
| `created_at` | DATETIME(6) UTC | Không | Immutable | Commit time insert history |

**Business key:** `transition_idempotency_key`; unique `(order_id, to_status)` phù hợp state machine TLCN không lặp state.

**Invariant:** chỉ cho phép ba loại row:

```text
NULL             → paid
NULL             → payment_failed
paid             → completed
```

- Initial history được insert cùng transaction tạo order.
- Completion history được insert cùng transaction update order.
- History không update/delete; runtime DB role chỉ cần `SELECT` và `INSERT` trên bảng này.
- `orders.status` phải bằng `to_status` mới nhất theo transaction order; reconciliation kiểm tra lại.

**Index mục tiêu:**

- unique `transition_idempotency_key`;
- unique `(order_id, to_status)` ngăn duplicate state;
- `(order_id, transitioned_at, order_status_history_id)` cho lifecycle lookup;
- `(created_at, order_status_history_id)` cho append-only extraction.

---

### 5.12. `inventory`

**Mục đích:** lưu tồn kho khởi tạo và current stock balance có độ trễ thấp cho website/checkout.

**Grain:** một row đại diện cho opening/current balance của một variant trong kho duy nhất.

| Cột | Kiểu logical | Null | Key/constraint | Ý nghĩa nghiệp vụ |
|---|---|---:|---|---|
| `variant_id` | BIGINT UNSIGNED | Không | PK, FK → `product_variants` | One-to-one variant balance |
| `opening_on_hand` | BIGINT UNSIGNED | Không | CHECK `>= 0`, immutable | Tồn kho ban đầu được seed cho variant |
| `on_hand` | BIGINT UNSIGNED | Không | CHECK `>= 0` | Số lượng vật lý logic hiện có |
| `version` | BIGINT UNSIGNED | Không | Monotonic | Hỗ trợ compare-and-set/debug conflict |
| `updated_at` | DATETIME(6) UTC | Không | — | Lần balance thay đổi gần nhất |

**Business key/PK:** `variant_id`.

**Invariant:**

- Một variant tối đa một inventory row.
- Sellable active variant phải có inventory row.
- Khi seed: `on_hand = opening_on_hand`.
- `opening_on_hand` không được sửa sau seed.
- `0 <= on_hand <= opening_on_hand` trong mọi committed state.
- Không có `reserved`; available trong TLCN chính là `on_hand`.
- Chỉ checkout hợp lệ với payment `succeeded` được giảm `on_hand`; checkout bị validation từ chối không thay đổi balance.
- TLCN không hỗ trợ restock hoặc adjustment cho inventory hiện hữu; admin chỉ xem tồn và đặt trạng thái bán.
- Pipeline đối soát `opening_on_hand - SUM(order_items.quantity của succeeded payments) = on_hand` theo variant.

**Index mục tiêu:**

- PK `variant_id` phục vụ checkout point lookup;
- `(updated_at, variant_id)` cho mutable extraction;
- không index `on_hand` trên OLTP chỉ để low-stock dashboard.

---

### 5.13. `wishlist_items`

**Mục đích:** lưu current wishlist của customer và giữ logical removal cho incremental extraction.

**Grain:** một row đại diện cho một product từng được một customer thêm vào wishlist.

| Cột | Kiểu logical | Null | Key/constraint | Ý nghĩa nghiệp vụ |
|---|---|---:|---|---|
| `wishlist_item_id` | BIGINT UNSIGNED | Không | PK | Stable internal/extraction key |
| `customer_id` | BIGINT UNSIGNED | Không | FK → `customers`, RESTRICT | Owner đã đăng nhập |
| `product_id` | BIGINT UNSIGNED | Không | FK → `products`, RESTRICT | Product được yêu thích; không khóa variant |
| `is_present` | BOOLEAN | Không | CHECK với `removed_at` | Có đang nằm trong wishlist hay không |
| `first_added_at` | DATETIME(6) UTC | Không | Immutable | Lần đầu customer thêm product |
| `last_added_at` | DATETIME(6) UTC | Không | CHECK `>= first_added_at` | Lần add/re-add gần nhất |
| `removed_at` | DATETIME(6) UTC | Có | CHECK state/time | Lần remove gần nhất |
| `updated_at` | DATETIME(6) UTC | Không | Monotonic theo mutation | Cursor incremental extraction |

**Business key:** unique `(customer_id, product_id)`.

**Invariant:**

- Một customer có một wishlist mặc định nhưng có thể có nhiều product khác nhau.
- Cùng product chỉ có một row/customer; re-add cập nhật row cũ.
- `is_present = true` tương ứng `removed_at = null`; false tương ứng removed time có giá trị.
- PUT add và DELETE remove biểu diễn desired state, retry không đảo trạng thái.
- Chỉ add product/category active; remove vẫn được phép khi product đã inactive.
- Product/customer không hard delete; anonymization không xóa quan hệ phục vụ lineage.

**Index mục tiêu:**

- unique `(customer_id, product_id)` bảo vệ grain;
- `(customer_id, is_present, last_added_at DESC, wishlist_item_id DESC)` cho wishlist listing;
- `(product_id, wishlist_item_id)` cho FK/reverse lookup;
- `(updated_at, wishlist_item_id)` cho mutable extraction.

---

## 6. State machine

### 6.1. Cart

```text
active ──checkout──> checked_out
```

- Không có transition ngược.
- Runtime chỉ đóng cart sau khi toàn bộ checkout validation đạt và order/payment đã được tạo.
- Checkout bị từ chối giữ cart `active` để customer sửa dữ liệu hoặc tồn kho rồi thử lại.

### 6.2. Order

Runtime storefront:

```text
checkout ──> paid ──complete──> completed
```

Synthetic fixture có thể tạo trực tiếp `payment_failed` để kiểm thử pipeline, nhưng runtime storefront không đi vào nhánh này.

- Order được tạo trực tiếp ở `paid` vì scope không có asynchronous payment provider.
- `payment_failed` synthetic và `completed` là terminal trong TLCN.
- Không cho `payment_failed → paid`, `completed → paid` hoặc completion lặp.

### 6.3. Payment

Runtime storefront:

```text
succeeded
```

`failed` chỉ dành cho synthetic fixture/lịch sử cũ. Payment row được tạo với final outcome và không update state.

---

## 7. Business invariant catalogue

| ID | Invariant | Cơ chế bảo vệ chính | Cơ chế bổ sung |
|---|---|---|---|
| INV-01 | Email normalized unique | UNIQUE | Normalize trước transaction; map duplicate-key thành domain error |
| INV-02 | Một credential/customer | PK/FK one-to-one | Cùng transaction registration |
| INV-03 | Category không cycle | Application ancestor validation | Lock hierarchy path; admin operation tần suất thấp |
| INV-04 | SKU unique | UNIQUE | Không tái sử dụng SKU inactive |
| INV-05 | Không trùng size/color/product | Composite UNIQUE | Normalize size/color trước insert |
| INV-06 | Giá/amount/quantity đúng sign | Data type + CHECK | Pydantic validation |
| INV-07 | Một active cart/customer | Generated unique guard | Retry create-cart race rồi đọc winner |
| INV-08 | Một variant/cart | Composite UNIQUE | Cart row lock + idempotent absolute quantity |
| INV-09 | Chỉ sửa active cart | Transaction + cart row lock | State recheck sau lock |
| INV-10 | Một order/cart | UNIQUE `orders.cart_id` | Cart lock trong checkout |
| INV-11 | Duplicate checkout trả cùng result | UNIQUE idempotency key | Request fingerprint/customer/cart validation |
| INV-12 | Order arithmetic chính xác | CHECK tổng order + transaction | Reconcile sum order items |
| INV-13 | Order item arithmetic chính xác | CHECK line total | Server-side exact integer calculation |
| INV-14 | Một payment/order | UNIQUE `payments.order_id` | Insert cùng order transaction |
| INV-15 | Payment amount/status khớp order | Same transaction | Silver DQ/reconciliation |
| INV-16 | Order transition hợp lệ | Row lock + transition map | History transition CHECK |
| INV-17 | Không duplicate transition | UNIQUE order/to-state + idempotency | Return committed result khi retry |
| INV-18 | `0 <= on_hand <= opening_on_hand` | CHECK + locked/conditional update | Last-item concurrency test |
| INV-19 | `opening_on_hand` immutable sau khi tạo variant | Không có update path + runtime privilege | Reset/reseed nếu cần đổi baseline |
| INV-20 | Opening trừ succeeded sold units bằng current balance | Checkout transaction | Pipeline reconciliation theo variant |
| INV-21 | Transaction snapshot immutable | Runtime grants/repository policy | No update endpoint; audit tests |
| INV-22 | Extracted delete không bị mất | Không hard delete; logical removal/inactive | Initial snapshot + lookback extraction |
| INV-23 | Synthetic/manual phân biệt được | `data_origin` + run ID | Generator contract và DQ rule |
| INV-24 | Một product/customer trong wishlist | UNIQUE `(customer_id, product_id)` | Customer row lock + desired-state API |
| INV-25 | Wishlist presence/time nhất quán | CHECK | Logical removal và DB timestamp |

Các invariant liên bảng như tổng order item, payment/order match và `opening_on_hand - succeeded sold units = on_hand` không thể được bảo vệ hoàn toàn bằng `CHECK`; chúng phải được duy trì trong cùng checkout transaction và được pipeline reconciliation kiểm tra độc lập.

---

## 8. Transaction catalogue

### 8.1. TX-01 — Register customer

| Thuộc tính | Thiết kế |
|---|---|
| Trigger | `POST /register` |
| Đọc | Lookup email normalized nếu cần thông báo sớm |
| Ghi | `customers`, `customer_credentials` |
| Boundary | Begin ngay trước insert customer; commit sau credential insert |
| Isolation | `READ COMMITTED` |
| Concurrency | UNIQUE email là arbiter cuối cùng; pre-check không bảo đảm uniqueness |
| Failure | Rollback cả customer và credential |
| Retry | Chỉ retry deadlock/transient error; duplicate email là domain error |
| Idempotency | Có thể dùng stable registration request key ở API nếu cần; không bắt buộc thêm bảng trong TLCN |
| OLAP | Customer row; credential bị loại khỏi extraction |

### 8.2. TX-02 — Create/get active cart và cart mutation

API nên biểu diễn desired state bằng absolute quantity:

- add/update: set `quantity = requested_quantity`, `is_present = true`, `removed_at = null`;
- remove: set `is_present = false`, `removed_at = database_now`.

**Boundary và thứ tự:**

1. Begin `READ COMMITTED`.
2. Tìm active cart theo unique guard và lock cart row.
3. Nếu chưa có, insert active cart.
4. Nếu create-cart race vi phạm unique guard, rollback statement/savepoint phù hợp, đọc row winner rồi tiếp tục trong clean transaction.
5. Recheck customer/cart active.
6. Lock cart item `(cart_id, variant_id)` nếu tồn tại.
7. Recheck product/variant active khi add/update.
8. Insert/update logical item và `carts.updated_at`.
9. Commit.

**Concurrency:** lock cart root trước item để checkout không chạy song song với mutation. Việc serial hóa mutation trong cùng cart là chấp nhận được vì cart nhỏ và transaction ngắn.

**Idempotency:** set absolute quantity làm retry tự nhiên idempotent; MySQL cart state là nguồn quyết định duy nhất trong TLCN.

**Failure:** rollback toàn bộ; không có inventory side effect.

### 8.3. TX-03 — Checkout

Runtime checkout không nhận payment scenario và không tính random outcome. Payment `succeeded` chỉ được ghi sau khi toàn bộ precondition đã được kiểm tra trong transaction. Không gọi external API và không chờ network trong transaction.

**Boundary và thứ tự khóa:**

1. Nhận `checkout_idempotency_key` và request fingerprint.
2. Begin `READ COMMITTED`.
3. Lookup order theo idempotency key:
   - nếu tồn tại và cùng customer/cart/request semantics, trả committed result;
   - nếu cùng key nhưng khác request semantics, trả idempotency conflict.
4. Lock cart row theo `cart_id`; xác nhận owner và state `active`.
5. Nếu cart đã checked out, lookup order theo unique `cart_id` và trả existing result hoặc conflict; không tạo order mới.
6. Lock các present cart item; reject nếu cart rỗng.
7. Đọc/khóa category, product và variant cần snapshot theo thứ tự key tăng dần; validate active.
8. Lock inventory row theo `variant_id` tăng dần.
9. Validate `on_hand >= quantity` cho mọi line.
10. Tính `order_items`, subtotal, shipping fee và total bằng integer từ dữ liệu server.
11. Insert order `paid`, toàn bộ `order_items`, payment `succeeded` và initial `order_status_history`.
12. Với từng variant theo thứ tự tăng dần:
    - giảm `inventory.on_hand` bằng locked/conditional update;
    - tăng `version` và `updated_at`.
13. Chuyển cart sang `checked_out`, set `checked_out_at` và `updated_at`.
14. Commit.

**Atomicity:** order, items, payment, initial history, cart closing và inventory decrement phải cùng commit hoặc cùng rollback.

**Idempotency/unknown commit:** client retry cùng `checkout_idempotency_key`. Unique key và unique cart/order cho phép trả lại order đã commit mà không bán hàng lần hai.

**Failure:**

- out-of-stock, inactive variant hoặc cart rỗng: rollback, cart giữ active;
- constraint conflict do concurrent checkout: re-read bằng cart/idempotency key trước khi quyết định retry;
- deadlock/lock timeout: retry toàn transaction tối đa hữu hạn với jitter;
- lỗi non-transient: rollback và trả domain error.

### 8.4. TX-04 — Complete paid order

| Thuộc tính | Thiết kế |
|---|---|
| Trigger | Internal endpoint hoặc generator |
| Đọc | Order theo ID/number, history theo idempotency key |
| Ghi | `orders.status/completed_at/updated_at`, insert history |
| Boundary | Begin trước lock order; commit sau history insert |
| Isolation | `READ COMMITTED` + `FOR UPDATE` order row |
| Invariant | Chỉ `paid → completed`; current state và history atomic |
| Duplicate | Cùng key trả committed result; key khác trên completed order cũng không tạo transition mới |
| Protection | Unique transition key và unique `(order_id, to_status)` |
| Retry | Deadlock/timeout retry hữu hạn |
| OLAP | Order current state và immutable transition |

---

### 8.5. TX-05 — Add/remove wishlist product

| Thuộc tính | Thiết kế |
|---|---|
| Trigger | `PUT` hoặc `DELETE /wishlist/products/{product_public_id}` |
| Đọc | Customer, product/category và wishlist item theo business key |
| Ghi | Insert hoặc update `wishlist_items` current state |
| Boundary | Begin trước customer lock; commit sau desired state được flush |
| Isolation | `READ COMMITTED` |
| Concurrency | Lock customer rồi wishlist row; UNIQUE là arbiter cuối cùng |
| Idempotency | PUT-present và DELETE-absent là no-op; retry không đổi timestamps lần nữa |
| Delete semantics | Remove set `is_present=false`, `removed_at=database_now`; không hard delete |
| OLAP | Current/logical state từ OLTP; TLCN không bảo tồn mọi add/remove trung gian giữa hai batch |

---

## 9. Isolation và concurrency analysis

### 9.1. Isolation decision matrix

| Nghiệp vụ | Isolation | Anomaly cần ngăn | Biện pháp bổ sung | Vì sao không cần cao hơn |
|---|---|---|---|---|
| Login/catalog/order history read | Autocommit `READ COMMITTED` | Dirty read | MVCC | Không ra quyết định trên tập thay đổi nhiều row |
| Registration | `READ COMMITTED` | Duplicate email | UNIQUE | Serializable không tốt hơn unique arbiter |
| Cart mutation | `READ COMMITTED` | Lost update, mutation vs checkout | Lock cart/item, absolute quantity | Transaction chỉ chạm một cart nhỏ |
| Wishlist mutation | `READ COMMITTED` | Duplicate row/lost desired state | Customer + item lock, UNIQUE, PUT/DELETE desired state | Transaction chạm một customer/product |
| Checkout | `READ COMMITTED` | Oversell, duplicate checkout, inconsistent snapshot | Explicit row locks, conditional update, UNIQUE, lock order cố định | Invariant không dựa trên predicate rộng |
| Complete order | `READ COMMITTED` | Duplicate transition/lost update | Lock order, unique history | Một aggregate root |
| Category re-parent | `READ COMMITTED` với path locks; nâng cục bộ nếu cần | Cycle/write skew | Ancestor validation và serialize admin operation | Không phải hot path; không đặt global Serializable |

### 9.2. Lost update

| Tình huống | Rủi ro | Cách ngăn |
|---|---|---|
| Hai request set quantity cùng cart item | Request sau ghi đè request trước | Lock cart/item; API dùng desired state; last committed command là kết quả có chủ đích |
| Checkout và cart update | Checkout đọc item trong lúc quantity đổi | Cả hai lock cart root trước; chỉ một transaction tiến hành |
| Hai checkout mua last item | Cả hai cùng thấy đủ hàng | Lock inventory theo variant; recheck sau lock; conditional decrement |
| Hai completion | Hai history row hoặc status overwrite | Lock order + unique transition constraints |

### 9.3. Write skew và phantom

- **Một active cart/customer:** nếu chỉ `SELECT rồi INSERT`, hai transaction có thể cùng không thấy cart. Generated unique guard biến predicate invariant thành uniqueness invariant, loại write skew/phantom.
- **Một order/cart:** unique `orders.cart_id` là arbiter, ngoài cart row lock.
- **Một payment/order:** unique `payments.order_id` là arbiter.
- **Category cycle:** là multi-row graph invariant, không giải quyết bằng CHECK. TLCN nên serialize thao tác re-parent hiếm gặp; nếu sau này có concurrent admin, áp dụng `SERIALIZABLE` cục bộ hoặc một hierarchy-root lock.
- **Inventory:** invariant nằm trên một row/variant, vì vậy row lock/conditional update đủ; không cần predicate lock toàn bảng.

### 9.4. Deadlock control

Thứ tự khóa chuẩn:

```text
customer (nếu cần)
→ cart
→ cart_items theo variant_id tăng dần
→ catalog rows theo key tăng dần
→ inventory theo variant_id tăng dần
→ order
```

- Không lock inventory theo thứ tự item từ request.
- Không gọi network/email/log collector trong transaction.
- Không chạy Spark/extraction query bên trong application transaction.
- Giữ transaction ngắn và không chờ user.
- Bắt MySQL deadlock/lock-timeout rõ ràng; retry toàn transaction tối đa 3 lần với exponential backoff + jitter.
- Theo dõi deadlock count, lock-wait duration và checkout transaction latency.

### 9.5. Duplicate execution và unknown commit

- Checkout: `checkout_idempotency_key` + unique cart/order.
- Payment: `payment_idempotency_key` + unique order/payment.
- Completion: `transition_idempotency_key` + unique order/to-state.
- Cart mutation: absolute desired quantity.
- Khi client timeout sau commit, không đoán transaction thất bại; retry bằng cùng key và đọc committed row.
- Cùng idempotency key nhưng khác customer/cart/amount semantics phải bị từ chối, không trả nhầm kết quả.

---

## 10. Index strategy

### 10.1. Nguyên tắc

- InnoDB row-oriented storage cho OLTP.
- Clustered PK là internal sequential key để giảm page split/fragmentation.
- Public UUID/business key là secondary unique index.
- Listing dùng keyset pagination theo internal ID hoặc `(created_at, id)`, không dùng offset lớn.
- Composite index đặt equality columns trước, sau đó sort/range và stable tie-breaker.
- Không tạo index phục vụ dashboard trên primary OLTP.
- Không index mọi FK một cách mù quáng; chỉ giữ FK/index phục vụ join/lock/read pattern thực tế.
- Chưa partition/shard vì dataset TLCN và single-node workload không chứng minh nhu cầu.

### 10.2. Index catalogue

| Bảng | Index logical | Query/invariant mục tiêu | Chi phí/trade-off |
|---|---|---|---|
| `customers` | UQ `public_id` | API identity | Secondary write nhỏ |
| `customers` | `(updated_at, customer_id)` | Incremental extraction | Thêm write mỗi profile/status update |
| `customer_credentials` | UQ `email_normalized` | Login + uniqueness | PII index; DB access phải hạn chế |
| `categories` | UQ `code`, UQ `public_id` | Business/public lookup | Master data ít ghi |
| `categories` | `(parent_category_id, is_active, category_id)` | Children listing | Hỗ trợ hierarchy read |
| `categories` | `(updated_at, category_id)` | Extraction | Chấp nhận được vì low-write |
| `products` | UQ `slug`, UQ `public_id` | Product detail | Hai stable lookup paths |
| `products` | `(category_id, is_active, product_id)` | Category listing/keyset | Không cover text/image để tránh index lớn |
| `products` | `(is_active, product_id)` | All-product listing | Low selectivity prefix nhưng hữu ích cho ordered scan |
| `products` | `(updated_at, product_id)` | Extraction | Write amplification khi catalog update |
| `product_variants` | UQ `sku`, UQ `public_id` | SKU/API lookup | Correctness + lookup |
| `product_variants` | UQ `(product_id, size_code, color_code)` | Combination invariant | Constraint bắt buộc |
| `product_variants` | `(product_id, is_active, variant_id)` | Product detail variants | Product prefix có selectivity tốt |
| `product_variants` | `(updated_at, variant_id)` | Extraction | Low-write master cost |
| `carts` | UQ `public_id` | Cart API lookup | Stable reference |
| `carts` | UQ `active_customer_guard` | Một active cart/customer | Correctness-critical |
| `carts` | `(customer_id, created_at DESC, cart_id DESC)` | Cart history | Secondary insert cost |
| `carts` | `(updated_at, cart_id)` | Extraction | Mutation write cost chấp nhận được |
| `cart_items` | UQ `(cart_id, variant_id)` | Item read/upsert/invariant | Index prefix phục vụ cart items |
| `cart_items` | `(variant_id, cart_item_id)` | FK/reverse reference lookup | Bắt buộc do composite UQ không bắt đầu bằng variant |
| `cart_items` | `(updated_at, cart_item_id)` | Extraction | Hot-table write amplification; cần cho DE scope |
| `wishlist_items` | UQ `(customer_id, product_id)` | Grain + idempotent desired state | Customer prefix phục vụ point lookup |
| `wishlist_items` | `(customer_id, is_present, last_added_at, wishlist_item_id)` | Wishlist listing/keyset | Low-write per customer |
| `wishlist_items` | `(product_id, wishlist_item_id)` | FK/reverse lookup | Master reference safety |
| `wishlist_items` | `(updated_at, wishlist_item_id)` | Incremental extraction | Mutation write cost chấp nhận được |
| `orders` | UQ `order_number`, UQ `cart_id`, UQ `checkout_idempotency_key` | Lookup + correctness | Ba unique path nhưng đều bắt buộc |
| `orders` | `(customer_id, created_at DESC, order_id DESC)` | Order history | Web read quan trọng |
| `orders` | `(status, created_at, order_id)` | Completion generator lookup | Dataset nhỏ; bỏ nếu execution plan không dùng |
| `orders` | `(updated_at, order_id)` | Extraction including completion | Bắt buộc cho batch cursor |
| `order_items` | UQ `(order_id, variant_id)` | Order detail + grain | Correctness |
| `order_items` | `(variant_id, order_item_id)` | FK/historical reference lookup | Append-only nên write cost dự đoán được |
| `order_items` | `(created_at, order_item_id)` | Extraction | Append-only, sequential-friendly |
| `payments` | UQ `payment_reference`, UQ `order_id`, UQ `payment_idempotency_key` | Lookup + one payment + dedup | Correctness-critical |
| `payments` | `(created_at, payment_id)` | Extraction | Append-only |
| `order_status_history` | UQ `transition_idempotency_key` | Dedup | Correctness-critical |
| `order_status_history` | UQ `(order_id, to_status)` | Không lặp state | Phù hợp state machine TLCN |
| `order_status_history` | `(order_id, transitioned_at, order_status_history_id)` | Lifecycle read | Stable tie-breaker |
| `order_status_history` | `(created_at, order_status_history_id)` | Extraction | Append-only |
| `inventory` | PK `variant_id` | Checkout point lock | Không cần surrogate khác |
| `inventory` | `(updated_at, variant_id)` | Extraction | Update mỗi succeeded checkout |

### 10.3. Index không nên thêm trong TLCN

- `orders.total_vnd`, `payments.amount_vnd` cho báo cáo.
- `inventory.on_hand` cho dashboard low-stock.
- `order_items.category_name_snapshot` hoặc product name cho BI.
- JSON index và generic attribute index. FULLTEXT chỉ thêm nếu performance experiment chứng minh bounded `LIKE` không đủ.
- Mọi status boolean riêng lẻ khi không đi cùng query pattern có selectivity/sort phù hợp.

Các truy vấn trên thuộc tính này phải chạy ở Gold/MySQL `analytics`, không chạy trên OLTP primary.

---

## 11. OLAP và batch-extraction readiness

### 11.1. Current state, snapshot và immutable history

| Nhóm | Bảng | Cách downstream xử lý |
|---|---|---|
| Current master | customers, categories, products, variants | Silver merge current state theo stable key; Gold dimension hiện hành |
| Current transaction | carts, cart_items, wishlist_items, orders, inventory | Silver merge theo `updated_at`/PK; order status history bổ sung lifecycle |
| Immutable snapshot | order_items, payments | Append/deduplicate theo PK/business key |
| Immutable history | order_status_history | Append/deduplicate; không overwrite transition cũ |
| Security-only | customer_credentials | Không extract |

### 11.2. Snapshot đủ cho Gold

- `fact_order`: `orders` cung cấp one-row/order, status, customer, subtotal, shipping, total và business timestamps.
- `fact_order_item`: `order_items` cung cấp one-row/order/variant, exact price, quantity, line total và catalog snapshot.
- `fact_payment`: `payments` cung cấp one-row/order, outcome, amount và attempted time.
- `fact_inventory_daily_snapshot`: chụp `opening_on_hand`/`on_hand` từ `inventory` tại cutoff; sold units trong kỳ được tổng hợp từ order items có succeeded payment.
- `dim_customer`: dùng `customers.public_id` đã pseudonymize; bỏ display name nếu không cần.
- `dim_category/product/variant`: dùng stable public/business keys từ master; fact order item giữ snapshot để không làm sai lịch sử khi label/category đổi.

### 11.3. Incremental extraction

| Loại bảng | Cursor |
|---|---|
| Mutable có surrogate PK | `(updated_at, internal_pk)` |
| `inventory` | `(updated_at, variant_id)` |
| Append-only | `(created_at, internal_pk)` |
| Credential | Không đăng ký source |

Yêu cầu vận hành:

- timestamp do database tạo, không tin client clock;
- precision microsecond và PK tie-breaker bắt buộc;
- capture high cursor trước extract và chỉ commit cursor sau full run thành công;
- configurable lookback để hấp thụ transaction boundary/clock edge;
- Bronze giữ extraction identity và source PK;
- logical removal/inactive phải được extract như update;
- initial snapshot dùng cùng stable key với incremental.

### 11.4. Giới hạn của cursor `updated_at`

Nếu cùng mutable row thay đổi nhiều lần giữa hai batch, extraction có thể chỉ thấy trạng thái cuối. Điều này được chấp nhận trong TLCN cho:

- customer profile;
- category/product/variant current attributes;
- current cart/cart item state;
- current wishlist item state;
- current inventory balance.

Một cart hoặc wishlist item bị remove rồi re-add giữa hai batch có thể chỉ xuất hiện ở trạng thái cuối `is_present = true`; schema chỉ bảo đảm trạng thái cuối được extract tại batch cutoff.

Các thay đổi cần lịch sử chính xác không dựa riêng vào `updated_at`:

- order state dùng `order_status_history`;
- payment và order item là immutable rows;
- sales-driven inventory history được suy ra từ succeeded payment + immutable order items; không có restock/adjustment trong TLCN;
- cart abandonment chỉ dùng cart/order state tại batch cutoff.

Vì vậy schema không giả vờ cung cấp full mutation history cho mọi mutable field nhưng vẫn đủ rebuild các fact/KPI OLTP-only đã chốt.

### 11.5. Reconciliation rules từ schema

1. `orders.subtotal_vnd = SUM(order_items.line_total_vnd)` theo order.
2. `orders.total_vnd = subtotal_vnd + shipping_fee_vnd`.
3. `payments.amount_vnd = orders.total_vnd`.
4. Payment succeeded ↔ initial order status paid; payment failed ↔ initial status payment_failed.
5. `inventory.opening_on_hand - SUM(order_items.quantity của succeeded payments) = inventory.on_hand` theo variant.
6. Payment-failed order items không được tính vào sold units hoặc inventory decrement.
7. `0 <= inventory.on_hand <= inventory.opening_on_hand`.
8. Current order status = latest valid status history.
9. Mọi checked-out cart có đúng một order; mọi order tham chiếu checked-out cart.

---

## 12. Read/write workload

| Flow | Read pattern | Write pattern | Consistency/latency | Contention |
|---|---|---|---|---|
| Login | Point lookup email | Không hoặc security timestamp ngoài hot path | Strong auth decision, thấp | Thấp |
| Product listing/search/filter | Product/category + matching active variant range + keyset | Không | Read committed, thấp | Thấp; bounded catalog query |
| Product detail | Slug/SKU + variants + inventory | Không | Current state đủ | Thấp |
| Wishlist view/mutation | Customer + present items/product | Desired-state insert/update | Strong mutation, thấp | Theo một customer/product |
| Cart view | Public cart/customer + items + variant | Không | Current committed | Theo một customer |
| Cart mutation | Point lock cart/item | Upsert logical state | Strong, thấp | Cùng cart |
| Checkout | Cart/items/catalog/inventory point locks | Order graph + optional inventory decrement | Correctness-critical | Last-item/variant |
| Order history | Customer + time range | Không | Current committed | Thấp |
| Complete order | Point lock order | Status + history | Strong | Cùng order |
| Batch extraction | Time/PK range | Không trên OLTP | Eventual, bounded batch | Có thể tăng read I/O |

Extraction phải chạy theo batch nhỏ, dùng index cursor và không giữ consistent snapshot dài gây áp lực MVCC/undo. Không chạy join fact/dimension hoặc aggregate dashboard trên primary.

---

## 13. Failure, durability và recovery

### 13.1. Transaction failure

- Constraint/domain failure: rollback, không retry tự động trừ create-cart race được xử lý có kiểm soát.
- Deadlock/lock timeout: rollback toàn transaction, retry hữu hạn từ đầu.
- Process crash trước commit: InnoDB rollback incomplete transaction.
- Process/client timeout không rõ commit: query/retry bằng idempotency key, không phát lệnh mới với key mới.
- Pipeline failure không được ghi ngược hoặc sửa source OLTP.

### 13.2. Durability

- API chỉ trả success sau database commit.
- Runtime checkout không gọi payment service bên ngoài nên không tạo distributed consistency gap.
- InnoDB redo/undo/binlog configuration phải ưu tiên durability phù hợp môi trường demo.
- Persistent Docker volume không thay thế backup.
- Trước final demo cần có logical backup và test restore tối thiểu.
- Replication không thuộc TLCN; backup và reproducible generator là hai cơ chế độc lập.

### 13.3. Append-only enforcement

- Application không cung cấp update/delete path cho `order_items`, `payments` và `order_status_history`.
- Runtime DB role chỉ có quyền cần thiết; order history ưu tiên `SELECT` + `INSERT`.
- Migration/maintenance dùng role riêng và phải được audit.
- Không dùng trigger phức tạp để che business logic; transaction service vẫn là nơi điều phối invariant liên bảng.

---

## 14. Security và privacy

- Password chỉ tồn tại dưới dạng adaptive hash trong `customer_credentials`.
- Không log password, hash, token, raw email, phone hoặc shipping address.
- `customer_credentials` không nằm trong source catalogue của Spark.
- Shipping snapshot ở `orders` cần cho source demo nhưng không publish vào Gold/serving.
- Customer key sang Silver/Gold phải pseudonymized; display name/email không cần cho KPI.
- API dùng public key/business key; không tin client-supplied customer ID từ body.
- Internal completion endpoint phải có credential/secret riêng và không public qua frontend.
- Synthetic dataset dùng email/phone/address giả cho demo công khai.

---

## 15. Những kỹ thuật chưa nên triển khai

- Kafka/CDC connector: batch incremental đã đủ cho TLCN.
- Reservation table: checkout hoàn tất đồng bộ trong một transaction ngắn và scope không có external payment wait.
- Multi-warehouse/stock allocation: một kho, một row/variant.
- Redis cart/cache: workload nhỏ, MySQL đủ và cache làm phức tạp consistency.
- Elasticsearch: search/filter bounded trên catalog nhỏ chưa chứng minh cần search engine riêng; MySQL query hiện tại đủ.
- MySQL FULLTEXT: là bước tối ưu có điều kiện sau `EXPLAIN`/performance report, không phải yêu cầu schema ban đầu.
- Partitioning/sharding/read replica: chưa có workload chứng minh.
- Event sourcing/CQRS: current-state relational model + immutable transaction snapshots + order status history đã đủ.
- Generic status/config tables: state set nhỏ, bounded CHECK rõ ràng hơn.

---

## 16. Trình tự triển khai đề xuất

1. Freeze tên bảng, cột, status và invariant trong tài liệu này.
2. Viết migration theo thứ tự dependency:
   - customer;
   - category/product/variant;
   - cart;
   - order/payment/history;
   - inventory.
3. Tạo seed catalog và inventory với `opening_on_hand = on_hand`; không tạo adjustment endpoint.
4. Viết repository/service theo aggregate boundary, không để endpoint tự ghép nhiều write rời rạc.
5. Triển khai register/login/catalog/cart.
6. Triển khai checkout idempotent và completion.
7. Thêm concurrency tests trước khi nối generator.
8. Đăng ký source catalogue, exclusion rule cho credential và extraction cursor/index.
9. Thêm reconciliation SQL/test ở pipeline, không chạy dashboard query trên source.
10. Chỉ tối ưu index sau khi có `EXPLAIN`, row count và local workload report.

---

## 17. Acceptance checklist cho schema

### Structure

- [ ] Đúng 13 bảng nghiệp vụ; không lẫn table Gold/analytics vào OLTP.
- [ ] Mỗi bảng có grain, PK và business key rõ.
- [ ] Mọi FK có delete semantics rõ; transaction history không cascade delete.
- [ ] Public/API key không dùng PII.

### Correctness

- [ ] Database ngăn được hai active cart/customer.
- [ ] Database ngăn duplicate SKU và duplicate product-size-color.
- [ ] Database ngăn hai order/cart và hai payment/order.
- [ ] Amount/quantity/sign/status có NOT NULL/CHECK phù hợp.
- [ ] Checkout success không thể làm `on_hand` âm.
- [ ] Success checkout và inventory decrement commit/rollback cùng nhau.
- [ ] `opening_on_hand` immutable và luôn lớn hơn hoặc bằng `on_hand`.
- [ ] State transition sai bị từ chối và history không bị nhân đôi.

### Idempotency/concurrency

- [ ] Retry checkout sau unknown commit trả cùng order.
- [ ] Hai checkout tranh last item chỉ một transaction thành công bán item.
- [ ] Duplicate completion không tạo transition thứ hai.
- [ ] Mọi multi-row lock theo thứ tự ổn định.

### DE/OLAP batch readiness

- [ ] Credential không được extract.
- [ ] Mutable source có `updated_at` + stable tie-breaker.
- [ ] Append-only source có business/created time + stable PK.
- [ ] Cart item removal và catalog deactivation nhìn thấy qua incremental extract.
- [ ] Order item giữ exact price, quantity và catalog snapshot.
- [ ] Order status history append-only.
- [ ] Chín reconciliation rule ở mục 11.5 chạy được tại cùng cutoff.

---

## 18. Kết luận kiến trúc

Schema đề xuất là một relational OLTP chuẩn hóa vừa đủ trên MySQL/InnoDB, với:

- sequential internal key cho transactional access;
- stable public/business key cho API và downstream;
- database constraint bảo vệ uniqueness và single-row invariant;
- short transaction + row lock bảo vệ cart, checkout và inventory;
- idempotency key xử lý duplicate execution/unknown commit;
- transaction snapshot ở order/order item/payment;
- immutable order status history và inventory baseline/current state có thể đối soát từ succeeded order items;
- explicit extraction cursor/index và delete semantics để phục vụ Bronze/Silver/Gold.

Thiết kế ưu tiên correctness và DE-readiness nhưng không đưa OLAP structure, distributed component hoặc nghiệp vụ ngoài scope vào primary database.
