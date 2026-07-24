# KẾ HOẠCH TIỂU LUẬN CHUYÊN NGÀNH

## 0. Thông tin tài liệu

Tài liệu này định nghĩa phạm vi và kế hoạch triển khai **Tiểu luận chuyên ngành (TLCN)** cho một hệ thống Data Lakehouse xử lý theo lô.

Tài liệu bao gồm:

- mục tiêu và câu hỏi nghiên cứu;
- source application tối giản;
- logical schema OLTP;
- event, log và generator;
- kiến trúc Data Lakehouse Bronze–Silver–Gold;
- ingestion, transformation, data quality và reconciliation;
- BI serving;
- bài toán Machine Learning dự đoán khả năng khách hàng mua lại;
- testing, roadmap, phân công và acceptance criteria.

Tài liệu chỉ mô tả thiết kế logic và kế hoạch thực hiện. Chưa viết DDL, migration hoặc code triển khai.

---

## 1. Tên đề tài

**Xây dựng Data Lakehouse xử lý theo lô cho dữ liệu giao dịch, hành vi và dự đoán khả năng khách hàng mua lại trên website thương mại điện tử tối giản**

Tên tiếng Anh:

**Building a Batch Data Lakehouse for Transactional and Behavioral Data with Customer Repurchase Prediction from a Minimal E-commerce Website**

---

## 2. Bối cảnh

Website thương mại điện tử phát sinh hai nhóm dữ liệu chính:

1. Dữ liệu giao dịch có cấu trúc trong MySQL: customer, product, cart, order, payment và inventory.
2. Dữ liệu bán cấu trúc trong JSONL: clickstream, access log và application log.

Nếu truy vấn phân tích trực tiếp trên OLTP sẽ làm tăng tải source database, khó tái hiện lịch sử và khó kiểm soát dữ liệu lỗi. TLCN xây dựng một pipeline batch để đưa dữ liệu từ MySQL và JSONL vào Data Lakehouse, chuẩn hóa và tích hợp dữ liệu, tạo các bảng phân tích và phục vụ dashboard mà không biến OLTP thành hệ thống báo cáo.

Website chỉ đóng vai trò source application tạo dữ liệu có kiểm soát. Trọng tâm của đề tài là tính đúng đắn, khả năng chạy lại và khả năng tái lập của pipeline Data Engineering.

Trên dữ liệu đã được chuẩn hóa tại Gold, TLCN bổ sung một bài toán ML nhỏ để chứng minh dữ liệu lakehouse có thể phục vụ một use case dự đoán có ý nghĩa. Bài toán dự đoán xác suất một customer đã từng mua sẽ phát sinh thêm ít nhất một đơn paid trong 30 ngày tiếp theo. ML là downstream consumer của Gold, không làm tăng nghiệp vụ website và không thay đổi vai trò system of record của OLTP.

---

## 3. Câu hỏi nghiên cứu

- **RQ1:** Tích hợp dữ liệu có cấu trúc từ MySQL và dữ liệu bán cấu trúc từ JSONL vào Data Lakehouse theo lô như thế nào?
- **RQ2:** Làm thế nào để pipeline incremental có thể rerun, replay và backfill mà không làm sai logical row hoặc KPI?
- **RQ3:** Phân biệt và xử lý ingestion error, schema error, business-quality error, duplicate và late-arriving record như thế nào?
- **RQ4:** Đối soát dữ liệu từ source đến Silver, Gold và BI serving tại cùng batch cutoff như thế nào?
- **RQ5:** Mô hình hóa fact, dimension và mart như thế nào để grain rõ ràng và không chạy analytics nặng trên OLTP?
- **RQ6:** Có thể xây dựng tập dữ liệu point-in-time và mô hình baseline có khả năng dự đoán customer mua lại trong 30 ngày mà tránh target leakage như thế nào?

---

## 4. Mục tiêu

### 4.1. Mục tiêu tổng quát

Xây dựng một hệ thống Data Lakehouse xử lý theo lô có khả năng thu nhận, lưu trữ, làm sạch, tích hợp, kiểm tra chất lượng, đối soát, phục vụ phân tích và tạo dữ liệu point-in-time cho bài toán dự đoán khả năng customer mua lại từ website thương mại điện tử tối giản.

### 4.2. Năng lực phải chứng minh

1. Website tạo được dữ liệu customer, product, cart, order, payment và inventory hợp lệ.
2. Event Collector nhận clickstream theo versioned contract và ghi rotating JSONL.
3. Generator tạo dữ liệu lịch sử có seed, scenario và `data_origin`.
4. Airflow điều phối initial load, incremental load, rerun, replay và backfill.
5. Bronze giữ raw data và đủ để rebuild toàn bộ Silver.
6. Silver chuẩn hóa, deduplicate, integrate, sessionize và quarantine.
7. Gold có fact, dimension và mart với grain rõ.
8. Cursor chỉ commit sau khi toàn bộ run được validate, reconcile và publish thành công.
9. Cùng input, code và config tạo cùng logical output.
10. Count, amount và inventory balance đối soát được với source tại cùng cutoff.
11. Late event và schema version mới được xử lý có kiểm soát.
12. Dashboard Superset chỉ đọc MySQL `analytics`.
13. Môi trường dựng lại được từ clean volumes bằng Docker Compose và runbook.
14. Feature/label dataset có grain `customer × as_of_date`, không dùng dữ liệu phát sinh sau thời điểm dự báo.
15. Mô hình repurchase được so sánh với baseline bằng temporal split và lưu đủ manifest để tái lập.
16. Batch prediction được publish bằng pseudonymous customer key, model version và score time.

---

## 5. Phạm vi TLCN

### 5.1. Source website

Website thực hiện các chức năng sau:

1. Đăng ký và đăng nhập tối thiểu.
2. Xem danh sách sản phẩm.
3. Xem chi tiết sản phẩm và variant.
4. Lọc sản phẩm theo category.
5. Customer đã đăng nhập thêm, xóa và cập nhật sản phẩm trong cart.
6. Checkout với địa chỉ nhập trực tiếp.
7. Local payment simulator trả kết quả `succeeded` hoặc `failed`.
8. Hiển thị kết quả checkout.
9. Xem lịch sử order tối thiểu.
10. Internal endpoint hoặc generator chuyển paid order sang `completed`.

UI chỉ cần rõ ràng và đủ để demo source flow; không dành thời gian cho animation hoặc frontend polish không phục vụ dữ liệu.

### 5.2. Data Engineering

TLCN thực hiện:

- source catalogue và data contract;
- MySQL initial/incremental extraction;
- JSONL closed-file discovery và ingestion;
- deterministic cutoff manifest;
- cursor management;
- pipeline audit;
- Bronze raw append-only;
- Silver typed, deduplicated và integrated;
- Gold facts, dimensions và marts;
- data quality rules;
- ingestion error và Silver quarantine;
- source-to-target reconciliation;
- idempotent rerun;
- replay từ Bronze;
- backfill theo source/date range;
- late-arriving event handling;
- event schema versioning và schema-evolution scenario;
- publish staging vào MySQL `analytics`;
- một Superset dashboard;
- pipeline observability;
- local performance/resource report;
- reproducible generator và clean-run rehearsal.

### 5.3. BI

Dashboard gồm năm khu vực:

1. Sales overview.
2. Funnel overview.
3. Product performance.
4. Inventory status.
5. Repurchase propensity.

### 5.4. Machine Learning

TLCN thực hiện một bài toán nhị phân:

> Với một customer đã có ít nhất một paid order trước thời điểm dự báo, dự đoán customer đó có phát sinh thêm ít nhất một paid order trong 30 ngày tiếp theo hay không.

Toàn bộ feature và label chỉ được tạo từ MySQL/JSONL do source website và generator của đề tài sinh ra; không dùng dataset bên ngoài.

