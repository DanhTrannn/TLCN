# KẾ HOẠCH TRIỂN KHAI SOURCE WEBSITE CHO TLCN

## 0. Thông tin tài liệu

Tài liệu này lập kế hoạch triển khai source website dựa trên:

- `remake.md`: phạm vi TLCN, tech stack, event/log và acceptance tổng thể;
- `schema.md`: logical schema 12 bảng, invariant, transaction, concurrency và CDC-readiness.

Đây là implementation plan, chưa phải DDL, migration hoặc source code. Khi có xung đột, phải cập nhật `remake.md`/`schema.md` trước rồi mới thay đổi contract tại đây.

```text
Browser → Next.js storefront → FastAPI ecommerce API → MySQL ecommerce
       └────────────────────→ FastAPI Event Collector → closed JSONL
```

Website tạo dữ liệu cho pipeline DE và bài toán repurchase ML. Website không chạy Spark, dashboard hoặc model inference.

---

## 1. Mục tiêu và giới hạn

### 1.1. Mục tiêu chức năng

1. Customer đăng ký và đăng nhập.
2. Người dùng chưa đăng nhập xem category, product và variant.
3. Customer đã đăng nhập xem, thêm, cập nhật và xóa item khỏi cart.
4. Customer checkout với địa chỉ nhập trực tiếp.
5. Local payment simulator trả `succeeded` hoặc `failed`.
6. Success checkout tạo paid order và giảm inventory atomically.
7. Failed checkout tạo payment-failed order nhưng không đổi inventory.
8. Customer xem order history và order detail.
9. Internal endpoint/generator chuyển paid order sang completed.
10. Browser phát bốn clickstream event sang Collector.
11. API/Collector tạo structured access/application log.
12. Generator tạo dữ liệu lịch sử tái lập cho DE/ML.

### 1.2. Mục tiêu kỹ thuật

- MySQL là system of record.
- Transaction ngắn, không chứa external API call.
- Checkout idempotent và xử lý được unknown commit.
- Hai checkout tranh last item không làm `on_hand` âm.
- Không hard delete transaction history.
- Mutable source có stable key, `updated_at` và delete semantics rõ.
- Event/log có version, event time, received time và dedup identity.
- Cùng generator seed/config tạo cùng logical dataset.
- Web hoàn thành và freeze cuối tuần 3 để ưu tiên DE.

### 1.3. Ngoài phạm vi

- UI thương mại hoàn chỉnh, animation hoặc frontend polish phức tạp.
- Anonymous cart, cart merge, guest checkout.
- Full-text search.
- Coupon, promotion, tax.
- Reservation, restock, inventory adjustment, nhiều warehouse.
- External payment, pending payment, nhiều payment attempt.
- Refund, return, review, shipment.
- Admin portal đầy đủ.
- Recommendation hoặc ML inference trên storefront.
- Redis, Kafka, Elasticsearch, microservice, distributed transaction.

---

## 2. Definition of Done

Source website hoàn thành khi:

- mọi page/endpoint bắt buộc hoạt động;
- migration khớp 12-table contract;
- success/failed checkout pass integration test;
- last-item concurrency và idempotency pass trên MySQL thật;
- bốn clickstream event được ghi thành closed JSONL đúng contract;
- log không chứa PII/secret;
- generator tạo master, transaction, behavior và repurchase history;
- source row có stable ID, UTC timestamp và `data_origin`;
- Docker `core` profile ổn định từ clean volumes;
- source catalogue/data dictionary đủ để bàn giao ingestion.

---

## 3. Tech stack web

| Thành phần | Công nghệ | Quyết định |
|---|---|---|
| Frontend | Node.js 22 LTS, Next.js 15, TypeScript | App Router, pin version |
| Styling | Tailwind CSS | Không thêm UI framework nếu chưa cần |
| Backend | Python 3.11, FastAPI, Pydantic 2 | REST API |
| ORM/migration | SQLAlchemy 2, Alembic | Explicit Unit of Work |
| Driver | PyMySQL | Pin phiên bản chính xác trong dependency lock |
| OLTP | MySQL 8.4 LTS, InnoDB | `READ COMMITTED` cho nghiệp vụ |
| Password | Argon2id library chuẩn | Không tự viết hashing |
| Auth | Short-lived JWT trong HttpOnly cookie | Không tạo session table |
| Collector | FastAPI, Pydantic, rotating JSONL | Atomic close/rename |
| Test | pytest, Vitest, Playwright tối thiểu | MySQL thật cho integration |
| Packaging | Docker Compose v2, Makefile | `core` profile |

Không thêm state-management library giai đoạn đầu. Ưu tiên native `fetch`, React state/context nhỏ và typed API client.

---

## 4. Kiến trúc source application

```text
Browser
├── Next.js storefront
│   ├── public catalog
│   ├── authenticated cart/checkout/orders
│   └── clickstream client
├── Ecommerce API
│   ├── auth
│   ├── catalog
│   ├── cart
│   ├── checkout/payment
│   ├── order
│   └── internal completion
├── MySQL ecommerce — 12 OLTP tables
└── Event Collector
    ├── validation
    ├── collector timestamp
    ├── rotating JSONL writer
    └── atomic close
```

