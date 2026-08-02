# Kế hoạch Source Website TLCN

## 0. Trạng thái tài liệu

Tài liệu này mô tả source website phục vụ TLCN theo [`scope.md`](scope.md) và [`../architecture/oltp-schema.md`](../architecture/oltp-schema.md).

Quyết định hiện hành:

- Website chỉ tạo dữ liệu nghiệp vụ trong MySQL OLTP.
- Search/filter vẫn là chức năng web nhưng search query không được lưu cho phân tích TLCN.

---

## 1. Mục tiêu và giới hạn

### 1.1. Mục tiêu chức năng

1. Customer đăng ký, đăng nhập và đăng xuất.
2. Public user xem category, product và variant.
3. Public user search/filter/sort catalog.
4. Customer quản lý wishlist mặc định chứa nhiều product.
5. Customer quản lý active cart.
6. Customer checkout với thông tin giao hàng.
7. Checkout hợp lệ có thể áp dụng một coupon, tạo order `paid`, payment `succeeded` và giảm inventory atomically.
8. Customer xem order, hủy order còn `paid` và review item của order `completed`.
9. Admin quản lý catalog, inventory, coupon, review moderation, customer status và xác nhận/hoàn tất/hủy order.
10. Hủy order `paid` hoàn inventory, full refund và release coupon trong một transaction.
16. Website tạo source rows đủ cho batch DE, dashboard và ML mua lại dựa trên OLTP.

### 1.2. Mục tiêu kỹ thuật

- MySQL là system of record.
- Transaction ngắn, không gọi external service.
- Checkout idempotent và không oversell.
- Không hard delete transaction history.
- Mutable source có stable key và `updated_at`.
- Amount dùng integer VND.
- PII được giới hạn và không extract credential.
- Source contract phù hợp initial/incremental batch extraction.

### 1.3. Ngoài phạm vi

- Anonymous cart, cart merge và guest checkout.
- Promotion engine tổng quát, stacking coupon và tax module.
- External payment, partial refund, return và shipment.
- Reservation, restock, multi-warehouse.
- Recommendation/ML inference trên storefront.
- Redis, Kafka, Elasticsearch và microservices.

---

## 2. Definition of Done

Source website hoàn thành khi:

- migration khớp logical schema 17 bảng;
- các page/API bắt buộc hoạt động;
- checkout valid/rejected, idempotency và last-item concurrency pass;
- profile `core` chỉ cần MySQL, Ecommerce API và Storefront;
- generator tạo OLTP master/history/repurchase data reproducibly;
- MySQL reader chỉ được cấp quyền trên 16 bảng analytical source;
- source catalogue/data dictionary đủ để bàn giao batch extraction;
- web không phụ thuộc Airflow, Spark, MinIO hoặc analytics database.

---

## 3. Tech stack

| Khối | Công nghệ |
|---|---|
| Frontend | Next.js 15, React, TypeScript |
| Backend | FastAPI, SQLAlchemy 2, Pydantic |
| Database | MySQL 8.4, InnoDB |
| Migration | Alembic |
| Auth | JWT trong HttpOnly cookie + CSRF double-submit |
| Test | Pytest, Next production build, MySQL integration |
| Dependency | npm lock + uv workspace/lock |
| Runtime | Docker Compose |

---

## 4. Kiến trúc source application

```text
Browser
  ↓ HTTP/JSON
Next.js Storefront
  ↓ HTTP/JSON + cookie/CSRF
FastAPI Ecommerce API
  ↓ short transaction
MySQL ecommerce
  ↓ read-only extraction
TLCN Batch Pipeline
```

Ranh giới bắt buộc:

- Storefront không truy cập MySQL.
- API không ghi Lakehouse/analytics database.
- Pipeline không ghi ngược OLTP.
- Dashboard không đọc primary OLTP.
- Không có browser→Collector path trong TLCN.

### 4.1. Backend layering

```text
router
→ auth/dependency/schema validation
→ application service
→ SQLAlchemy transaction/repository logic
→ MySQL
```

Application service sở hữu transaction boundary. Repository/query helper không tự commit.

### 4.2. Frontend layering

```text
app routes/components
→ typed API client
→ Ecommerce API
```

Không có analytics SDK hoặc event emitter trong runtime TLCN.

---

## 5. Module và table ownership

