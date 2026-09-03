# OLTP Table Reference

Mô tả chi tiết 16 bảng MySQL OLTP trong hệ thống D&K E-Commerce. `customer_credentials` bị loại khỏi lakehouse pipeline vì chứa thông tin xác thực.

Nguồn真相 (source of truth): Alembic migrations `0001`–`0009`.

---

## Tổng quan

| # | Bảng | Nhóm | Grain | Mutability | Extract cursor |
|---|------|------|-------|------------|----------------|
| 1 | `customers` | Customer | Một customer | Mutable/anonymizable | `(updated_at, customer_id)` |
| 2 | `categories` | Catalog | Một category | Mutable/inactive | `(updated_at, category_id)` |
| 3 | `products` | Catalog | Một product | Mutable/archive terminal | `(updated_at, product_id)` |
| 4 | `product_variants` | Catalog | Một tổ hợp size-color/product | Mutable/inactive | `(updated_at, variant_id)` |
| 5 | `inventory` | Inventory | Một balance/variant | Mutable, khóa khi checkout/cancel | `(updated_at, variant_id)` |
| 6 | `carts` | Cart | Một chu kỳ cart/customer | Mutable lifecycle | `(updated_at, cart_id)` |
| 7 | `cart_items` | Cart | Một variant/cart | Mutable/logical removal | `(updated_at, cart_item_id)` |
| 8 | `wishlist_items` | Wishlist | Một product từng wishlist/customer | Mutable presence | `(updated_at, wishlist_item_id)` |
| 9 | `coupons` | Promotion | Một coupon code | Mutable/archive terminal | `(updated_at, coupon_id)` |
| 10 | `coupon_redemptions` | Promotion | Một redemption/order | Mutable redeemed/released | `(updated_at, coupon_redemption_id)` |
| 11 | `orders` | Order | Một kết quả checkout/cart | Mutable state, snapshot amount | `(updated_at, order_id)` |
| 12 | `order_items` | Order | Một variant line/order | Append-only snapshot | `(created_at, order_item_id)` |
| 13 | `payments` | Payment | Một payment/order | Append-only | `(created_at, payment_id)` |
| 14 | `refunds` | Refund | Một full refund/payment | Append-only | `(created_at, refund_id)` |
| 15 | `order_status_history` | History | Một transition/order | Append-only | `(created_at, order_status_history_id)` |
| 16 | `product_reviews` | Review | Một review/order_item | Mutable visibility | `(updated_at, review_id)` |

---

## Quy ước chung

- **PK**: `BIGINT UNSIGNED` auto-increment surrogate key
- **Public ID**: `BINARY(16)` UUIDv5 deterministic — lộ qua API, không lộ PK
- **Tiền**: số nguyên VND (`BIGINT UNSIGNED`), không dùng FLOAT/DOUBLE
- **Thời gian**: UTC `DATETIME(6)` — microsecond precision
- **Bảng mutable**: có `updated_at` + composite cursor `(updated_at, PK)`
- **Bảng append-only**: có `created_at` + composite cursor `(created_at, PK)`
- **FK lịch sử**: `ON DELETE RESTRICT` — giữ audit trail
- **引擎**: InnoDB `READ COMMITTED`

---

## 1. `customers`

**Mục đích**: Identity nghiệp vụ, profile, role và trạng thái account.

| Cột | Kiểu | Constraint | Mô tả |
|-----|------|-----------|-------|
| `customer_id` | `BIGINT UNSIGNED` | PK, auto-increment | Surrogate key nội bộ |
| `public_id` | `BINARY(16)` | UK, NOT NULL | UUIDv5 — public identifier |
| `display_name` | `VARCHAR(120)` | NOT NULL | Tên hiển thị |
| `role` | `VARCHAR(16)` | NOT NULL, DEFAULT `'customer'` | `customer` hoặc `admin` |
| `status` | `VARCHAR(16)` | NOT NULL, DEFAULT `'active'` | `active` hoặc `inactive` |
| `data_origin` | `VARCHAR(16)` | NOT NULL, DEFAULT `'manual'` | `manual` hoặc `synthetic` |
| `generation_run_id` | `VARCHAR(64)` | NULLABLE | ID lần generate (synthetic data) |
| `anonymized_at` | `DATETIME(6)` | NULLABLE | Thời điểm PII bị ẩn danh hóa |
| `created_at` | `DATETIME(6)` | NOT NULL, DEFAULT NOW(6) | Thời gian tạo |
| `updated_at` | `DATETIME(6)` | NOT NULL, DEFAULT NOW(6) ON UPDATE | Thời gian cập nhật cuối |