### 4.1. Backend layering

```text
FastAPI route
→ Pydantic schema
→ application service
→ repository/query object
→ SQLAlchemy Unit of Work
→ MySQL
```

Rules:

- Route không tự commit nhiều lần.
- Repository không điều phối business transaction.
- Application service sở hữu transaction boundary.
- Client price/amount không phải nguồn chính thức.
- Transaction service không gọi Collector/external service.
- Request ID xuyên suốt route, service và log.

### 4.2. Frontend layering

```text
App Router page/layout
→ feature component/form
→ typed API client
→ ecommerce API

event hook → event client → Collector
```

- Public/authenticated page tách rõ.
- Không lưu JWT trong `localStorage`.
- Không giữ authoritative total chỉ ở frontend.
- Event failure không chặn business UI.

---

## 5. Module và table ownership

| Module | Read | Write | Cấm |
|---|---|---|---|
| Auth | customers, credentials | customers, credentials | Log/extract password hash |
| Catalog | categories, products, variants, inventory | Seed only | Public catalog mutation |
| Cart | customers, carts, cart items, variants | carts, cart items | Reserve stock |
| Checkout | cart graph, catalog, inventory | orders, items, payment, history, cart, inventory | External call trong transaction |
| Order query | orders, items, payments, history | Không | Cross-customer access |
| Completion | orders, history | order state + history | Transition ngoài `paid → completed` |
| Collector | Không đọc OLTP | JSONL | Làm source of truth order/payment |
| Generator | Tùy mode | Seed/shared service/API | Bypass invariant của normal rows |

Runtime không có restock/adjustment endpoint. `opening_on_hand` chỉ tạo lúc seed và runtime role không được sửa.

---

## 6. Page map và UX

| Route | Auth | Chức năng |
|---|---:|---|
| `/register` | Không | Tạo account |
| `/login` | Không | Đăng nhập |
| `/products` | Không | Listing, category filter, cursor/load-more |
| `/products/[slug]` | Không | Product detail + variants |
| `/cart` | Có | Xem/update/remove cart item |
| `/checkout` | Có | Address, summary, demo payment |
| `/checkout/result/[orderNumber]` | Có | Paid/failed result |
| `/orders` | Có | Order history |
| `/orders/[orderNumber]` | Có | Order detail + lifecycle |

### 6.1. Navigation/auth guard

- Header có Products, Cart, Orders, Login/Logout.
- Unauthenticated add-to-cart chuyển login với safe return path.
- Return path phải thuộc allowlist nội bộ.
- Không có anonymous cart nên không giữ item trước login.

### 6.2. Catalog

- Filter một category code/lần.
- Pagination bằng cursor, không offset lớn.
- Chỉ hiển thị active category/product/variant.
- Product detail hiển thị size, color, price và stock indicator.
- Current stock chỉ tham khảo; checkout revalidate.
- `view_product` phát sau detail load thành công.

### 6.3. Cart

- Update là set absolute quantity, không blind increment.
- Remove là logical removal.
- Cart total chỉ là preview; checkout tính lại.
- Checked-out cart không tái sử dụng.

### 6.4. Checkout

- Form: receiver name, phone, address text.
- Submit tạo `Idempotency-Key` và giữ cùng key khi retry logical request.
- Không dựa vào disabled button để chống duplicate.
- Timeout retry cùng key hoặc query order result.
- Out-of-stock giữ cart active.
- Payment failure đóng cart; customer tạo cart mới nếu thử lại.

### 6.5. Order history

- Chỉ trả order của authenticated customer.
- Keyset pagination theo created time + stable key.
- Dùng order/order-item snapshot; không tính lại từ catalog.

---

## 7. API conventions

- Base path `/api/v1`.
- JSON dùng `snake_case`.
- Timestamp ISO-8601 UTC.
- Money integer VND.
- Public API không trả internal PK.
- Pagination trả opaque `next_cursor`.
- Unknown write field bị từ chối.
- Không serialize ORM object trực tiếp.

Error envelope:

```json
{
  "error": {
    "code": "OUT_OF_STOCK",
    "message": "Không đủ tồn kho.",
    "request_id": "...",
    "details": {}
  }
}
```

Error code cốt lõi:

- `VALIDATION_ERROR`, `AUTH_REQUIRED`, `INVALID_CREDENTIALS`;
- `EMAIL_ALREADY_EXISTS`, `FORBIDDEN`, `RESOURCE_NOT_FOUND`;
- `CART_NOT_ACTIVE`, `EMPTY_CART`, `VARIANT_NOT_SELLABLE`;
- `OUT_OF_STOCK`, `IDEMPOTENCY_CONFLICT`;
- `INVALID_STATE_TRANSITION`, `CONCURRENCY_RETRY_EXHAUSTED`;
- `INTERNAL_ERROR`.

Request identity:

- API tạo `request_id` nếu client không gửi ID hợp lệ.
- Checkout/completion dùng `Idempotency-Key` tách khỏi request ID.
- Cùng key nhưng khác customer/cart/payload trả `409 IDEMPOTENCY_CONFLICT`.

---

## 8. API catalogue

### 8.1. Auth

| Method | Path | Auth | Mục đích |
|---|---|---:|---|
| POST | `/api/v1/auth/register` | Không | Tạo customer + credential |
| POST | `/api/v1/auth/login` | Không | Set auth/CSRF cookie |
| POST | `/api/v1/auth/logout` | Có | Clear cookie |
| GET | `/api/v1/auth/me` | Có | Current customer tối thiểu |

Register nhận `display_name`, `email`, `password`; server gán origin/status/timestamps.

### 8.2. Catalog

| Method | Path | Auth | Mục đích |
|---|---|---:|---|
| GET | `/api/v1/categories` | Không | Category active |
| GET | `/api/v1/products` | Không | Listing theo category + cursor |
| GET | `/api/v1/products/{slug}` | Không | Product + active variants |

### 8.3. Cart

| Method | Path | Auth | Mục đích |
|---|---|---:|---|
| GET | `/api/v1/cart` | Có | Đọc active cart, không tạo row |
| PUT | `/api/v1/cart/items/{variant_public_id}` | Có | Set quantity/re-add |
| DELETE | `/api/v1/cart/items/{variant_public_id}` | Có | Logical remove |

PUT body: `{ "quantity": 2 }`.

- Backend tạo active cart lazily ở mutation đầu.
- Quantity là integer dương trong configured limit.
- Validate customer/product/variant active.
- Không reserve stock.

### 8.4. Checkout

| Method | Path | Auth | Idempotency | Mục đích |
|---|---|---:|---:|---|
| POST | `/api/v1/checkout` | Có | Bắt buộc | Checkout active cart |

Input: receiver name, phone, address; optional forced outcome chỉ khi `DEMO_MODE=true`.

Response: order number/status, payment reference/status, subtotal, shipping fee, total, currency, created time.

Client không gửi authoritative customer/cart ID, unit price hoặc total.

### 8.5. Order

| Method | Path | Auth | Mục đích |
|---|---|---:|---|
| GET | `/api/v1/orders` | Có | History theo cursor |
| GET | `/api/v1/orders/{order_number}` | Có | Order aggregate detail |

Backend luôn filter owner từ auth token.

### 8.6. Internal completion

| Method | Path | Auth | Idempotency |
|---|---|---:|---:|
| POST | `/internal/v1/orders/{order_number}/complete` | Internal secret | Bắt buộc |

- Không xuất hiện trên storefront.
- Chỉ `paid → completed`.
- Duplicate trả committed result, không nhân history.

### 8.7. Health

| Method | Path | Mục đích |
|---|---|---|
| GET | `/health/live` | Process sống |
| GET | `/health/ready` | Dependency thiết yếu sẵn sàng |

---

## 9. Authentication và authorization

### 9.1. Credential/token

- Normalize email trước lookup/insert.
- Hash password bằng Argon2id.
- JWT chứa public customer ID và expiry tối thiểu.
- JWT lưu HttpOnly cookie; `Secure` khi HTTPS, `SameSite=Lax`.
- Không refresh/session table; hết hạn thì login lại.
- Không trả/log password hash hoặc auth token.

### 9.2. CSRF/CORS

- Mutation dùng double-submit CSRF token hoặc cơ chế tương đương đã test.
- Frontend gửi CSRF header; backend so với cookie.
- CORS chỉ allow configured storefront origin.
- Internal endpoint dùng secret riêng, không dùng customer cookie.

### 9.3. Ownership

- Customer identity lấy từ verified token.
- Không tin customer/cart ID từ body.
- Cart/order luôn filter theo owner.
- Cross-customer access trả theo policy `404`/`403` thống nhất.

---

## 10. Transaction plan

### 10.1. TX-WEB-01 — Register

1. Normalize/validate và hash password ngoài transaction.
2. Begin `READ COMMITTED`.
3. Insert customer.
4. Insert credential.
5. Commit.

Unique normalized email là arbiter; customer/credential không commit một phần.

### 10.2. TX-WEB-02 — Cart mutation

1. Begin `READ COMMITTED`.
2. Find/lock active cart.
3. Nếu chưa có, insert; unique active-owner guard xử lý race.
4. Recheck cart active.
5. Lock item `(cart, variant)` nếu tồn tại.
6. Validate product/variant active.
7. Set absolute quantity hoặc logical remove.
8. Update cart timestamp.
9. Commit.

Cart mutation và checkout cùng lock cart root trước item.

### 10.3. TX-WEB-03 — Checkout