| Module | Đọc | Ghi | Không được làm |
|---|---|---|---|
| Auth | customer/credential | customer/credential | Trả password hash |
| Catalog | category/product/variant/inventory | Admin catalog | Tạo analytical search history |
| Wishlist | customer/product/wishlist | wishlist | Hard delete wishlist history |
| Cart | cart/item/catalog/inventory | cart/item | Reserve inventory |
| Checkout | customer/cart/catalog/inventory | order/item/payment/history/cart/inventory | Random payment, external call |
| Orders | order graph | Không, trừ completion service | Recompute historical price |
| Admin | domain tables theo role | Bounded mutations | Xóa transaction history |
| Generator | source contract | Synthetic OLTP rows | Sinh browser events trong TLCN |

---

## 6. Page map

| Route | Auth | Chức năng |
|---|---:|---|
| `/` | Không | Landing tối giản |
| `/register` | Không | Tạo account |
| `/login` | Không | Đăng nhập |
| `/products` | Không | Search/filter/sort catalog |
| `/products/[slug]` | Không | Product detail + variant |
| `/wishlist` | Có | Current wishlist |
| `/cart` | Có | Cart mutation |
| `/checkout` | Có | Shipping info + order summary |
| `/checkout/result/[orderNumber]` | Có | Paid result |
| `/orders` | Có | Order history |
| `/orders/[orderNumber]` | Có | Order detail/history |
| `/admin` | Admin | Overview |
| `/admin/products` | Admin | Product/variant management |
| `/admin/orders` | Admin | Order list/detail/completion |
| `/admin/customers` | Admin | Customer status |

### 6.1. Catalog

- Search bounded `LIKE` trên name/description.
- Filter category, size, color, price và in-stock.
- Sort newest/price.
- Keyset cursor, không offset lớn.
- Một matching variant phải thỏa đồng thời variant-level filter.
- Search/filter không ghi table history hoặc event trong TLCN.

### 6.2. Wishlist

- Một implicit wishlist/customer, chứa nhiều product.
- Unique `(customer_id, product_id)`.
- PUT/DELETE biểu diễn desired state.
- Remove logical bằng `is_present=false`, re-add cập nhật row cũ.
- Wishlist state là nguồn OLTP có thể extract; không có full click history.

### 6.3. Cart

- Tối đa một active cart/customer.
- Update dùng absolute quantity.
- Remove là logical removal.
- Add-to-cart không reserve/decrement stock.
- Cart total chỉ là preview; checkout tính lại.
- Checked-out cart không tái sử dụng.

### 6.4. Checkout

- Yêu cầu đăng nhập.
- Form chỉ có receiver name, phone và address.
- Không có payment scenario hoặc random outcome.
- Client tạo `Idempotency-Key` và giữ cùng key khi retry cùng logical request.
- Server revalidate toàn bộ cart/catalog/inventory.
- Checkout rejected giữ cart active.
- Checkout valid trả order `paid` và payment `succeeded`.

### 6.5. Order history

- Chỉ trả order của authenticated customer.
- Dùng snapshot tại `orders`/`order_items`.
- Không tính lại historical amount từ catalog hiện tại.
- History transition append-only.

---

## 7. API conventions

- Prefix `/api/v1`.
- JSON `snake_case`.
- Public UUID/business key trên URL.
- Không nhận internal numeric customer ID từ client.
- Timestamp UTC ISO 8601.
- Amount integer VND.
- Mutation cần CSRF.
- Checkout/internal completion cần idempotency key.
- Domain error có stable `error_code`.
- Structured log không chứa password, token hoặc shipping address.

---

## 8. API catalogue

### Auth

- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/logout`
- `GET /auth/me`

### Catalog

- `GET /categories`
- `GET /catalog/facets`
- `GET /products`
- `GET /products/{slug}`

### Wishlist

- `GET /wishlist`
- `PUT /wishlist/products/{product_public_id}`
- `DELETE /wishlist/products/{product_public_id}`

### Cart

- `GET /cart`
- `PUT /cart/items/{variant_public_id}`
- `DELETE /cart/items/{variant_public_id}`

### Checkout/order

- `POST /checkout`
- `GET /orders`
- `GET /orders/{order_number}`
- internal/admin completion endpoint

### Admin

- overview;
- product/variant CRUD bounded;
- order listing/detail/completion;
- customer listing/status.

### Health

- `/health/live`
- `/health/ready`

Không có event ingestion endpoint trong API TLCN.

---

## 9. Authentication và privacy

- Password hash chỉ nằm trong `customer_credentials`.
- JWT lưu HttpOnly cookie.
- CSRF token kiểm tra cho state-changing request.
- Cookie Secure/SameSite cấu hình theo môi trường.
- Customer ownership kiểm tra server-side.
- Admin role kiểm tra server-side.
- Shipping address chỉ dùng vận hành/order detail, không đưa vào Gold.
- `customer_credentials` không cấp SELECT cho DE reader.

---

## 10. Transaction plan

### TX-WEB-01 — Register

1. Normalize email.
2. Begin `READ COMMITTED`.
3. Insert customer và credential atomically.
4. Unique email xử lý race.
5. Commit rồi mới set auth cookie.

### TX-WEB-02 — Wishlist mutation

1. Lock customer.
2. Resolve active product khi add.
3. Lock `(customer, product)` row nếu tồn tại.
4. Set desired `is_present` state/timestamps.
5. Commit.

### TX-WEB-03 — Cart mutation

1. Lock/find active cart.
2. Lock logical item.
3. Validate active product/variant.
4. Set absolute quantity hoặc logical remove.
5. Update cart timestamp.
6. Commit.

### TX-WEB-04 — Checkout

1. Validate request/idempotency/address.
2. Begin `READ COMMITTED`.
3. Replay committed result nếu cùng idempotency key.
4. Lock customer và active cart.
5. Lock present items theo variant ID.
6. Validate cart không rỗng.
7. Lock category/product/variant theo stable order; validate active.
8. Lock inventory theo variant ID.
9. Validate `on_hand >= quantity` cho mọi line.
10. UI checkout có popup liệt kê coupon đang khả dụng theo subtotal và usage limit; quote/checkout vẫn kiểm tra lại ở server.
11. Nếu có coupon: khóa coupon, kiểm tra window/subtotal/limit và tính discount.
12. Tính snapshots/subtotal/discount/shipping/total từ dữ liệu server.
13. Insert paid order, items, succeeded payment, initial history và coupon redemption.
14. Conditional decrement inventory và tăng version.
15. Close cart.
16. Commit.

Mọi write cùng commit/rollback. Không gọi external API, email hoặc analytics service trong transaction.

### TX-WEB-05 — Confirm/complete order

1. Validate admin auth và idempotency.
2. Lock order.
3. Chỉ cho `paid → confirmed` hoặc `confirmed → completed`.
4. Update order timestamp + insert immutable history.
5. Commit.

### TX-WEB-06 — Cancel paid order

1. Lock order và xác minh customer ownership hoặc admin role.
2. Chỉ cho `paid → cancelled`; replay theo idempotency key.
3. Lock payment, inventory, coupon redemption/coupon theo thứ tự ổn định.
4. Hoàn inventory, insert full refund, release coupon usage.
5. Update order + insert immutable history kèm actor/reason.
6. Commit atomically.

### TX-WEB-07 — Review sau mua

1. Customer chỉ review order item thuộc order `completed` của mình.
2. Unique `order_item_id` bảo đảm tối đa một review/item.
3. Review mới ở `pending`; admin chuyển sang `approved` hoặc `rejected`.
4. Public product page chỉ hiển thị review `approved`.

---

## 11. Inventory và amount

### Inventory

- `opening_on_hand` immutable sau seed.
- `0 <= on_hand <= opening_on_hand`.
- Add-to-cart/wishlist không thay đổi stock.
- Checkout valid là runtime flow duy nhất giảm stock.
- Conditional update ngăn oversell.
- Không restock/adjustment trong TLCN.

Reconciliation:

```text
opening_on_hand - sold units từ succeeded payments = on_hand
```

### Amount

- VND integer, không FLOAT/DOUBLE.
- Unit price lấy từ variant tại checkout.
- Order item snapshot price/name/SKU/size/color.
- Shipping fee flat và free threshold.
- Order total snapshot, không tính lại khi đọc lịch sử.

---

## 12. OLTP data handoff

### 12.1. Analytical source tables

Pipeline đọc 16 bảng:

- customers;
- categories;
- products;
- product_variants;
- carts;
- cart_items;
- wishlist_items;
- orders;
- order_items;
- payments;
- order_status_history;
- inventory;
- coupons;
- coupon_redemptions;
- refunds;
- product_reviews.

Pipeline không đọc `customer_credentials`.

### 12.2. Source contract bắt buộc

Mỗi table phải có:

- owner;
- grain;
- PK/business key;
- mutability;
- cursor `(timestamp, PK)`;
- timestamp semantics;
- logical delete/inactive semantics;
- PII classification;
- extraction columns;
- expected row relationship;
- DQ and reconciliation rules.

### 12.3. Limitation của batch OLTP

Mutable row chỉ cho biết state tại lần extract. Nếu cart/wishlist bị thay đổi nhiều lần giữa hai batch, pipeline có thể chỉ thấy state cuối.

KPI cart/wishlist phải được diễn giải như snapshot trạng thái tại batch cutoff, không phải lịch sử đầy đủ của mọi lần thay đổi.

---

## 13. Generator

Modes TLCN:

- `seed_master`;
- `historical_transactions`;
- `repurchase_history`;


Generator phải:

- deterministic theo seed/anchor time;
- tuân thủ PK/FK/unique/check/state invariant;
- tạo đủ 12 tháng cho ML;
- có small/medium/large-local config;
- gắn `data_origin=synthetic` và generation run ID khi schema hỗ trợ;

---

## 14. Logging

API và web vẫn có operational logging để debug:

- request ID;
- method/normalized route;
- status;
- latency;
- service/version;
- error code;
- sanitized message.

Operational log không được ingest vào Lakehouse, không phải deliverable dữ liệu và không được dùng làm dashboard/ML TLCN.

---

## 15. Testing

### Backend unit

- auth/schema/security;
- money arithmetic;
- pagination/cursor;
- catalog filter semantics;
- wishlist desired-state;
- checkout request không có payment scenario.

### MySQL integration

- register atomic/email race;
- one active cart;
- cart/wishlist logical mutation;
- checkout valid;
- checkout rejected;
- idempotent replay;
- concurrent last-item;
- order completion;
- inventory reconciliation.

### Frontend/build

- auth guard;
- product/search/filter;
- wishlist/cart/checkout/order/admin;
- production build;

### DE handoff

- reader không đọc credential;
- cursor columns/index tồn tại;
- source count/amount reconciliation query chạy được;
- clean migration/seed/generator.

---

## 16. Runtime profiles

| Profile | Dịch vụ |
|---|---|
| `core` | MySQL ecommerce, Ecommerce API, Storefront |
| `tools` | OLTP data generator |
| `batch` | MinIO, Spark, Airflow, PostgreSQL metadata |
| `bi` | MySQL analytics, Superset, PostgreSQL metadata |

Startup TLCN:

```text
core
→ tools nếu cần synthetic data
→ batch
→ bi
```


---

## 17. Roadmap web

### Tuần 1

- schema/migration/seed;
- auth/catalog/search/filter;
- health/logging/security.

### Tuần 2

- wishlist/cart;
- checkout/inventory/idempotency;
- order/admin;
- MySQL integration/concurrency tests.

### Tuần 3

- OLTP generator;
- DE read-only grants;
- source catalogue/data dictionary;
- extraction cursor/reconciliation queries;
- clean Docker/runbook handoff.


---

## 18. Deliverables web

- storefront;
- Ecommerce API;
- MySQL migration/seed;
- admin console tối thiểu;
- generator OLTP;
- OpenAPI;
- source data dictionary;
- source cursor/PII contract;
- integration/concurrency tests;
- reconciliation queries;
- setup/runbook.


---

## 19. Acceptance checklist

- [ ] Auth/catalog/search/filter chạy đúng.
- [ ] Wishlist chứa nhiều product/customer.
- [ ] Cart active và logical item đúng.
- [ ] Checkout không random, không scenario.
- [ ] Checkout valid commit atomic.
- [ ] Checkout rejected không tạo order/payment.
- [ ] Concurrent checkout không oversell.
- [ ] Order snapshot/history đúng.
- [ ] Admin role và bounded operations đúng.
- [ ] 13-table migration từ clean DB.
- [ ] Generator OLTP reproducible.
- [ ] DE reader không đọc credentials.
- [ ] Source contract bàn giao đủ cho Bronze/Silver/Gold.

---