Phạm vi ML gồm:

- feature engineering theo thời điểm từ dữ liệu Gold;
- label 30 ngày từ succeeded payment/paid order;
- rolling historical snapshots để tạo training rows;
- temporal train/validation/test split;
- `DummyClassifier` làm baseline;
- Logistic Regression là mô hình chính dễ giải thích;
- một tree-based model nhẹ để so sánh nếu đủ thời gian;
- batch training, evaluation, artifact manifest và batch scoring;
- publish customer score đã pseudonymize cho dashboard;
- báo cáo leakage, class imbalance, calibration và giới hạn synthetic data.

Không triển khai:

- online inference API;
- recommendation/personalization;
- deep learning;
- automated retraining phức tạp;
- feature store riêng;
- MLflow;
- causal inference hoặc khẳng định chiến dịch marketing làm customer mua lại.

---

## 6. Nguyên tắc kiến trúc

- MySQL ecommerce là system of record cho dữ liệu giao dịch.
- Delta Gold là nguồn phân tích chuẩn.
- MySQL `analytics` chỉ là serving copy cho Superset.
- Không chạy analytics nặng trên OLTP primary.
- Bronze append-only và giữ source duplicate.
- Silver rebuild được từ Bronze và pipeline metadata.
- Timestamp lưu UTC; dashboard hiển thị `Asia/Ho_Chi_Minh`.
- Tiền lưu bằng số nguyên VND hoặc decimal chính xác; không dùng `FLOAT`/`DOUBLE`.
- Mỗi source, table, fact và mart có grain rõ.
- Mỗi batch có input identity, cutoff và output identity rõ.
- Cursor không commit trước khi full run thành công.
- Pipeline retry không được nhân logical row.
- Publish dùng staging và validation trước khi serving.
- Feature và label phải point-in-time correct; không dùng dữ liệu sau `as_of_time` để tạo feature.
- Training, evaluation và scoring phải gắn với Gold dataset version, feature schema version và model version.
- ML failure không được rollback hoặc chặn cursor của core DE pipeline đã publish thành công.
- Correctness và reproducibility được ưu tiên hơn throughput.

---

## 7. Tech stack

| Thành phần | Công nghệ |
|---|---|
| Frontend | Node.js 22 LTS, Next.js 15, TypeScript, Tailwind |
| Backend | Python 3.11, FastAPI, Pydantic 2, SQLAlchemy 2, Alembic |
| OLTP | MySQL 8.4 LTS, InnoDB |
| Event Collector | FastAPI, Pydantic, rotating JSONL |
| Processing | Apache Spark 3.5.x, PySpark |
| Table format | Delta Lake 3.3.x, Scala 2.12 |
| Object storage | MinIO |
| Orchestration | Airflow 2.10.x, LocalExecutor |
| Metadata DB | PostgreSQL cho Airflow/Superset |
| BI serving | MySQL `analytics` |
| BI | Apache Superset |
| Machine Learning | scikit-learn, joblib; exact version pin trong dependency lock |
| ML input/output | Gold Delta/Parquet; artifact và manifest lưu trên MinIO |
| Testing | pytest, PySpark data tests, Vitest/Playwright tối thiểu |
| Packaging | Docker Compose v2, Makefile |
| JVM | Java 17 |
| Version control | GitHub |

Version phải được pin; không dùng tag `latest`.

---

## 8. Kiến trúc logical

```text
Browser → Next.js → FastAPI → MySQL ecommerce
       └───────────────→ Event Collector → closed JSONL

MySQL tables + closed JSONL
→ Airflow capture source cutoffs
→ Spark extract/ingest
→ Bronze Delta
→ Silver Delta
→ Gold Delta
→ publish staging
→ MySQL analytics
→ Superset

Gold Delta
→ point-in-time feature/label dataset
→ temporal split
→ train/evaluate model
→ versioned artifact + batch prediction
→ MySQL analytics/Superset
```

### 8.1. Vai trò từng khối

- **Next.js/FastAPI:** tạo dữ liệu nghiệp vụ và hành vi.
- **MySQL ecommerce:** lưu trạng thái giao dịch chính thức.
- **Collector/JSONL:** thu clickstream và operational logs.
- **Airflow:** orchestration, dependency, retry và audit.
- **Spark:** extraction và transformation theo lô.
- **Delta Lake:** lưu Bronze, Silver và Gold.
- **MinIO:** object storage cho Delta tables, manifests và reports.
- **MySQL analytics:** serving database cho BI.
- **Superset:** trực quan hóa dữ liệu đã publish.
- **scikit-learn:** huấn luyện baseline/model nhẹ và batch scoring trên feature dataset đã được Spark chuẩn bị.
- **MinIO ML artifacts:** lưu model, preprocessing pipeline, metrics và manifest; không dùng MLflow.

### 8.2. Docker profiles

- `core`: storefront, API, Collector và MySQL ecommerce.
- `batch`: MinIO, Spark, Airflow và PostgreSQL metadata.
- `bi`: MySQL analytics và Superset.

Mỗi service có health check, persistent volume, resource limit và init procedure.

---

## 9. Source website design

### 9.1. Pages

- Register/login.
- Product listing.
- Product detail.
- Cart.
- Checkout.
- Checkout result.
- Order history tối giản.

### 9.2. API groups

- Authentication.
- Catalog/product/variant.
- Cart mutation.
- Checkout.
- Order lookup.
- Internal order completion.
- Event collection.

### 9.3. Business flow

```text
register/login
→ browse catalog
→ view product
→ add to cart
→ begin checkout
→ validate cart/inventory
→ local payment outcome
→ paid hoặc payment_failed order
→ optional completion simulation
```

### 9.4. Local payment simulator

- Không gọi payment provider bên ngoài.
- Outcome được cấu hình hoặc sinh deterministically cho generator scenario.
- Một order có đúng một payment row.
- Success checkout giảm inventory trong cùng transaction tạo order.
- Failed checkout không thay đổi inventory.
- Customer tạo cart/order mới nếu muốn thực hiện checkout lần khác.

---

## 10. Logical schema OLTP

Logical schema gồm 12 bảng.

| Bảng | Grain | Mục đích và invariant chính |
|---|---|---|
| `customers` | Một customer | Public UUID unique; profile tối thiểu; status active/inactive |
| `customer_credentials` | Một credential/customer | Email normalized unique; password hash không extract sang lakehouse |
| `categories` | Một category | Optional `parent_id`; tên/code unique trong scope phù hợp |
| `products` | Một product | Tên, mô tả ngắn, category, image URL và active status |
| `product_variants` | Một product-size-color | SKU unique; combination unique/product; price VND integer |
| `carts` | Một cart/customer | `active` hoặc `checked_out`; tối đa một active cart/customer |
| `cart_items` | Một variant/cart | Unique `(cart_id, variant_id)`; quantity dương |
| `orders` | Một checkout result | Customer/cart, status, subtotal, shipping fee, total và address snapshot |
| `order_items` | Một variant line/order | Snapshot SKU, name, size, color, unit price và quantity |
| `payments` | Một payment/order | Unique order; status `succeeded` hoặc `failed`; amount snapshot |
| `order_status_history` | Một order transition | Append-only; from/to/time/source |
| `inventory` | Một variant | `opening_on_hand >= on_hand >= 0`; không restock/adjustment trong TLCN |

### 10.1. Customer

`customers` lưu public key, tên hiển thị, contact fields tối thiểu, status và timestamps.

`customer_credentials` lưu normalized email, password hash, enabled status và credential timestamps. Pipeline không extract bảng này.

### 10.2. Catalog

`categories` hỗ trợ category cha/con ở mức dữ liệu; website chỉ cần filter theo category.

`products` lưu dữ liệu dùng chung của sản phẩm.