1. Validate request/idempotency/address.
2. Tính deterministic payment outcome ngoài transaction.
3. Begin `READ COMMITTED`.
4. Lookup idempotency key; nếu có, validate semantics và trả committed order.
5. Lock active cart; validate owner/state.
6. Lock present items.
7. Lock/read catalog theo stable order; validate sellable.
8. Lock inventory theo `variant_id` tăng dần.
9. Validate đủ stock.
10. Tính snapshots, subtotal, shipping fee, total bằng integer VND.
11. Insert order, items, payment, initial history.
12. Nếu succeeded, conditional decrement inventory và tăng version/timestamp.
13. Nếu failed, không update inventory.
14. Close cart.
15. Commit.

Order graph, cart closing và optional inventory decrement cùng commit/rollback. Không gọi Collector/email/external API trong transaction.

### 10.4. TX-WEB-04 — Complete order

1. Validate internal auth/idempotency.
2. Begin `READ COMMITTED`.
3. Lock order.
4. Nếu completed, trả committed result.
5. Nếu không paid, reject.
6. Update status/completed time.
7. Insert `paid → completed` history.
8. Commit.

### 10.5. Lock/retry

```text
customer nếu cần
→ cart
→ cart items theo variant_id
→ catalog rows theo stable ID
→ inventory theo variant_id
→ order
```

Deadlock/timeout retry toàn transaction tối đa hữu hạn với backoff+jitter. Không retry domain error.

---

## 11. Inventory và amount contract

### 11.1. Inventory

- Seed tạo `opening_on_hand = on_hand`.
- `opening_on_hand` immutable.
- `0 <= on_hand <= opening_on_hand`.
- Add-to-cart không reserve.
- Checkout succeeded là runtime flow duy nhất giảm stock.
- Failed payment không giảm stock.
- Không restock/adjustment; reset/reseed nếu cần.

Reconciliation:

```text
opening_on_hand - SUM(quantity của order items có succeeded payment) = on_hand
```

### 11.2. Shipping/amount

Config:

- `CURRENCY_CODE=VND`;
- `SHIPPING_FLAT_FEE_VND`;
- `FREE_SHIPPING_THRESHOLD_VND`.

Formula:

```text
line_total_vnd = unit_price_vnd × quantity
subtotal_vnd = SUM(line_total_vnd)
shipping_fee_vnd = 0 nếu subtotal đạt threshold, ngược lại flat fee
total_vnd = subtotal_vnd + shipping_fee_vnd
```

- Dùng integer VND.
- Server đọc variant price.
- Order/items snapshot amount và catalog label.
- Không coupon/tax.

---

## 12. Local payment simulator

### 12.1. Mục tiêu/rules

- Không external provider/network.
- Deterministic theo idempotency key + scenario/seed.
- Outcome tính trước DB transaction.
- Một order đúng một final payment row.
- Succeeded amount bằng total.
- Failed có failure code và không giảm stock.
- Không pending, refund hoặc nhiều attempt.

### 12.2. Mode

- Default: seeded deterministic success/failure ratio.
- Demo: cho phép forced outcome khi environment bật.
- Generator: scenario/run ID điều khiển outcome.
- Public-like mode không cho client tùy ý ép result.

---

## 13. Event plan

### 13.1. Ownership

Browser phát 4 clickstream event:

1. `session_start`;
2. `view_product`;
3. `add_to_cart`;
4. `begin_checkout`.

Downstream derive 3 business event từ OLTP:

1. `order_created`;
2. `payment_succeeded`;
3. `payment_failed`.

Collector chỉ nhận 4 behavior event; application không phát business JSONL thay cho OLTP.

### 13.2. Envelope

- event ID/name/schema version;
- event time;
- analytics session ID;
- optional pseudonymous customer/cart/product/variant reference;
- device class/optional traffic source/request ID;
- `data_origin`;
- payload.

Collector bổ sung received time, service/version và file transport metadata.

### 13.3. Trigger

| Event | Trigger | Required reference |
|---|---|---|
| `session_start` | Tạo analytics session | session |
| `view_product` | Detail load thành công | product |
| `add_to_cart` | Add/re-add commit thành công | cart + variant |
| `begin_checkout` | Submit checkout form | cart |

### 13.4. Session/delivery

- Analytics session là first-party browser ID, không phải auth/OLTP session.
- Rotate sau 30 phút inactivity.
- Không tạo `customer_sessions` trong MySQL.
- Best-effort; event failure không rollback transaction.
- Event ID là dedup key; retry giữ nguyên ID.
- Ưu tiên `sendBeacon`/`fetch keepalive`.
- Schema v2 thêm nullable `traffic_source` cho evolution test.

---

## 14. Event Collector và logging

### 14.1. Collector write path

Collector expose `POST /events/v1/events` cho một event/envelope:

- không dùng customer authentication làm nguồn actor chính thức;
- chỉ nhận request từ configured storefront origin;
- giới hạn content type và payload size;
- event hợp lệ trả `202 Accepted` sau khi writer nhận record;
- retry cùng `event_id` được deduplicate trong một bounded time window;
- event sai schema trả `400` với error code ổn định.

1. Validate envelope.
2. Gán received time.
3. Serialize một JSON line/event.
4. Append active temporary file.
5. Rotate theo size/time.
6. Flush theo policy.
7. Atomic rename thành closed `.jsonl`.