**Check constraints**:
- `status IN ('active', 'inactive')`
- `role IN ('customer', 'admin')`
- `data_origin IN ('manual', 'synthetic')`

**Indexes**:
- `uq_customers_public_id` — UK trên `public_id`
- `ix_customers_role_status_id` — `(role, status, customer_id)`
- `ix_customers_updated_at_customer_id` — extraction cursor

**Invariant**: Anonymize không xóa PK/FK. Role/status thuộc tập cho phép.

---

## 2. `categories`

**Mục đích**: Phân cấp sản phẩm dạng tree. product chỉ thuộc category lá.

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
- `uq_categories_categories_public_id` — UK trên `public_id`
- `ix_categories_parent_is_active_id` — `(parent_category_id, is_active, category_id)`
- `ix_categories_updated_at_category_id` — extraction cursor

**Invariant**: Không tạo chu trình hierarchy. Category lá = không có child.

---

## 3. `products`

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

**Invariant**: Archive là terminal — không cascade sang variant, wishlist hay order item.

---

## 4. `product_variants`

**Mục đích**: Tổ hợp size-color-SKU-giá cho mỗi product.

| Cột | Kiểu | Constraint | Mô tả |
|-----|------|-----------|-------|
| `variant_id` | `BIGINT UNSIGNED` | PK, auto-increment | Surrogate key |
| `public_id` | `BINARY(16)` | UK, NOT NULL | UUIDv5 |
| `product_id` | `BIGINT UNSIGNED` | FK → `products.product_id`, NOT NULL, ON DELETE RESTRICT | Product cha |
| `sku` | `VARCHAR(64)` | UK, NOT NULL | Mã SKU duy nhất |
| `size_code` | `VARCHAR(32)` | NOT NULL | Mã size (VD: `'M'`, `'XL'`) |
| `color_code` | `VARCHAR(64)` | NOT NULL | Mã màu (VD: `'DEN'`) |
| `price_vnd` | `BIGINT UNSIGNED` | NOT NULL | Giá bán (VND, integer) |
| `is_active` | `BOOLEAN` | NOT NULL, DEFAULT `TRUE` | Bật/tắt |
| `created_at` | `DATETIME(6)` | NOT NULL, DEFAULT NOW(6) | |
| `updated_at` | `DATETIME(6)` | NOT NULL, DEFAULT NOW(6) ON UPDATE | |

**Check constraints**:
- `price_vnd >= 0`
- `UNIQUE (product_id, size_code, color_code)` — ngăn trùng tổ hợp

**Indexes**:
- `uq_product_variants_sku` — UK trên `sku`
- `uq_product_variants_public_id` — UK trên `public_id`
- `uq_product_variants_product_size_color` — composite UK
- `ix_product_variants_product_id_is_active_variant_id` — `(product_id, is_active, variant_id)`
- `ix_product_variants_updated_at_variant_id` — extraction cursor

---

## 5. `inventory`

**Mục đích**: Số dư tồn kho cho mỗi variant. Khóa row khi checkout/cancel.

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

**Invariant**: `0 <= on_hand <= opening_on_hand`. Version tăng khi có thay đổi để detect conflict và hỗ trợ extraction.

---

## 6. `carts`

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

## 7. `cart_items`

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

## 8. `wishlist_items`

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

## 9. `coupons`

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
| `total_usage_limit` | `BIGINT UNSIGNED` | NULLABLE | Giới hạn tổng lần dùng (NULL = vô hạn) |
| `per_customer_usage_limit` | `INT UNSIGNED` | NULLABLE | Giới hạn mỗi customer |
| `used_count` | `BIGINT UNSIGNED` | NOT NULL, DEFAULT `0` | Số lần đã dùng |
| `archived_at` | `DATETIME(6)` | NULLABLE | Thời điểm archive (terminal) |
| `archived_by_customer_id` | `BIGINT UNSIGNED` | FK → `customers.customer_id`, NULLABLE, ON DELETE RESTRICT | Admin archive |
| `archive_reason` | `VARCHAR(500)` | NULLABLE | Lý do archive (≥3 ký tự) |
| `created_at` | `DATETIME(6)` | NOT NULL, DEFAULT NOW(6) | |
| `updated_at` | `DATETIME(6)` | NOT NULL, DEFAULT NOW(6) ON UPDATE | |