`product_variants` lưu SKU, size, color, price và active status. Mỗi product không có hai variant trùng tổ hợp size/color.

### 10.3. Cart

`carts` thuộc customer đã đăng nhập. Cart checked-out không tái sử dụng.

`cart_items` lưu variant, quantity và timestamps. Add-to-cart không giữ inventory; checkout luôn validate lại.

### 10.4. Order và payment

`orders` snapshot customer-facing values tại checkout:

- subtotal;
- shipping fee;
- total amount;
- receiver name;
- phone;
- address text;
- order status;
- created/updated/completed time.

`order_items` snapshot product/variant information và price tại thời điểm checkout.

`payments` lưu một kết quả payment/order. Payment succeeded amount phải bằng order total.

`order_status_history` giữ mọi transition; không update hoặc delete row lịch sử.

### 10.5. Inventory

`inventory` lưu:

- `opening_on_hand`: tồn kho khởi tạo, immutable sau seed;
- `on_hand`: tồn kho hiện hành.

TLCN không hỗ trợ restock hoặc inventory adjustment sau seed. Success checkout giảm `on_hand` trong cùng transaction với order/payment; failed checkout không thay đổi inventory. Invariant:

```text
0 <= on_hand <= opening_on_hand
```

Pipeline đối soát current stock theo công thức:

```text
opening_on_hand - sold units từ succeeded payments = on_hand
```

### 10.6. State machines

Cart:

```text
active → checked_out
```

Order:

```text
paid → completed
payment_failed
```

Payment:

```text
succeeded
failed
```

---

## 11. Transaction catalogue

### T1. Cart mutation

- Tìm hoặc tạo active cart/customer.
- Lock cart và cart item cần cập nhật.
- Upsert/delete item.
- Update cart timestamp.
- Commit.

### T2. Checkout

1. Lock cart và cart items.
2. Lock inventory theo variant ID tăng dần.
3. Validate active variant và `on_hand >= quantity`.
4. Tính subtotal, shipping fee và total.
5. Lấy kết quả từ local payment simulator.
6. Tạo order, order items, payment và initial status history.
7. Nếu success: giảm `on_hand`, order=`paid`.
8. Nếu failure: không đổi inventory, order=`payment_failed`.
9. Cart chuyển `checked_out`.
10. Commit.

Transaction dùng InnoDB `READ COMMITTED` và locking read.

### T3. Complete order

- Lock paid order.
- Validate transition `paid → completed`.
- Update order và insert status history.
- Duplicate completion trả cùng committed result.

### 11.1. Concurrency tests

- Hai checkout cạnh tranh last item không làm `on_hand` âm.
- Duplicate complete order không tạo hai transition.
- Success checkout và inventory decrement luôn commit/rollback cùng nhau.
- Failed checkout không thay đổi inventory.

---

## 12. Event catalog — 7 event

| Event | Source chính thức | Grain | Mục đích |
|---|---|---|---|
| `session_start` | Clickstream JSONL | Một analytics session start | Session denominator |
| `view_product` | Clickstream JSONL | Một product view | Product interest |
| `add_to_cart` | Clickstream JSONL | Một successful add | Funnel cart step |
| `begin_checkout` | Clickstream JSONL | Một checkout click | Funnel checkout step |
| `order_created` | Derived từ OLTP order | Một order | Canonical business event |
| `payment_succeeded` | Derived từ OLTP payment | Một succeeded payment | Paid conversion và revenue |
| `payment_failed` | Derived từ OLTP payment | Một failed payment | Checkout failure |

### 12.1. Clickstream envelope

Mọi clickstream event có:

- event ID;
- event name;
- schema version;
- event time;
- collector received time;
- analytics session ID;
- optional customer/cart/product/variant reference;
- device class;
- optional traffic source;
- request ID nếu có;
- `data_origin`;
- payload.

### 12.2. Source-of-truth rule

- Clickstream là best-effort và dùng cho hành vi/funnel.
- Order và payment events được derive từ OLTP trong Silver.
- Application không phát business event rồi coi JSONL là nguồn sự thật thay cho OLTP.

---

## 13. Logging

### 13.1. Access log

Grain: một HTTP request.

Fields:

- timestamp;
- request ID;
- method;
- normalized route;
- status code;
- latency;
- service;
- optional pseudonymous customer/session reference.

### 13.2. Application log

Grain: một application log entry.

Fields:

- timestamp;
- service;
- level;
- request ID;
- error code;
- sanitized message/stack.

Log được ghi JSON một dòng và không chứa password, token, raw IP hoặc shipping address.

---

## 14. Synthetic generator

Generator là nguồn dữ liệu có thể tái lập cho pipeline test và demo.

### 14.1. Modes

- `seed_master`: category, product, variant và `opening_on_hand`/`on_hand` ban đầu.
- `historical_transactions`: customer, cart, paid/failed order, payment, inventory decrement do paid order và completion.
- `behavior_events`: session, view, add và checkout events.
- `failure_fixtures`: malformed JSON, duplicate, invalid enum, negative amount, missing reference, late event và unknown schema version.
- `repurchase_history`: tạo tối thiểu 12 tháng hành vi/giao dịch với các mức recency, frequency và engagement khác nhau để có rolling ML snapshots.

### 14.2. Metadata

- seed;
- scenario ID;
- generator version;
- configurable time anchor;
- generated time;
- `data_origin`;
- expected row/KPI manifest.

### 14.3. Reproducibility

- Cùng seed, version và config tạo cùng logical dataset.
- Normal historical data đi qua API hoặc shared domain service.
- Failure fixtures dùng path/namespace riêng.
- Synthetic và manually created data phân biệt được.
- Có ba cấu hình dữ liệu: small, medium và large-local.
- Repurchase scenario có class-distribution manifest, nhưng latent generator segment không được ghi vào source row hoặc dùng làm feature.
- Tín hiệu mua lại phải có noise; không tạo một feature đơn lẻ quyết định trực tiếp label.

---

## 15. Source catalogue và batch boundary

### 15.1. MySQL sources

- customers;
- categories;
- products;
- product variants;
- carts và cart items;
- orders và order items;
- payments;
- order status history;
- inventory.

### 15.2. JSONL sources

- web events;
- access logs;
- application logs;
- failure fixture files.

Collector ghi file tạm, rotate theo time/size rồi atomic rename thành closed file. Pipeline chỉ ingest closed files.

### 15.3. Cutoff manifest

Mỗi pipeline run tạo manifest chứa:

- run/batch ID;
- source name;
- low cursor;
- captured high cursor;
- file path/checksum/size/record count;
- source schema version;
- capture time;
- code/config version.

### 15.4. Incremental cursor

- Mutable table: `(updated_at, internal_pk)`.
- Append-only table: `(created_at, internal_pk)`.
- JSONL: closed-file manifest identity.

Pipeline thực hiện:

1. Read committed low cursor.
2. Capture high cursor/source manifest.
3. Extract `(low, high]` với configurable lookback.
4. Write và validate Bronze.
5. Build Silver/Gold.
6. Reconcile và publish.
7. Commit cursor khi full run success.

---

## 16. Airflow DAG

```text
check_services
→ capture_mysql_high_cursors + discover_closed_jsonl
→ extract_mysql + ingest_jsonl
→ write_bronze
→ validate_bronze
→ build_silver_domain + build_silver_events_logs
→ run_silver_dq
→ build_gold_dimensions + build_gold_facts
→ build_gold_marts
→ reconcile_source_to_gold
→ publish_analytics_staging
→ validate_publish
→ swap_or_upsert_analytics
→ commit_cursors
→ publish_pipeline_audit
```

ML dùng DAG downstream riêng, chỉ nhận một Gold publication đã thành công:

```text
resolve_gold_publication
→ build_point_in_time_features
→ build_repurchase_labels
→ validate_ml_dataset
→ temporal_split
→ train_dummy_and_logistic
→ optional_train_random_forest
→ evaluate_and_select
→ persist_model_artifact_manifest
→ batch_score_eligible_customers
→ validate_predictions
→ publish_repurchase_scores
→ publish_ml_audit
```

Core DE DAG không chờ ML DAG để commit source cursor. Training failure giữ nguyên Gold/BI publication gần nhất và model production gần nhất.

### 16.1. DAG invariants

- Task retry không nhân logical row.
- Cursor không commit sớm.
- Failed run giữ đủ audit để rerun.
- Publish không để dashboard đọc bảng nửa hoàn thành.
- Backfill không làm hỏng scheduled cursor.
- Task output có deterministic identity.
- ML run không tự động ghi đè model tốt gần nhất nếu dataset, DQ hoặc evaluation gate thất bại.
- Rerun cùng Gold version, ML config, code và seed tạo cùng split, feature rows và prediction trong tolerance đã định nghĩa.

---

## 17. Bronze layer

### 17.1. Trách nhiệm

- Lưu raw source representation.
- Bổ sung ingestion metadata.
- Giữ source duplicate.
- Cho phép replay Silver mà không đọc lại source.
- Không join, sessionize hoặc tính KPI.

### 17.2. Bronze tables

Naming MySQL batch: `bronze_<entity>_batch`.

Tối thiểu:

- `bronze_customers_batch`;
- `bronze_categories_batch`;
- `bronze_products_batch`;
- `bronze_product_variants_batch`;
- `bronze_carts_batch`, `bronze_cart_items_batch`;
- `bronze_orders_batch`, `bronze_order_items_batch`;
- `bronze_payments_batch`;
- `bronze_order_status_history_batch`;
- `bronze_inventory_batch`;
- `bronze_web_events_raw`;
- `bronze_access_logs_raw`;
- `bronze_application_logs_raw`;
- `bronze_ingestion_errors`.

### 17.3. Metadata chung

- Bronze record ID;
- source system/entity;
- source primary/business key;
- batch/run ID;
- extracted/received/ingested time;
- cursor/cutoff reference;
- schema version;
- raw payload/checksum;
- file/checksum/line offset cho JSONL;
- data origin.

### 17.4. Ingestion error

`bronze_ingestion_errors` dùng cho:

- malformed JSON;
- encoding/framing lỗi;
- unknown file/source;
- thiếu envelope/routing metadata;
- unsupported schema envelope.

Readable record có lỗi nghiệp vụ vẫn vào Bronze chuẩn và được xử lý tại Silver.

### 17.5. Idempotency và partition

- JSONL transport identity: file checksum + byte/line offset.
- MySQL identity: source table + source PK + source version/cursor + extraction unit.
- Intentional replay có replay ID riêng.
- Event/log/error partition theo `ingest_date`.
- Không partition theo UUID, customer hoặc product.

---

## 18. Silver layer

### 18.1. Trách nhiệm

- Parse và cast kiểu dữ liệu.
- Chuẩn hóa timestamp về UTC.
- Validate key, status, amount và enum.
- Deduplicate transport và event duplicate.
- Merge current-state entity.
- Giữ append-only business history.
- Tích hợp order, payment và inventory.
- Derive canonical business events từ OLTP.
- Sessionize clickstream với timeout 30 phút.
- Parse access/application logs.
- Tokenize hoặc bỏ PII không cần thiết.
- Ghi quarantine và DQ result.

### 18.2. Silver domain tables

- `silver_customers`;
- `silver_categories`;
- `silver_products`;
- `silver_product_variants`;
- `silver_carts`, `silver_cart_items`;
- `silver_orders`, `silver_order_items`;
- `silver_payments`;
- `silver_order_status_history`;
- `silver_inventory`.

### 18.3. Silver integration/quality tables

- `silver_web_events_clean`;
- `silver_business_events`;
- `silver_sessions`;
- `silver_request_logs`;
- `silver_order_lifecycle`;
- `silver_data_quarantine`;
- `silver_data_quality_results`.

Silver chỉ chuẩn hóa nguồn; không tính label ML và không ghi model score. Feature/label được dựng từ Gold để tái sử dụng fact/dimension đã đối soát.

### 18.4. Late-arriving data

- Lưu event time và received time.
- Scheduled run dùng configurable lookback window.
- Late event trong lookback được merge/deduplicate lại.
- Event quá lookback vẫn được ingest và gắn `is_late`.
- Affected Gold partitions được recompute khi backfill.

### 18.5. Schema evolution scenario

Acceptance gồm một scenario:

- event schema v1 không có `traffic_source`;
- event schema v2 thêm nullable `traffic_source`;
- Bronze giữ cả hai payload/version;
- Silver chuẩn hóa về canonical schema;
- unknown incompatible version vào quarantine;
- record được recover khi parser mới được bổ sung và replay.

---

## 19. Gold layer

### 19.1. Dimensions

| Table | Grain |
|---|---|
| `dim_date` | Một calendar date |
| `dim_customer` | Một pseudonymized customer |
| `dim_category` | Một category |
| `dim_product` | Một product |
| `dim_product_variant` | Một variant |
| `dim_device` | Một normalized device class |

### 19.2. Facts

| Table | Grain |
|---|---|
| `fact_event` | Một valid clickstream/canonical business event |
| `fact_session` | Một derived analytics session |
| `fact_order` | Một order |
| `fact_order_item` | Một variant line/order |
| `fact_payment` | Một payment/order |
| `fact_inventory_daily_snapshot` | Một variant/cuối ngày |

### 19.3. Marts

| Mart | Grain | Nội dung |
|---|---|---|
| `mart_sales_daily` | Một business date | Paid orders, revenue, units, AOV |
| `mart_funnel_daily` | Date × device | Session, view, cart, checkout, paid funnel |
| `mart_product_daily` | Date × product/variant | Views, cart additions, paid units, revenue |
| `mart_inventory_daily` | Snapshot date × variant | Opening stock, on-hand, sold units và low-stock status |

Mỗi fact/mart document grain, source, filters, cutoff, refresh và reconciliation rule.

### 19.4. ML datasets

| Table | Grain | Vai trò |
|---|---|---|
| `gold_customer_repurchase_features` | Customer × `as_of_date` × feature schema version | Point-in-time feature snapshot |
| `gold_customer_repurchase_training` | Customer × `as_of_date` × label horizon | Features + eligibility + `repurchased_30d` |
| `gold_customer_repurchase_predictions` | Customer × score date × model version | Probability, threshold decision và score band |

Các bảng ML là dữ liệu dẫn xuất. Có thể rebuild từ Gold facts/dimensions, cutoff manifest, ML config và model artifact; không ghi prediction ngược vào OLTP.

---

## 20. KPI, dashboard và Machine Learning

### 20.1. Sales KPI

- `paid_order_count`.
- `gross_collected_revenue` từ succeeded payments.
- `sold_units` từ order items của paid orders.
- `AOV = gross_collected_revenue / paid_order_count`.

### 20.2. Funnel KPI

- Sessions.
- Product-view sessions.
- Add-to-cart sessions.
- Checkout sessions.
- Paid orders có thể liên kết.
- View-to-cart rate.
- Cart-to-checkout rate.
- Checkout-to-paid rate.

Funnel ghi rõ clickstream coverage.

### 20.3. Product/inventory KPI

- Product views.
- Add-to-cart count.
- Paid units.
- Revenue/product.
- Current `on_hand`.
- `opening_on_hand`.
- Sold units từ order items có succeeded payment.
- Low-stock theo configured threshold.

### 20.4. Ý nghĩa bài toán ML

Repurchase prediction trả lời câu hỏi: trong nhóm customer đã từng mua, ai có khả năng phát sinh paid order mới trong 30 ngày tới?

