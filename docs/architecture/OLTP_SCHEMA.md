# Logical Schema MySQL OLTP TLCN

## 0. Phạm vi và nguồn quyết định

Tài liệu này mô tả schema OLTP hiện hành của source website sau migration
`0009_reviews_publish_immediately`.
Thiết kế tuân theo `skills/oltp-design/SKILL.md`: grain rõ ràng, chuẩn hóa dữ liệu ghi, snapshot dữ liệu giao dịch, transaction ngắn, khóa theo thứ tự ổn định và invariant được bảo vệ ở tầng thấp nhất phù hợp.

Schema có 17 bảng nghiệp vụ. Pipeline DE được đọc 16 bảng; `customer_credentials` bị loại vì chứa thông tin xác thực.
Không có bảng analytics/star schema trong MySQL ecommerce.

## 1. Quyết định nghiệp vụ

- Checkout yêu cầu đăng nhập và active cart có hàng hợp lệ.
- Add-to-cart không giữ hàng; checkout kiểm tra và trừ `inventory.on_hand` atomically.
- Thanh toán nội bộ thành công ngay khi checkout hợp lệ; không random và không gọi cổng ngoài.
- Order đi theo state machine:

```text
paid --admin xác nhận--> confirmed --admin hoàn tất--> completed

paid --customer/admin hủy--> cancelled
```

- Chỉ order `paid` được hủy. `confirmed` và `completed` không được hủy trong TLCN.
- Hủy order phải hoàn tồn kho, full refund payment, release coupon và ghi history trong cùng transaction.
- Mỗi order tối đa một coupon; coupon và discount được snapshot trên order.
- Mỗi `order_item` tối đa một review; chỉ chủ order `completed` được tạo review.
- Review được hiển thị ngay sau khi customer gửi. Admin chỉ hậu kiểm để ẩn nội dung
  vi phạm hoặc khôi phục review đã ẩn; không có hàng chờ duyệt.
- Xóa product/coupon trên admin là **archive terminal**, không hard delete. Archive
  giữ nguyên khóa và quan hệ lịch sử, buộc `is_active = false`, lưu actor/thời điểm/lý do
  và không cho bật lại.
- `is_active = false` nhưng `archived_at IS NULL` chỉ là tắt tạm thời; trạng thái này
  vẫn có thể bật lại.
- Dữ liệu giao dịch và lịch sử không hard delete.

## 2. Quy ước chung

- PK nội bộ: `BIGINT UNSIGNED` tăng dần.
- Public identifier: `BINARY(16)` UUID cho entity lộ qua API.
- Tiền: số nguyên VND, không dùng FLOAT/DOUBLE.
- Thời gian: UTC, `DATETIME(6)`.
- Bảng mutable có `updated_at` và composite cursor `(updated_at, PK)`.
- Bảng append-only có cursor `(created_at, PK)` hoặc `(transitioned_at, PK)` theo contract.
- FK lịch sử dùng `ON DELETE RESTRICT`.
- Giao dịch write dùng InnoDB `READ COMMITTED`, khóa row bằng `SELECT ... FOR UPDATE` khi quyết định dựa trên dữ liệu mutable.
- Không giữ transaction mở khi gọi dịch vụ ngoài.

## 3. Quan hệ tổng quát

```text
customers 1--1 customer_credentials
customers 1--n carts 1--n cart_items n--1 product_variants
customers 1--n wishlist_items n--1 products
categories 1--n categories
categories 1--n products 1--n product_variants 1--1 inventory
carts 1--0..1 orders 1--n order_items
orders 1--1 payments 1--0..1 refunds
orders 1--n order_status_history
coupons 1--n orders
coupons 1--n coupon_redemptions n--1 orders
order_items 1--0..1 product_reviews
customers 1--n product_reviews
```

## 4. Catalogue bảng và grain

### 4.1. Chiến lược định danh

- PK/FK vật lý trong OLTP dùng `BIGINT UNSIGNED` surrogate key để giữ
  index nhỏ, join nhanh và phù hợp import hàng triệu dòng.
- Thực thể đi qua API dùng `public_id BINARY(16)` chứa UUID; API không
  để lộ surrogate key nội bộ.
- Generator dùng UUIDv5 deterministic cho `public_id`,
  `logical_identity`, `generation_run_id` và các khóa
  kỹ thuật/idempotency.
- `order_number`, SKU, slug và coupon code là business key có ý nghĩa
  hiển thị, nên giữ định dạng nghiệp vụ thay vì biến thành UUID.
- Trong SQL export, UUID được biểu diễn bằng `UUID_TO_BIN('<uuid>')`;
  Lakehouse chuẩn hóa lại thành chuỗi UUID canonical ở Silver nếu cần.

### 4.2. Danh mục bảng