**Check constraints**:
- `discount_type IN ('percentage', 'fixed_amount')`
- `(discount_type = 'percentage' AND discount_value BETWEEN 1 AND 100) OR (discount_type = 'fixed_amount' AND discount_value > 0)`
- `starts_at < ends_at`
- `total_usage_limit IS NULL OR total_usage_limit > 0`
- `per_customer_usage_limit IS NULL OR per_customer_usage_limit > 0`
- `total_usage_limit IS NULL OR used_count <= total_usage_limit`
- Archive metadata consistency (giống products)
- `archived_at IS NULL OR is_active = FALSE`

**Concurrency**: Checkout khóa row coupon trước khi kiểm tra `used_count`. Tăng counter và insert redemption atomically trong cùng transaction.

**Indexes**:
- `uq_coupons_public_id` — UK trên `public_id`
- `uq_coupons_code_normalized` — UK trên `code_normalized`
- `ix_coupons_updated_at_coupon_id` — extraction cursor
- `ix_coupons_archived_at_coupon_id` — `(archived_at, coupon_id)`

---

## 10. `coupon_redemptions`

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
- `ix_coupon_redemptions_coupon_customer_status` — `(coupon_id, customer_id, status)` — per-customer limit check
- `ix_coupon_redemptions_updated_at_id` — `(updated_at, coupon_redemption_id)` — extraction cursor

---

## 11. `orders`

**Mục đích**: Kết quả checkout. State machine: `paid → confirmed → completed`, `paid → cancelled`.

| Cột | Kiểu | Constraint | Mô tả |
|-----|------|-----------|-------|
| `order_id` | `BIGINT UNSIGNED` | PK, auto-increment | Surrogate key |
| `order_number` | `VARCHAR(32)` | UK, NOT NULL | Mã đơn hàng hiển thị |
| `cart_id` | `BIGINT UNSIGNED` | FK → `carts.cart_id`, UK, NOT NULL, ON DELETE RESTRICT | Cart đã checkout (1:1) |
| `customer_id` | `BIGINT UNSIGNED` | FK → `customers.customer_id`, NOT NULL, ON DELETE RESTRICT | Chủ đơn |
| `checkout_idempotency_key` | `VARCHAR(64)` | UK, NOT NULL | Idempotency key cho checkout |
| `status` | `VARCHAR(24)` | NOT NULL | Trạng thái hiện tại |
| `currency_code` | `CHAR(3)` | NOT NULL, DEFAULT `'VND'` | Luôn VND |
| `subtotal_vnd` | `BIGINT UNSIGNED` | NOT NULL | Tổng tiền hàng (trước giảm giá) |
| `discount_amount_vnd` | `BIGINT UNSIGNED` | NOT NULL, DEFAULT `0` | Số tiền giảm giá |
| `shipping_fee_vnd` | `BIGINT UNSIGNED` | NOT NULL | Phí vận chuyển |
| `total_vnd` | `BIGINT UNSIGNED` | NOT NULL | Tổng thanh toán |
| `coupon_id` | `BIGINT UNSIGNED` | FK → `coupons.coupon_id`, NULLABLE, ON DELETE RESTRICT | Coupon đã áp dụng |
| `coupon_code_snapshot` | `VARCHAR(64)` | NULLABLE | Snapshot mã coupon |
| `coupon_type_snapshot` | `VARCHAR(24)` | NULLABLE | Snapshot loại giảm giá |
| `coupon_value_snapshot` | `BIGINT UNSIGNED` | NULLABLE | Snapshot giá trị giảm |
| `receiver_name` | `VARCHAR(160)` | NOT NULL | Tên người nhận |
| `receiver_phone` | `VARCHAR(32)` | NOT NULL | SĐT người nhận |
| `shipping_address_text` | `VARCHAR(1000)` | NOT NULL | Địa chỉ giao hàng |
| `data_origin` | `VARCHAR(16)` | NOT NULL, DEFAULT `'manual'` | `manual` hoặc `synthetic` |
| `generation_run_id` | `VARCHAR(64)` | NULLABLE | ID lần generate |
| `created_at` | `DATETIME(6)` | NOT NULL, DEFAULT NOW(6) | |
| `updated_at` | `DATETIME(6)` | NOT NULL, DEFAULT NOW(6) ON UPDATE | |
| `paid_at` | `DATETIME(6)` | NULLABLE | Thời điểm thanh toán |
| `confirmed_at` | `DATETIME(6)` | NULLABLE | Thời điểm admin xác nhận |
| `completed_at` | `DATETIME(6)` | NULLABLE | Thời điểm hoàn tất |
| `cancelled_at` | `DATETIME(6)` | NULLABLE | Thời điểm hủy |