Kết quả có thể dùng để:

- ước lượng quy mô nhóm customer có khả năng quay lại;
- chia propensity band phục vụ phân tích retention/cross-sell;
- ưu tiên nhóm để phân tích hoặc thử nghiệm chiến dịch sau này;
- chứng minh Gold data có thể phục vụ workload dự đoán ngoài dashboard mô tả.

Model chỉ tạo propensity score, không chứng minh một can thiệp marketing sẽ gây ra repurchase.

### 20.5. Population, observation và prediction horizon

- **Prediction unit:** một `customer_key` đã pseudonymize tại một `as_of_date`.
- **Eligible customer:** có ít nhất một succeeded payment trước hoặc tại `as_of_time` và có đủ định danh để liên kết order/event.
- **Observation window chính:** 180 ngày kết thúc tại `as_of_time`; một số feature có thêm cửa sổ 30 và 90 ngày.
- **Prediction horizon:** `(as_of_time, as_of_time + 30 ngày]`.
- **Historical snapshots:** tạo tại cuối mỗi tháng; các label window không được dùng làm feature cho chính row đó.
- **Scoring population:** eligible customer tại Gold publication mới nhất; scoring row không có label cho đến khi horizon đóng.

Customer chưa từng mua thuộc bài toán first-purchase conversion, không nằm trong population này.

### 20.6. Label contract

`repurchased_30d = 1` khi customer có ít nhất một `payments.status = succeeded` với `attempted_at` nằm trong prediction horizon; ngược lại bằng 0 khi horizon đã đóng đầy đủ.

Quy tắc:

- dùng payment succeeded/order paid làm nguồn chính thức, không dùng clickstream checkout;
- order `payment_failed` không tạo positive label;
- chỉ đưa row có horizon đã đóng vào training/evaluation;
- label gắn `label_window_start`, `label_window_end`, Gold publication và code/config version;
- late correction/backfill làm affected label partition được rebuild và version lại;
- không dùng order completion sau `as_of_time` làm feature vì nó có thể tiết lộ tương lai.

### 20.7. Feature contract

Feature tối thiểu, đều được tính chỉ từ dữ liệu khả dụng tại `as_of_time`:

**Purchase/RFM**

- `days_since_last_paid_order`;
- `paid_order_count_30d`, `paid_order_count_90d`, `paid_order_count_180d`;
- `paid_revenue_30d`, `paid_revenue_90d`, `paid_revenue_180d`;
- `avg_order_value_180d`;
- `paid_units_180d`;
- `distinct_category_count_180d`;
- `days_between_last_two_paid_orders`, nullable khi chưa đủ hai order.

**Behavior**

- `session_count_30d`;
- `product_view_count_30d`;
- `add_to_cart_count_30d`;
- `begin_checkout_count_30d`;
- `days_since_last_session`;
- `view_to_cart_ratio_30d`, có quy tắc chia cho 0 rõ ràng.

**Checkout/payment quality**

- `payment_failed_count_90d`;
- `checkout_to_paid_ratio_90d`;
- `days_since_first_paid_order`.

Không dùng email, tên, phone, address, raw public UUID, future order, future event, current label hoặc latent generator segment làm feature.

Với clickstream, point-in-time availability yêu cầu cả `event_time <= as_of_time` và `collector_received_time <= as_of_time`. Feature missing do clickstream best-effort được điền theo rule cố định và có missingness/coverage report.

### 20.8. Leakage prevention và split

- Split theo `as_of_date`, không dùng random row split.
- Train dùng các snapshot cũ nhất; validation dùng giai đoạn kế tiếp; test dùng giai đoạn mới nhất.
- Label window của train phải kết thúc trước validation period; label window của validation phải kết thúc trước test period.
- Preprocessing statistics chỉ fit trên train rồi áp dụng cho validation/test.
- Threshold/hyperparameter chọn trên validation; test chỉ đánh giá một lần cho báo cáo cuối.
- Feature query có explicit upper bound theo event/business time và input Gold publication.
- Mỗi row lưu `feature_max_source_time`; DQ yêu cầu giá trị này không vượt `as_of_time`.
- Không dùng current customer status hoặc current master value nếu không tái dựng được đúng tại historical `as_of_time`.

### 20.9. Model và preprocessing

1. `DummyClassifier` theo class prior làm baseline bắt buộc.
2. Logistic Regression là mô hình chính:
   - median imputation cho numerical missing;
   - standardization cho feature cần thiết;
   - class weight chỉ dùng khi được chọn từ validation;
   - coefficient được báo cáo để giải thích chiều ảnh hưởng, không diễn giải nhân quả.
3. `RandomForestClassifier` cấu hình nhỏ là mô hình so sánh tùy thời gian; không mở rộng sang XGBoost/deep learning trong TLCN.

Preprocessing và classifier được đóng thành một scikit-learn `Pipeline` để training/scoring dùng cùng logic.

### 20.10. Evaluation

Metrics bắt buộc:

- positive rate theo split;
- PR-AUC là metric chính khi class imbalance;
- ROC-AUC;
- precision, recall và F1 tại threshold chọn trên validation;
- confusion matrix;
- Brier score và calibration plot;
- Precision@Top-20% hoặc Lift@Top-20% cho use case xếp hạng.

Phải so với Dummy baseline. Nếu model không vượt baseline, báo cáo trung thực kết quả, phân tích dữ liệu/feature và không claim model có giá trị dự đoán.

Không chọn model chỉ theo test score. Báo cáo mean/variance qua một số seed cố định nếu thời gian cho phép, nhưng temporal holdout cuối vẫn là kết quả chính.

### 20.11. Artifact, scoring và serving

Mỗi accepted training run lưu trên MinIO:

- serialized preprocessing + model artifact;
- `model_version`;
- training Gold publication/dataset checksum;
- feature schema version và ordered feature list;
- train/validation/test date ranges;
- algorithm, hyperparameter và random seed;
- threshold và score-band boundaries;
- metrics/confusion matrix/calibration data;
- code/config version;
- created time và run ID.

Prediction output bắt buộc có:

- pseudonymous customer key;
- `score_date`/`as_of_time`;
- `repurchase_probability_30d` trong `[0,1]`;
- predicted class tại frozen threshold;
- propensity band `low`, `medium`, `high` theo configured boundaries;
- model version, feature schema version và Gold publication;
- scored time.

MySQL `analytics.customer_repurchase_scores` chỉ giữ dữ liệu pseudonymized cần cho BI. Model artifact không commit vào Git và không dùng MLflow.

### 20.12. Dashboard layout

Một Superset dashboard gồm năm khu vực:

1. Sales overview.
2. Funnel overview.
3. Product performance.
4. Inventory status.
5. Repurchase propensity: eligible customers, score distribution, propensity bands và realized 30-day rate cho các historical snapshots đã đóng label.

Superset chỉ đọc MySQL `analytics`.

---

## 21. Data quality và quarantine

### 21.1. Bronze technical checks

- File checksum/size/record count.
- Parse success/failure.
- Required envelope metadata.
- Supported schema version.
- Duplicate transport identity.

### 21.2. Silver semantic checks

- PK/business key not null và unique.
- FK reference tồn tại.
- Valid enum/status.
- Price, amount và quantity có sign hợp lệ.
- Order arithmetic: subtotal + shipping = total.
- Payment amount bằng order total.
- Payment/order status nhất quán.
- Inventory không âm.
- `opening_on_hand >= on_hand >= 0`.
- Event time nằm trong configured validity/skew range.
- Required session/entity references tồn tại.

### 21.3. Gold checks

- Fact grain uniqueness.
- Dimension key coverage.
- Unknown member được dùng có kiểm soát.
- Mart total bằng fact total tại cùng cutoff.
- Paid revenue chỉ lấy payment succeeded.
- Inventory snapshot reconcile với `opening_on_hand`, current `on_hand` và succeeded order items.