| Nhóm | Bảng | Grain | Tính chất |
|---|---|---|---|
| Customer | `customers` | Một customer | Mutable/anonymizable |
| Auth | `customer_credentials` | Một credential/customer | Mutable, không extract |
| Catalog | `categories` | Một category | Mutable/inactive |
| Catalog | `products` | Một product | Mutable/inactive/archive terminal |
| Catalog | `product_variants` | Một tổ hợp size-color/product | Mutable/inactive |
| Inventory | `inventory` | Một balance/variant | Mutable, khóa khi checkout/cancel |
| Cart | `carts` | Một chu kỳ cart/customer | Mutable lifecycle |
| Cart | `cart_items` | Một variant/cart | Mutable/logical removal |
| Wishlist | `wishlist_items` | Một product từng wishlist/customer | Mutable presence |
| Promotion | `coupons` | Một coupon code | Mutable configuration/counter/archive terminal |
| Order | `orders` | Một kết quả checkout/cart | Mutable state, snapshot amount |
| Order | `order_items` | Một variant line/order | Append-only snapshot |
| Payment | `payments` | Một payment/order | Append-only trong TLCN |
| Promotion | `coupon_redemptions` | Một redemption/order | Mutable redeemed/released |
| Refund | `refunds` | Một full refund/payment | Append-only trong TLCN |
| History | `order_status_history` | Một transition/order | Append-only |
| Review | `product_reviews` | Một review/order_item | Mutable current visibility state |

## 5. Thiết kế theo domain

### 5.1. Customer và credential

#### `customers`

Mục đích: identity nghiệp vụ, profile, role và trạng thái account.

Cột chính: `customer_id` PK, `public_id` UK, `email_normalized` UK, `full_name`, `phone`, `role`, `status`, `pii_anonymized_at`, `data_origin`, `generation_run_id`, `created_at`, `updated_at`.

Invariant: role/status thuộc tập cho phép; anonymize không xóa PK/FK. Index phục vụ login lookup, customer list và incremental extraction.

#### `customer_credentials`

Mục đích: password hash cho đúng một customer.

Cột chính: `customer_id` PK/FK, `password_hash`, `password_changed_at`, timestamps.

Invariant: 1:1 với customer. Không cấp quyền cho DE reader và không đưa vào lakehouse.

### 5.2. Catalog và inventory

#### `categories`

Cột chính: `category_id` PK, `public_id` UK, `parent_category_id` FK self-reference, `code` UK, `slug` UK, `name`, `is_active`, timestamps.

Invariant: product chỉ thuộc category lá do application transaction kiểm tra; không tạo chu trình hierarchy.

#### `products`

Cột chính: `product_id` PK, `public_id` UK, `category_id` FK, `slug` UK, `name`,
`description`, `image_url`, `is_active`, `archived_at`,
`archived_by_customer_id` FK, `archive_reason`, timestamps.

Invariant: thông tin chung ở product; size/color/SKU/giá ở variant. Ba archive field
cùng null hoặc cùng có giá trị; archive buộc inactive. FK actor dùng `ON DELETE RESTRICT`
để giữ audit. Archive không xóa variant, wishlist hay order item; các endpoint bán hàng
loại product archive bằng trạng thái của parent.

#### `product_variants`

Cột chính: `variant_id` PK, `public_id` UK, `product_id` FK, `sku` UK, `size_code`, `color_code`, `price_vnd`, `is_active`, timestamps.

Invariant: unique `(product_id, size_code, color_code)` ngăn trùng tổ hợp; `price_vnd >= 0`.

#### `inventory`

Cột chính: `variant_id` PK/FK, `opening_on_hand`, `on_hand`, `version`, `updated_at`.

Invariant: `0 <= on_hand <= opening_on_hand`; TLCN không có reservation/backorder. `version` tăng khi checkout hoặc cancel để phát hiện thay đổi và hỗ trợ extraction.

### 5.3. Cart và wishlist

#### `carts`

Cột chính: `cart_id` PK, `public_id` UK, `customer_id` FK, `status`, `last_activity_at`, `checked_out_at`, `abandoned_at`, timestamps.

Invariant: một customer tối đa một cart `active`; cart đã checkout/abandoned không tái sử dụng. Unique arbiter thực thi active-cart ownership theo mô hình hiện hành.

#### `cart_items`

Cột chính: `cart_item_id` PK, `cart_id` FK, `variant_id` FK, `quantity`, `is_present`, `removed_at`, timestamps.

Invariant: unique `(cart_id, variant_id)`; quantity dương; logical removal giữ lịch sử. Add/update cart không thay đổi inventory.

#### `wishlist_items`

Cột chính: `wishlist_item_id` PK, `customer_id` FK, `product_id` FK, `is_present`, `added_at`, `removed_at`, timestamps.