- Pipeline chỉ đọc closed file.
- Active file có suffix/directory riêng.
- Closed metadata có checksum, size, record count.
- Một writer process mặc định; multi-worker phải dùng single writer queue.
- Malformed request không ghi partial line.

### 14.2. Access/application log

Access log: timestamp, request ID, service, method, normalized route, status, latency, optional pseudonymous references, error code.

Application log: timestamp, service/version, level, request ID, operation/error code, sanitized message/stack.

Không log password/hash/token, raw email/IP, phone, address hoặc authorization header.

### 14.3. Metrics tối thiểu

- request count/status/latency;
- DB error/connection count;
- checkout success/failure/out-of-stock;
- deadlock/timeout/retry;
- event accepted/rejected;
- JSONL active/closed/rotation error;
- generator rows/scenarios/duration.

Không bắt buộc Prometheus; structured report/log đủ cho TLCN.

## 15. Generator và dữ liệu mẫu

Generator không chỉ tạo dữ liệu để trình diễn giao diện mà còn phải tạo nguồn dữ liệu đủ tin cậy cho pipeline DE và bài toán dự đoán khả năng mua lại.

### 15.1. Các chế độ chạy

| Chế độ | Mục đích | Dữ liệu chính |
|---|---|---|
| `seed_master` | Khởi tạo dữ liệu nền | category, product, variant, inventory |
| `historical_transactions` | Tạo lịch sử mua hàng | customer, cart, order, order_item, payment, order_status_history |
| `behavior_events` | Tạo clickstream có kiểm soát | 4 browser events trong event catalog |
| `repurchase_history` | Tạo tập dữ liệu phục vụ ML tương lai | chuỗi đơn hàng theo customer và thời gian |
| `failure_fixtures` | Tạo ca lỗi để kiểm thử | hết hàng, payment failed, request trùng, cart không hợp lệ |

Mỗi chế độ phải:

- nhận `seed` để có thể tái lập;
- nhận khoảng thời gian dữ liệu;
- ghi `generation_run_id` và `data_origin = generated`;
- xuất thống kê số bản ghi và số scenario;
- không bỏ qua API hoặc invariant nếu mục tiêu là kiểm thử tích hợp;
- có chế độ bulk riêng nếu mục tiêu chỉ là tạo lịch sử lớn cho DE.

### 15.2. Kiểm soát thời gian

- Generator dùng injectable clock thay vì sửa trực tiếp timestamp tùy ý trong public API.
- Dữ liệu lịch sử phải có `created_at`, `updated_at`, `occurred_at` và thứ tự trạng thái hợp lý.
- Không tạo payment thành công trước order hoặc order status history.
- Không tạo event browser xảy ra sau transaction một cách vô lý nếu chúng thuộc cùng một journey.
- Public web API không cho client tự truyền timestamp nghiệp vụ.

### 15.3. Dữ liệu inventory

- Khi seed variant, đặt `opening_on_hand = on_hand`.
- Sau khi tạo order thành công, `on_hand` giảm đúng theo số lượng bán.
- Không sinh nghiệp vụ restock/adjustment vì ngoài scope.
- Cuối mỗi run phải kiểm tra:

```text
opening_on_hand - tổng số lượng item của order thành công = on_hand
```

### 15.4. Dữ liệu cho bài toán mua lại

Dữ liệu lịch sử nên bao phủ tối thiểu 12 tháng và có:

- customer chỉ mua một lần;
- customer mua lặp lại sau nhiều khoảng thời gian khác nhau;
- customer có nhiều order nhưng bị payment fail ở một số lần;
- khác biệt về recency, frequency và monetary;
- khác biệt về category và variant đã mua;
- nhiễu hợp lý để tránh nhãn được quyết định bởi một quy tắc cứng.

Generator có thể dùng latent segment để sinh hành vi, nhưng không ghi segment đó vào bảng hoặc feature đầu vào nhằm tránh data leakage.

---

## 16. Handoff từ web sang DE

### 16.1. Nguồn MySQL

Pipeline được phép đọc hoặc CDC các bảng nghiệp vụ trong `schema.md`, ngoại trừ `customer_credentials` vì không có giá trị phân tích và chứa dữ liệu nhạy cảm.

Các lưu ý bắt buộc:

- `customers`, `products`, `product_variants`, `carts`, `cart_items`, `orders` và `inventory` có phần mutable;
- cart item bị xóa khỏi trải nghiệm người dùng bằng trạng thái logic theo schema, không làm mất lịch sử cần thiết;
- product/variant ngừng bán bằng trạng thái active/inactive;
- trên `orders`, chỉ state và state timestamps được đổi; amount, address và transaction snapshot là immutable;
- `order_items`, `payments` và `order_status_history` là immutable sau insert;
- `orders`, `payments` và `order_status_history` là nguồn nghiệp vụ chính thức cho ba business events;
- event browser là best-effort và không thay thế sự thật trong OLTP.

### 16.2. Source contract