### 21.4. ML data checks

- Unique grain `(customer_key, as_of_date, feature_schema_version)`.
- Customer thỏa eligibility và có paid order trước/tại `as_of_time`.
- Training row chỉ tồn tại khi label horizon đã đóng.
- `feature_max_source_time <= as_of_time`.
- Không có PII/raw customer identifier trong feature, label hoặc prediction.
- Feature schema, order và data type khớp model manifest.
- Numerical feature có range/missingness rule; không chứa vô cực ngoài contract.
- Label chỉ nhận `0` hoặc `1`; positive rate được report theo split.
- Probability nằm trong `[0,1]`; mỗi eligible customer/model/score date có tối đa một prediction.
- Training/test date range không overlap trái contract.

ML DQ error chặn training/scoring publication của run đó nhưng không rollback Gold publication. Invalid ML row được ghi vào ML quality report có source Gold reference; không trộn với raw ingestion error.

### 21.5. Quarantine contract

Mỗi row quarantine lưu:

- Bronze/source reference;
- table/file;
- rule/error code;
- offending field và masked value;
- reason;
- batch/run ID;
- schema version;
- quarantined time;
- resolution/replay status.

Severity:

- `error`: chặn affected Gold/publish;
- `warning`: publish và ghi audit;
- `info`: theo dõi.

---

## 22. Reconciliation

Tại cùng cutoff manifest phải đối soát:

1. Source orders ↔ Silver orders ↔ Gold fact orders.
2. Succeeded payment count và amount.
3. Order-item quantity và subtotal.
4. Inventory current source ↔ Silver inventory.
5. Inventory balance: `opening_on_hand - succeeded sold units = on_hand` theo variant.
6. Source/closed-file/Bronze/Silver event counts.
7. Quarantined/rejected counts.
8. Mart sales totals ↔ facts.
9. Eligible customer count ↔ feature row count theo `as_of_date`.
10. Feature rows + excluded rows theo reason ↔ candidate population.
11. Positive label count ↔ customer có succeeded payment trong đúng 30-day horizon.
12. Prediction row count ↔ scoring-eligible customer count của model run.

Integer count và VND amount phải exact.

Mỗi reconciliation result có:

- rule ID;
- source/target;
- cutoff;
- expected/actual/difference;
- severity;
- pass/fail;
- batch/run ID.

---

## 23. Rerun, replay và backfill

### 23.1. Rerun

- Chạy lại cùng run input không thay logical row count hoặc KPI.
- Không nhân business output.
- Publish lại cùng version không tạo duplicate serving row.
- Rerun ML cùng Gold version/config/code/seed không đổi split, feature checksum và prediction ngoài numerical tolerance.

### 23.2. Replay

- Recreate Silver và Gold trong môi trường test.
- Rebuild chỉ từ Bronze và pipeline metadata.
- Kết quả khớp stored row count, checksum và KPI.
- ML feature/label dataset rebuild được từ versioned Gold; scoring rebuild được từ feature snapshot và model artifact.

### 23.3. Backfill

- Nhận source/date hoặc partition range.
- Dùng audit/cursor namespace riêng.
- Recompute affected Silver/Gold partitions.
- Reconcile và publish lại affected analytics range.
- Lưu reason và reference tới original run.

### 23.4. Partial failure

Test failure tại tối thiểu ba điểm:

- sau Bronze trước Silver;
- sau Silver trước Gold;
- sau Gold trước cursor commit.

Sau retry/rerun, output cuối tương đương clean successful run.

---

## 24. Pipeline audit và observability

Các bảng metadata:

- `pipeline_runs`;
- `pipeline_source_runs`;
- `pipeline_task_metrics`;
- `data_quality_results`;
- `reconciliation_results`;
- `dataset_publications`;
- `ml_training_runs`;
- `ml_scoring_runs`;
- `ml_artifact_manifests`.

Mỗi run lưu:

- pipeline/run/batch ID;
- logical date;
- cursor start/end;
- cutoff manifest;
- source/files read;
- rows read/written/rejected/quarantined;
- duration từng stage;
- status/error;
- code/config version;
- retry/replay/backfill reference;
- published dataset version.

ML run bổ sung:

- input Gold publication và feature dataset checksum;
- feature schema/model version;
- split date ranges và seed;
- row/class counts theo split;
- metrics, selected threshold và evaluation status;
- artifact path/checksum;
- scoring output version và prediction count.

Pipeline health được trình bày bằng audit queries/report.

---

## 25. Analytics publish

```text
Gold mart
→ analytics staging
→ schema/count/reconciliation validation
→ atomic swap hoặc idempotent upsert
→ serving tables
```

Publish requirements:

- staging run có batch/version ID;
- validation chạy trước serving switch;
- failed validation giữ serving version cũ;
- rerun không tạo duplicate;
- publish audit lưu source Gold version và timestamp.
- repurchase score dùng staging riêng và chỉ publish khi schema, row count, probability range, uniqueness và artifact reference hợp lệ.
- failed ML publish giữ score/model serving version trước; không ảnh hưởng sales/funnel marts.

---

## 26. Performance experiment

Chạy controlled local experiment với ba dataset sizes:

- small: khoảng 10 nghìn records;
- medium: khoảng 100 nghìn records;
- large-local: khoảng 1 triệu records nếu máy đáp ứng.

Ghi nhận:

- total DAG duration;
- duration theo stage;
- rows/second;
- Bronze/Silver/Gold output size;
- số file/partition;
- peak memory quan sát được;
- rerun duration;
- replay duration;
- ảnh hưởng của partition strategy.
- feature-build duration và output size;
- training duration theo model;
- batch-scoring rows/second và peak memory;
- model artifact size.

---

## 27. Testing strategy

### 27.1. Source tests

- Register/login.
- Catalog/product detail.
- Cart mutation.
- Successful checkout.
- Failed checkout.
- Last-item concurrent checkout.
- Order completion.
- Event/log contract.

### 27.2. Ingestion tests

- Initial load.
- Incremental rows cùng timestamp khác PK.
- Mutable row update.
- Duplicate closed file.
- Closed file và file đang mở.
- Malformed JSON.
- Retry trước/sau cursor commit.

### 27.3. Transformation tests

- Cast/timezone.
- Dedup.
- Current-state merge.
- Append-only history.
- Late event/lookback.
- Sessionization.
- Schema v1/v2.
- Unknown schema quarantine.
- Fact/dimension grain.

### 27.4. Correctness tests

- DQ severity behavior.
- Source-to-Silver-to-Gold reconciliation.
- Inventory balance từ opening stock và succeeded order items.
- Exact VND amount.
- Rerun idempotency.
- Bronze replay.
- Date-range backfill.
- Staging publish safety.

### 27.5. Reproducibility tests

- Clean machine/clean volumes.
- Same seed và config.
- Same code/config và Bronze snapshot.
- Stored manifest/checksum comparison.
- Cả hai thành viên chạy được demo từ runbook.

### 27.6. ML tests

- Label boundary: payment đúng trước, tại và sau 30-day horizon.
- Eligible/non-eligible customer.
- Feature window upper bound và `feature_max_source_time`.
- Late event có received time sau `as_of_time` không lọt vào historical feature.
- Temporal split và purge giữa label windows.
- Preprocessing chỉ fit trên train.
- Feature schema/order khớp artifact khi scoring.
- Dummy baseline, Logistic Regression và optional Random Forest chạy reproducibly.
- Probability range, unique prediction grain và score-band mapping.
- Cùng artifact + feature snapshot tạo cùng prediction trong tolerance.
- PII không xuất hiện trong feature, artifact metadata hoặc serving score.

---

## 28. Security và privacy