**Check constraints**:
- `status IN ('paid', 'payment_failed', 'confirmed', 'completed', 'cancelled')`
- `currency_code = 'VND'`
- `subtotal_vnd >= 0`
- `shipping_fee_vnd >= 0`
- `discount_amount_vnd <= subtotal_vnd`
- `total_vnd = subtotal_vnd - discount_amount_vnd + shipping_fee_vnd`
- Coupon snapshot consistency: Toàn bộ coupon fields NULL + discount=0, HOẶC tất cả NOT NULL + discount>0
- `coupon_type_snapshot` value: `percentage` (1–100) hoặc `fixed_amount` (>0)
- Status–timestamp consistency:
  - `payment_failed`: tất cả timestamp NULL
  - `paid`: `paid_at` NOT NULL, còn lại NULL
  - `confirmed`: `paid_at` + `confirmed_at` NOT NULL, còn lại NULL
  - `completed`: tất cả timestamp NOT NULL (trừ `cancelled_at`)
  - `cancelled`: `paid_at` + `cancelled_at` NOT NULL, còn lại NULL
- `data_origin IN ('manual', 'synthetic')`

**Indexes**:
- `uq_orders_order_number` — UK trên `order_number`
- `uq_orders_cart_id` — UK trên `cart_id` (1 cart → 1 order)
- `uq_orders_checkout_idempotency_key` — UK trên `checkout_idempotency_key`
- `ix_orders_customer_id_created_at_order_id` — customer history
- `ix_orders_status_created_at_order_id` — admin queue
- `ix_orders_updated_at_order_id` — extraction cursor
- `ix_orders_coupon_id_order_id` — coupon lineage

**State machine**:
```
paid --admin xác nhận--> confirmed --admin hoàn tất--> completed
paid --customer/admin hủy--> cancelled
```
Chỉ order `paid` được hủy. `confirmed` và `completed` không được hủy.

---

## 12. `order_items`

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
| `quantity` | `INT UNSIGNED` | NOT NULL | Số lượng |
| `line_total_vnd` | `BIGINT UNSIGNED` | NOT NULL | `unit_price_vnd × quantity` |
| `created_at` | `DATETIME(6)` | NOT NULL, DEFAULT NOW(6) | |

**Check constraints**:
- `unit_price_vnd >= 0`
- `quantity > 0`
- `line_total_vnd = unit_price_vnd * quantity`

**Unique**: `(order_id, variant_id)` — mỗi variant chỉ có một dòng trong order

**Indexes**:
- `uq_order_items_public_id` — UK trên `public_id`
- `uq_order_items_order_id_variant_id` — composite UK
- `ix_order_items_variant_id_order_item_id` — `(variant_id, order_item_id)`
- `ix_order_items_created_at_order_item_id` — extraction cursor

---

## 13. `payments`

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

## 14. `refunds`

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

## 15. `order_status_history`

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
- `from_status IS NULL AND to_status IN ('paid', 'payment_failed')` — tạo mới
- `from_status = 'paid' AND to_status IN ('confirmed', 'cancelled')`
- `from_status = 'confirmed' AND to_status = 'completed'`

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

## 16. `product_reviews`

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

**Invariant**: Transaction tạo review phải chứng minh order thuộc customer và status `completed`. Review mới tự động `approved`.

---

## Quan hệ tổng quát

```
customers 1───n carts 1───n cart_items n───1 product_variants 1───1 inventory
customers 1───n wishlist_items n───1 products
categories 1───n categories (self-ref)
categories 1───n products 1───n product_variants
carts 1───0..1 orders 1───n order_items
orders 1───1 payments 1───0..1 refunds
orders 1───n order_status_history
orders n───0..1 coupons (nullable FK)
coupons 1───n coupon_redemptions n───1 orders
order_items 1───0..1 product_reviews
customers 1───n product_reviews
```

## Lock ordering

```
customer → cart → cart_item → catalog/variant → coupon → inventory → order children
```

Cancel bắt đầu từ order rồi khóa children theo ID ổn định. Không transaction nào khóa ngược từ coupon/inventory sang order đang tồn tại.

## Reconciliation rules

- `orders.total_vnd = subtotal_vnd - discount_amount_vnd + shipping_fee_vnd`
- Succeeded payment amount = order total
- Succeeded refund amount = payment amount và order cancelled
- Cancelled order phải có history, refund và inventory đã restore
- Active redeemed count theo coupon = `coupons.used_count`
- `archived_at IS NOT NULL` thì entity inactive và đủ actor/reason
- Mọi review phải trỏ đến completed purchased order item
- Review `approved` auto-publish; review `rejected` phải đủ moderator/time/reason
- `inventory.on_hand = opening_on_hand - units của order không cancelled`