Trước khi khóa source, lập data dictionary tối thiểu cho từng bảng:

- grain;
- PK, business key và FK;
- mô tả cột;
- timezone và đơn vị tiền;
- enum/status hợp lệ;
- mutable hay immutable;
- trường dùng cho incremental load;
- PII classification;
- quy tắc hard delete, logical delete hoặc anonymize.

### 16.3. Điều kiện bàn giao

- Schema version được ghi rõ.
- Seed/generator version được ghi rõ.
- Event catalog 7 event được khóa.
- JSONL closed-file contract được tài liệu hóa.
- Có query đối soát order, payment, inventory và event count.
- Có bộ fixture nhỏ, tái lập được để chạy pipeline end-to-end.

---

## 17. Security và privacy

### 17.1. Security checklist

- Secret, JWT key và database credential lấy từ environment hoặc secret file ngoài source control.
- Password chỉ lưu dưới dạng Argon2id hash.
- Cookie bật `HttpOnly`, `Secure` ở production và `SameSite` phù hợp.
- Request thay đổi trạng thái phải qua CSRF protection.
- Tất cả API cart/order kiểm tra ownership ở backend.
- Không tin `customer_id`, price, discount hoặc total do browser gửi.
- Validate content type, payload size, pagination và enum.
- Rate-limit nhẹ cho login, register, checkout và event ingestion.
- Trả error code ổn định, không lộ stack trace hoặc SQL.

### 17.2. Quyền database

- Runtime API chỉ có quyền cần cho nghiệp vụ.
- Migration dùng credential riêng.
- Pipeline DE dùng read-only hoặc CDC credential riêng.
- Event Collector không cần quyền ghi MySQL.
- Không cấp quyền đọc `customer_credentials` cho DE.

### 17.3. PII

- Không ghi raw email, phone, address, token hoặc IP vào event.
- Log chỉ dùng request ID và pseudonymous reference cần thiết.
- Order giữ snapshot giao dịch theo chính sách của `schema.md`.
- Quy trình anonymize customer phải giữ khóa quan hệ phục vụ audit và truyền thay đổi sang DE.

---

## 18. Chiến lược kiểm thử

Không dùng SQLite để thay thế các integration test liên quan tới lock, unique constraint, transaction hoặc isolation của MySQL.

### 18.1. Unit test backend

- validation request/response;
- password hashing và JWT;
- tính line amount, subtotal, shipping fee và grand total;
- state transition hợp lệ;
- mapping exception thành error code;
- event schema validation;
- generator probability và deterministic seed.

### 18.2. Unit/component test frontend

- loading, empty và error state;
- auth redirect;
- cart quantity control;
- checkout confirmation;
- payment result;
- event payload không chứa PII.

### 18.3. Integration test với MySQL

| Nhóm | Ca kiểm thử bắt buộc |
|---|---|
| Registration | customer và credential atomic; email trùng bị từ chối |
| Active cart | hai request tạo cart đồng thời vẫn chỉ có một active cart |
| Cart item | add trùng variant tăng quantity; remove rồi add lại đúng quy tắc logic |
| Checkout success | tạo order, item, payment, history và giảm inventory trong một transaction |
| Checkout failure | tạo `payment_failed` order/payment, đóng cart và không giảm inventory |
| Amount | server tính đúng subtotal, shipping fee và grand total |
| Idempotency | retry cùng key trả cùng kết quả; cùng key khác payload bị từ chối |
| Inventory | hai checkout tranh item cuối chỉ một request thành công |
| Completion | transition pending sang completed đúng; request lặp không tạo lịch sử trùng |
| Reconciliation | opening stock trừ sold quantity bằng current stock |

### 18.4. Event Collector test

- nhận đúng 4 loại browser event;
- từ chối event sai schema/version;
- deduplicate theo event ID trong cửa sổ cấu hình;
- rotate file đúng ngưỡng;
- pipeline chỉ thấy closed file;
- restart không làm hỏng dòng JSONL;
- malformed request không tạo partial record.

### 18.5. End-to-end test

1. Register và login.
2. Xem danh sách và chi tiết sản phẩm.
3. Add cùng variant hai lần.
4. Sửa quantity và xóa item.
5. Checkout thành công.
6. Xem order detail và trạng thái.
7. Kích hoạt completion nội bộ.
8. Xác minh order, payment, inventory, history và closed event file.

### 18.6. Non-functional test

- kiểm tra query plan cho catalog, cart, order history;
- chạy concurrency test cho active cart và last-item checkout;
- kiểm tra request timeout/retry;
- kiểm tra log không chứa secret/PII;
- kiểm tra generator tái lập với cùng seed;
- smoke test toàn bộ Docker Compose.

---

## 19. Cấu trúc repository đề xuất

```text
.
├── apps/
│   └── storefront/              # Next.js
├── services/
│   ├── ecommerce-api/           # FastAPI
│   └── event-collector/         # Service Python nhỏ
├── database/
│   ├── migrations/
│   └── seeds/
├── generator/
│   ├── scenarios/
│   └── fixtures/
├── data/
│   └── events/                  # Local only, gitignored
├── docs/
│   ├── api/
│   ├── event-catalog/
│   └── source-contract/
├── docker-compose.yml
└── .env.example
```