- Password hash nằm ở `customer_credentials` và không extract.
- Event/log không chứa secret, token hoặc raw PII.
- Customer dimension dùng pseudonymous key.
- Shipping address không đưa vào Gold analytics.
- `.env` không commit.
- MinIO, MySQL, Superset và Airflow dùng credential riêng.
- Serving tables không chứa email, phone hoặc address.
- ML feature/prediction chỉ dùng pseudonymous customer key; model artifact không chứa raw training PII.
- Synthetic data được dùng cho demo công khai.

---

## 29. Repository structure

```text
apps/storefront
services/ecommerce-api
services/event-collector
database/{migrations,seeds,init}
generator/{configs,master,historical,behavior,repurchase,fixtures}
pipelines/batch/{extract,bronze,silver,gold,publish,reconcile,backfill}
ml/repurchase/{features,labels,training,scoring,configs,reports}
airflow/{dags,config}
quality/{rules,fixtures,reports}
dashboards/business-overview
infrastructure/{docker,minio,spark,airflow,superset,mysql}
tests/{unit,integration,data,e2e}
docs/{architecture,source-contracts,event-catalog,data-dictionary,kpi,runbook,thesis}
docker-compose.yml
.env.example
Makefile
README.md
```

---

## 30. Phân công hai người

### Người A — Source và Ingestion

- Website/API tối giản.
- OLTP migrations/seeds.
- Event Collector và log contract.
- Generator/failure fixtures.
- MySQL extraction và JSONL discovery.
- Cutoff manifest, cursor và Bronze.
- Source reconciliation queries.
- Repurchase generator scenario, expected label/class manifest và ML source-quality fixtures.
- Dummy baseline, Logistic Regression experiment và model evaluation report.

### Người B — Transformation và Analytics

- Docker platform, MinIO, Spark, Delta và Airflow.
- Silver domain/events/logs.
- DQ và quarantine.
- Gold facts/dimensions/marts.
- Reconciliation và analytics publish.
- Superset dashboard và performance report.
- Point-in-time feature/label jobs, artifact manifest, batch scoring và score publish.

### Làm chung

- Freeze source/event/schema/KPI contracts.
- Review grain và time semantics.
- Freeze ML population/label/feature/leakage contract và review temporal split.
- Rerun/replay/backfill tests.
- Clean-environment rehearsal.
- Báo cáo và demo.

Sau tuần 3, cả hai thành viên tập trung chủ yếu vào Data Engineering.

---

## 31. Roadmap 10 tuần

| Tuần | Người A | Người B | Gate |
|---:|---|---|---|
| 1 | Source flow, schema, event contract | Architecture, RQ, KPI/ML target/grain, Delta PoC | Freeze contracts |
| 2 | Migration/seed, auth/catalog/cart | Compose, MinIO/Spark/Airflow | Source + platform foundation |
| 3 | Checkout, Collector, generator + repurchase scenario | JSONL/MySQL ingestion PoC | Source application hoàn tất |
| 4 | Incremental extraction, manifest, Bronze | Bronze tables, audit và validation | Initial/incremental stable |
| 5 | Source fixes và failure fixtures | Silver domain/events/logs, dedup | Silver rebuildable |
| 6 | Source reconciliation và ML population fixtures | DQ, quarantine, late data, schema evolution | Quality gate stable |
| 7 | Backfill/replay support | Gold facts/dimensions/marts + ML feature/label | Gold/ML grains accepted |
| 8 | Train/evaluate model và source runbook | Artifact/score publish, dashboard, performance | End-to-end analytics + ML |
| 9 | E2E/failure/reproducibility tests | Rerun/replay/backfill/reconcile + ML tests | Clean-run rehearsal |
| 10 | Bug fix, report, slide, demo | Bug fix, report, fallback dataset | Final |

---

## 32. Milestones

### M0 — Scope và contract freeze, cuối tuần 1

- RQ và acceptance matrix.
- OLTP schema.
- Event catalog.
- Source/cursor/cutoff contracts.
- Bronze/Silver/Gold grain catalogue.
- DQ/reconciliation matrix.
- Repurchase population, label, feature, temporal split và evaluation contract.

### M1 — Source và platform, cuối tuần 3

- Website source flow hoàn chỉnh.
- Collector/JSONL rotation.
- Reproducible generator.
- MySQL, MinIO, Spark và Airflow chạy được.
- Generator có repurchase history và expected class manifest.

### M2 — Ingestion, cuối tuần 4

- Initial/incremental MySQL.
- Closed JSONL ingestion.
- Bronze/audit/cursor.
- Rerun ingestion ổn định.

### M3 — Silver và quality, cuối tuần 6

- Silver domain/events/logs.
- Dedup/sessionization.
- DQ/quarantine.
- Late event/schema evolution.
- Rebuild từ Bronze.

### M4 — Analytics product, cuối tuần 8

- Gold facts/dimensions/marts.
- Reconciliation.
- Analytics publish.
- Dashboard.
- Performance report.
- Point-in-time repurchase dataset.
- Baseline/model evaluation, versioned artifact và batch score publish.

### M5 — Final, cuối tuần 10

- Failure recovery.
- Replay/backfill.
- Clean setup.
- Runbook, report, slide và demo.

---

## 33. Deliverables

### 33.1. Source system

1. Minimal Next.js storefront.
2. Minimal FastAPI ecommerce API.
3. MySQL OLTP migrations/seeds.
4. JSONL Event Collector.
5. Reproducible data generator.

### 33.2. Data platform

1. Docker Compose profiles.
2. Airflow DAGs.
3. Initial/incremental extraction.
4. Cutoff/file manifests.
5. Bronze Delta tables.
6. Silver Delta tables.
7. Gold facts/dimensions/marts.
8. DQ/quarantine framework.
9. Reconciliation jobs.
10. Replay và backfill jobs.
11. Pipeline audit metadata.
12. Analytics staging/publish.
13. Superset dashboard.
14. Point-in-time ML feature/label datasets.
15. Repurchase training/evaluation/scoring jobs.
16. Versioned model artifact và ML run manifests.
17. Pseudonymized repurchase score serving table/dashboard panel.

### 33.3. Tài liệu và reports

1. Architecture diagram.
2. Source schema và data dictionary.
3. Source/cursor/cutoff contract.
4. Event/log contract.
5. Bronze/Silver/Gold catalogue.
6. Fact/mart grain catalogue.
7. DQ/quarantine rules.
8. Reconciliation matrix.
9. Rerun/replay/backfill report.
10. Schema evolution/late-event report.
11. Performance/resource report.
12. README, setup và runbook.
13. TLCN report, slide và demo script.
14. ML population/label/feature data contract.
15. Leakage prevention và temporal split report.
16. Baseline/model evaluation, calibration và limitation report.
17. Model artifact/scoring runbook.

---

## 34. Acceptance criteria

### 34.1. Website/source

- Login, catalog, cart và checkout chạy được.
- Success checkout tạo paid order/payment, order items và giảm inventory atomically.
- Failed checkout không trừ inventory.
- Concurrent last-item checkout không làm inventory âm.
- Collector tạo event đúng contract.
- Generator tạo lại cùng logical dataset bằng cùng seed.

### 34.2. Ingestion/Bronze

- Initial và incremental không miss same-timestamp rows.
- Pipeline chỉ ingest closed JSONL files.
- Duplicate file/record không nhân transport row ngoài contract.
- Bronze giữ raw payload và source duplicate.
- Malformed record vào ingestion error đúng loại.
- Cursor chỉ commit sau full success.

### 34.3. Silver/quality

- Silver rebuild được từ Bronze.
- Dedup rule deterministic.
- Late event được flag và cập nhật affected output đúng.
- Schema v1/v2 cùng được chuẩn hóa.
- Unknown version vào quarantine và replay được sau khi thêm parser.
- Semantic invalid record được xử lý tại Silver quarantine.