Invariant: unique `(customer_id, product_id)`. “Một wishlist/customer” nghĩa là một tập nhiều item, không phải chỉ một sản phẩm.

### 5.4. Coupon

#### `coupons`

Mục đích: cấu hình coupon đơn giản và counter sử dụng hiện hành.

Cột:

- `coupon_id` PK, `public_id` UK, `code_normalized` business key UK;
- `discount_type`: `percentage` hoặc `fixed_amount`;
- `discount_value`: 1..100 với percentage, >0 VND với fixed amount;
- `minimum_subtotal_vnd`;
- `starts_at`, `ends_at`, `is_active`;
- `total_usage_limit`, `per_customer_usage_limit` nullable;
- `archived_at`, `archived_by_customer_id` FK, `archive_reason`;
- `used_count`, `created_at`, `updated_at`.

Invariant: `starts_at < ends_at`; limit nếu có phải dương; `used_count <= total_usage_limit`.
Ba archive field cùng null hoặc cùng có giá trị; archive buộc inactive và actor dùng
`ON DELETE RESTRICT`. Index `(updated_at, coupon_id)` phục vụ incremental extraction.

Concurrency: checkout khóa row coupon trước khi kiểm tra `used_count`; đếm redemption customer trong cùng transaction; tăng counter và insert redemption atomically. Cancel khóa coupon và redemption, release đúng một lần rồi giảm counter.

#### `coupon_redemptions`

Mục đích: chứng minh một order đã chiếm usage coupon và cho phép release khi hủy.

Cột: `coupon_redemption_id` PK, `coupon_id` FK, `order_id` FK/UK, `customer_id` FK, `status` (`redeemed`, `released`), `redeemed_at`, `released_at`, timestamps.

Invariant: một order tối đa một redemption; status/timestamp nhất quán. Index `(coupon_id, customer_id, status)` phục vụ per-customer limit; `(updated_at, coupon_redemption_id)` phục vụ extraction.

### 5.5. Order, payment, refund và history

#### `orders`

Cột identity/ownership: `order_id` PK, `order_number` UK, `cart_id` FK/UK, `customer_id` FK, `checkout_idempotency_key` UK.

Cột snapshot tiền: `currency_code`, `subtotal_vnd`, `discount_amount_vnd`, `shipping_fee_vnd`, `total_vnd`.

Cột coupon snapshot: `coupon_id` FK nullable, `coupon_code_snapshot`, `coupon_type_snapshot`, `coupon_value_snapshot`.

Cột giao hàng snapshot: `receiver_name`, `receiver_phone`, `shipping_address_text`.

Cột lifecycle: `status`, `paid_at`, `confirmed_at`, `completed_at`, `cancelled_at`, timestamps.

Invariant:

- `currency_code = 'VND'`;
- `discount_amount_vnd <= subtotal_vnd`;
- `total_vnd = subtotal_vnd - discount_amount_vnd + shipping_fee_vnd`;
- không coupon thì toàn bộ coupon snapshot null và discount bằng 0;
- có coupon thì snapshot đầy đủ và discount > 0;
- timestamp phải khớp trạng thái;
- một cart chỉ tạo tối đa một order;
- checkout replay dựa trên unique `checkout_idempotency_key`.

Indexes: customer history `(customer_id, created_at, order_id)`, admin queue `(status, created_at, order_id)`, extraction `(updated_at, order_id)`, coupon lineage `(coupon_id, order_id)`.

#### `order_items`

Cột chính: `order_item_id` PK, `public_id` UK, `order_id` FK, `variant_id` FK; snapshot product/category/SKU/size/color; `unit_price_vnd`, `quantity`, `line_total_vnd`, `created_at`.

Invariant: unique `(order_id, variant_id)`; quantity dương; `line_total_vnd = unit_price_vnd * quantity`. Master data thay đổi không làm đổi lịch sử order.

#### `payments`

Cột: `payment_id` PK, `payment_reference` UK, `order_id` FK/UK, `payment_idempotency_key` UK, `status`, `currency_code`, `amount_vnd`, `failure_code`, `attempted_at`, `created_at`.

Invariant TLCN: một payment/order; checkout hiện hành luôn ghi `succeeded`, không random; amount/currency khớp order. Giá trị `failed` chỉ được giữ trong constraint để tương thích dữ liệu lịch sử trước migration.

#### `refunds`

Mục đích: full refund khi hủy order đã paid; không phải return hàng hóa.

Cột: `refund_id` PK, `public_id` UK, `payment_id` FK/UK, `refund_idempotency_key` UK, `status`, `currency_code`, `amount_vnd`, `reason`, `requested_by_customer_id` FK, `created_at`, `completed_at`.