Không tách microservice theo từng domain. `ecommerce-api` là modular monolith để giảm chi phí vận hành và giữ transaction boundary rõ ràng.

---

## 20. Môi trường chạy

### 20.1. Docker Compose

Các service tối thiểu:

- `mysql`;
- `ecommerce-api`;
- `storefront`;
- `event-collector`;
- generator chạy theo profile hoặc one-shot job.

Pipeline DE có thể nằm ở Compose riêng hoặc profile riêng để web vẫn chạy độc lập.

### 20.2. Nhóm cấu hình

- database URL và pool;
- JWT/cookie/CSRF;
- storefront API URL;
- event collector URL;
- shipping fee và free-shipping threshold;
- JSONL directory, rotation size/time;
- log level;
- generator seed/time range.

### 20.3. Startup order

1. MySQL healthy.
2. Migration hoàn tất.
3. Seed master data nếu môi trường trống.
4. API và Event Collector healthy.
5. Frontend sẵn sàng.
6. Generator hoặc pipeline chạy theo nhu cầu.

---

## 21. Roadmap triển khai ba tuần

### Tuần 1 — Nền tảng và catalog

- dựng cấu trúc repository và Docker Compose;
- triển khai schema/migration theo `schema.md`;
- seed category, product, variant và inventory;
- làm register, login, logout và current user;
- làm product list, filter cơ bản và product detail;
- thiết lập request ID, structured log và health check;
- viết unit test cho auth, amount và catalog.

**Đầu ra:** người dùng tạo tài khoản, đăng nhập và xem catalog từ MySQL.

### Tuần 2 — Cart, checkout và order

- làm active cart và cart item mutation;
- triển khai amount calculator;
- triển khai payment simulator;
- triển khai checkout transaction và idempotency;
- triển khai order list/detail;
- triển khai internal completion;
- viết integration/concurrency test với MySQL.

**Đầu ra:** flow mua hàng đơn giản chạy trọn vẹn và giữ đúng invariant.

### Tuần 3 — Event, generator và bàn giao DE

- tích hợp 4 browser events;
- hoàn thiện Event Collector và JSONL rotation;
- xác định cách derive 3 business events;
- viết generator cho history, repurchase và failure fixture;
- chạy E2E, reconciliation và privacy check;
- hoàn thiện API spec, event catalog và source contract;
- khóa source schema/event cuối tuần.

**Đầu ra:** web ổn định, có nguồn OLTP và event đủ để pipeline DE tiếp tục.

Sau source freeze, chỉ sửa bug hoặc contract violation; không bổ sung nghiệp vụ web mới.

---

## 22. Phân công hai người

| Hạng mục | Người A | Người B | Phối hợp |
|---|---|---|---|
| Frontend | Chính | Review | E2E |
| FastAPI domain/API | Chính | Review transaction | Contract |
| MySQL/migration | Review | Chính | Invariant |
| Event Collector | Review client | Chính | Event schema |
| Generator | Scenario nghiệp vụ | Khung và reproducibility | Data quality |
| Testing | Unit frontend/backend | Integration/concurrency | E2E |
| Tài liệu | API/UX | Source/event contract | Demo |

Nguyên tắc:

- một người sở hữu chính mỗi hạng mục nhưng mọi contract phải được review chéo;
- cả hai cùng hiểu checkout transaction và inventory invariant;
- không để một người chỉ làm web và người còn lại chỉ làm DE;
- sau tuần 3, phần lớn nguồn lực chuyển sang pipeline DE và phân tích.

---

## 23. Mốc nghiệm thu

| Mốc | Nội dung | Điều kiện qua |
|---|---|---|
| `WEB-M0` | Foundation | Compose chạy, migration/seed thành công, health check xanh |
| `WEB-M1` | Auth + Catalog | register/login và duyệt catalog hoạt động |
| `WEB-M2` | Commerce Core | cart, checkout, order và inventory đúng transaction |
| `WEB-M3` | Data Source Ready | event, generator, test và source contract hoàn tất |

Không chuyển mốc nếu integration test quan trọng của mốc hiện tại chưa qua.

---

## 24. Deliverables phần web

- source code `storefront`, `ecommerce-api`, `event-collector`;
- Docker Compose và `.env.example`;
- migration và master-data seed;
- OpenAPI specification;
- source data dictionary;
- event catalog 7 event;
- generator và failure fixtures;
- unit, integration, concurrency và E2E tests;
- script/query reconciliation;
- hướng dẫn chạy local và kịch bản demo;
- báo cáo giới hạn phạm vi và các hướng mở rộng sau TLCN.

---

## 25. Tiêu chí nghiệm thu chi tiết

### 25.1. Auth và catalog