### 34.4. Gold/BI

- Mỗi fact, dimension và mart có grain/source/formula/cutoff.
- Paid revenue khớp succeeded payments.
- Sold units khớp order items của paid orders.
- Inventory snapshot khớp `opening_on_hand`, succeeded order items và current `on_hand`.
- Dashboard chỉ đọc MySQL analytics.

### 34.5. Rerun/replay/backfill

- Rerun cùng input không đổi logical output/KPI.
- Replay Bronze tạo lại Silver/Gold tương đương.
- Backfill chỉ thay affected range.
- Partial failure trước cursor commit recover được.
- Publish không để serving ở trạng thái nửa hoàn thành.

### 34.6. Reproducibility

- Dựng được từ clean volumes.
- Cả hai thành viên chạy được hệ thống theo runbook.
- New checkout xuất hiện trong dashboard sau một DAG run.
- Có fallback dataset và manifests cho demo.

### 34.7. Machine Learning

- Training dataset có grain `customer × as_of_date`, stable key và version rõ.
- Label 30 ngày khớp succeeded payment trong đúng horizon.
- Feature query pass point-in-time/leakage tests.
- Train/validation/test split theo thời gian và preprocessing chỉ fit trên train.
- Dummy baseline và Logistic Regression luôn được đánh giá; optional Random Forest không làm tăng scope nếu thiếu thời gian.
- Báo cáo PR-AUC, ROC-AUC, threshold metrics, confusion matrix, Brier/calibration và ranking metric.
- Nếu model không vượt baseline thì kết luận đúng giới hạn, không chọn lại test set hoặc che giấu kết quả.
- Artifact manifest đủ để load model và tái tạo batch prediction.
- Prediction unique theo customer/score date/model, probability hợp lệ và không chứa PII.
- ML run failure không ảnh hưởng core Gold/BI publication.

---

## 35. Demo end-to-end

1. Khởi động `core`, `batch`, `bi`.
2. Seed catalog/inventory.
3. Login, view product, add cart và checkout.
4. Kiểm tra MySQL order/payment và inventory trước/sau checkout.
5. Kiểm tra Collector đóng JSONL file.
6. Chạy Airflow DAG.
7. Trình bày cutoff manifest và pipeline audit.
8. Xem raw record trong Bronze.
9. Xem deduplicated/normalized record trong Silver.
10. Trình bày malformed record ở ingestion error.
11. Trình bày readable invalid record ở Silver quarantine.
12. Xem Gold facts/marts và reconciliation result.
13. Xem dashboard Superset.
14. Xem một ML row và chứng minh feature chỉ dùng dữ liệu trước `as_of_time`.
15. Trình bày temporal split, baseline/model metrics và artifact manifest.
16. Batch-score eligible customers và xem repurchase propensity trên Superset.
17. Rerun cùng batch/ML input để chứng minh idempotency và reproducibility.
18. Replay hoặc backfill một ngày để chứng minh recoverability.

---

## 36. Cấu trúc báo cáo

### Chương 1 — Giới thiệu

Bối cảnh, vấn đề, câu hỏi nghiên cứu, mục tiêu, phạm vi và đóng góp.

### Chương 2 — Cơ sở lý thuyết

OLTP/OLAP, batch processing, Lakehouse, Delta, medallion, incremental cursor, idempotency, data quality, reconciliation, dimensional modeling, binary classification, temporal validation, class imbalance, calibration và data leakage.

### Chương 3 — Phân tích và thiết kế

Source system, data contracts, architecture, cutoff, metadata, Bronze/Silver/Gold, grain, DQ, reconciliation và ML population/label/feature contract.

### Chương 4 — Triển khai

Website/API source, Collector, generator, Airflow, Spark, Delta, MinIO, transformations, publish, Superset và repurchase training/scoring pipeline.

### Chương 5 — Thử nghiệm và đánh giá

Initial/incremental, rerun, replay, backfill, failure recovery, late data, schema evolution, quarantine, reconciliation, performance, reproducibility, temporal ML evaluation, calibration và leakage tests.

### Chương 6 — Kết luận

Trả lời câu hỏi nghiên cứu, giới hạn của môi trường batch/local/synthetic và hướng phát triển.

---

## 37. Risks và kiểm soát scope

| Rủi ro | Biện pháp |
|---|---|
| Source website chậm hoàn thành | Hoàn tất và freeze source flow cuối tuần 3 |
| Generator không tái lập | Seed, version, anchor time và expected manifest |
| Incremental miss row | Composite cursor, lookback và same-time tests |
| Rerun nhân dữ liệu | Deterministic transport/business identity |
| Bronze không replay được | Raw payload, schema version và metadata đầy đủ |
| DQ/quarantine chồng chéo | Tách technical ingestion error và semantic quarantine |
| Gold sai nhưng serving vẫn cập nhật | Reconciliation gate trước publish |
| Backfill phá scheduled cursor | Cursor namespace và audit riêng |
| Thiếu tài nguyên local | Docker profiles và ba dataset sizes |
| Demo phụ thuộc dữ liệu live | Fallback dataset, manifests và clean rehearsal |
| ML làm loãng trọng tâm DE | Chỉ một bài toán nhị phân, model nhẹ, feature build và reproducibility mới là trọng tâm |
| Target leakage | Point-in-time feature contract, upper-bound tests và temporal split có purge |
| Positive class quá ít/nhiều | Generator class manifest, PR-AUC, class-weight validation và ranking metric |
| Synthetic pattern quá dễ | Latent segment không xuất ra source, thêm noise và so sánh theo temporal holdout |
| Model không vượt baseline | Báo cáo trung thực, phân tích data/feature; không tuning trên test |

Các thành phần ưu tiên bảo vệ trong lịch thực hiện:

- initial và incremental ingestion;
- cutoff manifest và cursor safety;
- Bronze/Silver/Gold;
- DQ, ingestion error và quarantine;
- rerun, replay và backfill;
- late event và schema evolution scenario;
- reconciliation;
- analytics publish;
- reproducible generator và clean demo.
- point-in-time ML feature/label dataset;
- baseline/model evaluation và artifact reproducibility.

---

## 38. Checklist

### Source application

- [ ] Auth tối thiểu.
- [ ] Catalog/product/variant.
- [ ] Authenticated cart.
- [ ] Checkout/payment result.
- [ ] Inventory opening/current balance.
- [ ] Collector/logging/generator.

### Ingestion

- [ ] Source catalogue.
- [ ] Cursor/cutoff contract.
- [ ] Closed-file manifest.
- [ ] Initial load.
- [ ] Incremental load.
- [ ] Pipeline audit.
- [ ] Bronze raw/error.

### Transformation và quality

- [ ] Silver domain.
- [ ] Silver events/session/logs.
- [ ] Dedup/current-state/history.
- [ ] Late data.
- [ ] Schema evolution.
- [ ] DQ/quarantine.
- [ ] Reconciliation.

### Analytics và operations

- [ ] Gold facts/dimensions/marts.
- [ ] Analytics staging/publish.
- [ ] Superset dashboard.
- [ ] Rerun.
- [ ] Replay.
- [ ] Backfill.
- [ ] Performance report.
- [ ] Clean-run/runbook/demo.

### Machine Learning

- [ ] Repurchase population/label/feature contract.
- [ ] Rolling point-in-time snapshots.
- [ ] Leakage và temporal-split tests.
- [ ] Dummy baseline và Logistic Regression.
- [ ] Optional Random Forest comparison.
- [ ] Evaluation/calibration/ranking report.
- [ ] Versioned model artifact/manifest.
- [ ] Batch scoring và prediction DQ.
- [ ] Repurchase serving table/dashboard panel.
- [ ] ML rerun/reproducibility test.