Invariant: một payment tối đa một refund; VND; full refund amount bằng payment amount; succeeded phải có `completed_at`. Unique payment/idempotency keys là arbiter chống refund lặp.

#### `order_status_history`

Cột: `order_status_history_id` PK, `order_id` FK, `from_status`, `to_status`, `transition_source`, `reason`, `transition_idempotency_key` UK, `transitioned_at`, `created_at`.

Invariant cho dữ liệu mới: initial `paid`, `paid -> confirmed|cancelled`, `confirmed -> completed`; cancel bắt buộc reason; unique `(order_id, to_status)` ngăn transition đích lặp. Không update/delete history.

### 5.6. Review

#### `product_reviews`

Mục đích: review có verified purchase, tự động hiển thị và hậu kiểm đơn giản.

Cột: `review_id` PK, `public_id` UK, `order_item_id` FK/UK, `customer_id` FK, `product_id` FK, `rating`, `content`, `status`, `moderation_reason`, `moderated_by_customer_id` FK, `moderated_at`, timestamps.

Invariant:

- rating 1..5;
- một `order_item` tối đa một review;
- transaction tạo review phải chứng minh order thuộc customer và status `completed`;
- status chỉ gồm `approved` (đang hiển thị) và `rejected` (đã ẩn);
- review mới `approved` có ba moderation field null;
- review bị ẩn phải có moderator/time và lý do tối thiểu ba ký tự; review được khôi
  phục có moderator/time nhưng `moderation_reason` null;
- endpoint public chỉ đọc `approved`.

Indexes: `(product_id, status, created_at, review_id)` cho trang sản phẩm; `(customer_id, created_at, review_id)` cho lịch sử; `(updated_at, review_id)` cho extraction.

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
- Archive: khóa coupon; lần đầu set inactive và đủ ba archive field trong cùng
  transaction. Request lặp là no-op và giữ audit đầu tiên.
- Không sửa snapshot trên order cũ.

### TX-08 — Admin archive product

- Khóa product; lần đầu set inactive và đủ ba archive field trong cùng transaction.
- Request lặp là no-op và giữ audit đầu tiên; product archive không thể tái kích hoạt.
- Không cascade sang variant, wishlist hoặc order item để giữ tham chiếu và snapshot
  lịch sử.

## 7. Thứ tự khóa và xử lý race

Thứ tự chuẩn khi transaction chạm nhiều aggregate:

```text
customer -> cart -> cart_item -> catalog/variant -> coupon -> inventory -> order children
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
| Review hai request | UK `product_reviews.order_item_id` |
| Hai admin đổi visibility review | row lock + current-state check; request cùng state idempotent |
| Transition lặp | UK history idempotency và `(order_id, to_status)` |
| Hai admin cùng archive | row lock + archive idempotent, giữ audit đầu tiên |

Deadlock vẫn có thể xảy ra; application chỉ retry transaction khi lỗi được xác định là deadlock/serialization và request idempotent.

## 8. OLAP readiness và reconciliation

16 source table được extract; credential bị cấm. Bảng mới dùng cursor:

| Bảng | Cursor | Mutability |
|---|---|---|
| `products` | `(updated_at, product_id)` | Mutable/current archive state |
| `coupons` | `(updated_at, coupon_id)` | Mutable |
| `coupon_redemptions` | `(updated_at, coupon_redemption_id)` | Mutable |
| `refunds` | `(created_at, refund_id)` | Append-only |
| `product_reviews` | `(updated_at, review_id)` | Mutable current visibility/moderation |

Reconciliation cốt lõi:

- `orders.total_vnd = subtotal_vnd - discount_amount_vnd + shipping_fee_vnd`;
- succeeded payment amount = order total;
- succeeded refund amount = payment amount và order cancelled;
- cancelled order phải có history, refund và inventory đã restore;
- active redeemed count theo coupon = `coupons.used_count`;
- `archived_at IS NOT NULL` thì entity inactive và đủ actor/reason; order/order item
  lịch sử vẫn join được đến product/coupon archive;
- mọi review phải trỏ đến completed purchased order item;
- review `approved` auto-publish có thể không có moderator; review `rejected` phải đủ
  moderator/time/reason;
- inventory: `opening_on_hand - units của order không cancelled = on_hand` trong phạm vi không adjustment.

PII ở customer/order shipping snapshot phải được phân loại và mask/anonymize ở downstream. OLTP là source of truth; lakehouse chỉ dẫn xuất.

## 9. Nâng cấp ngoài TLCN

Nếu phát triển thành KLTN có thể bổ sung external payment attempts, transactional outbox/CDC, inventory ledger/reservation, shipment, partial refund/return và event clickstream. Các phần này không được giả định là đã có trong schema TLCN hiện tại.