- Register tạo customer và credential atomic; active cart được tạo lazy ở cart mutation đầu tiên.
- Email trùng bị từ chối rõ ràng.
- Password không xuất hiện trong log hoặc response.
- Public xem được catalog, authenticated endpoint từ chối anonymous.
- Product/variant inactive không được thêm mới vào cart.

### 25.2. Cart

- Mỗi customer có tối đa một active cart.
- Một variant chỉ có một cart item logic trong active cart.
- Quantity luôn dương và không vượt giới hạn cấu hình.
- Cart không reserve hay giảm inventory.
- Cart checkout không được tái sử dụng.

### 25.3. Checkout và order

- Server snapshot name, SKU, unit price và amount.
- Mỗi cart tạo tối đa một order.
- Payment failed vẫn tạo `payment_failed` order/payment, đóng cart và không giảm inventory.
- Payment success, order và inventory commit atomic.
- Retry cùng idempotency key không tạo giao dịch mới.
- Order total bằng tổng item và shipping snapshot theo invariant.
- Không gọi external API trong database transaction.

### 25.4. Inventory

- `opening_on_hand` và `on_hand` không âm.
- Checkout lock đúng variant rows theo thứ tự ổn định.
- Không oversell khi có request đồng thời.
- Reconciliation query cho kết quả bằng nhau.
- Không có restock/adjustment ngoài scope.

### 25.5. Event, log và generator

- Browser phát đúng 4 event, không chứa PII.
- Ba business events được derive từ OLTP.
- Event Collector tạo closed JSONL hợp lệ.
- Log có request ID, status, latency và error code.
- Generator chạy lại cùng seed cho kết quả thống kê tương đương.
- Dữ liệu lịch sử đủ cho pipeline và bài toán mua lại tương lai.

### 25.6. Vận hành

- Một lệnh có thể dựng môi trường local.
- Migration chạy từ database rỗng.
- Smoke test qua sau khi restart service.
- Source contract và OpenAPI khớp implementation.

---

## 26. Kịch bản demo

1. Khởi động hệ thống và hiển thị health check.
2. Register một customer mới.
3. Duyệt category, product và chọn variant.
4. Add-to-cart, sửa quantity và xem tổng tạm tính.
5. Checkout thành công và xem order detail.
6. Hiển thị payment, inventory giảm và order status history.
7. Gọi internal completion và xác minh transition.
8. Mở closed JSONL để chỉ ra clickstream đã được thu.
9. Chạy query derive ba business events.
10. Chạy reconciliation và trình bày dữ liệu đầu vào cho pipeline DE.

Nên có thêm một ca payment failed và một ca tranh item cuối để chứng minh xử lý lỗi/concurrency.

---

## 27. Rủi ro và cách kiểm soát

| Rủi ro | Kiểm soát |
|---|---|
| Web lấn át phần DE | Khóa scope, hoàn thành trong ba tuần, không thêm feature sau `WEB-M3` |
| Sai transaction checkout | Viết integration/concurrency test trước khi làm đẹp UI |
| Schema và API lệch nhau | Dùng `schema.md` làm contract và review migration theo invariant |
| Event chứa PII | Allowlist field, schema validation và automated privacy test |
| JSONL bị đọc khi đang ghi | Active/closed protocol và atomic rename |
| Generator tạo dữ liệu giả quá sạch | Thêm noise, failure scenario và nhiều hành vi mua lại |
| Dữ liệu không tái lập | Seed, generation run metadata và fixture version |
| Hai người phụ thuộc nhau | Chốt contract sớm, chia ownership và review chéo |

---

## 28. Checklist trước khi chuyển trọng tâm sang DE

- [ ] Tất cả endpoint trong API catalogue đã có hoặc được đánh dấu loại bỏ chính thức.
- [ ] Schema thực tế khớp 12 bảng trong `schema.md`.
- [ ] Checkout và inventory concurrency test đã qua.
- [ ] Reconciliation inventory không lệch.
- [ ] Event catalog đúng 7 event.
- [ ] Event Collector chỉ bàn giao closed JSONL.
- [ ] Generator có seed và tạo được lịch sử mua lại.
- [ ] OpenAPI, source contract và data dictionary đã khóa phiên bản.
- [ ] Không có password, token hoặc raw PII trong log/event.
- [ ] Demo end-to-end chạy lại được trên môi trường sạch.
- [ ] Các giới hạn ngoài scope được ghi rõ.
- [ ] Nhóm xác nhận source freeze và chuyển trọng tâm sang DE.

---

## 29. Hướng mở rộng sau TLCN

Các hạng mục sau chỉ được xem là hướng phát triển, không triển khai trong phần web TLCN:

- anonymous cart và merge cart;
- coupon, refund, shipment, return, review;
- multiple warehouse và reservation;
- payment gateway thật;
- transactional outbox;
- admin/CMS đầy đủ;
- recommendation hoặc ML inference online;
- mở rộng event catalog ngoài 7 event đã khóa.

Việc ghi rõ hướng mở rộng giúp thiết kế không tự khóa đường phát triển, nhưng không được dùng để mở rộng scope triển khai hiện tại.
