# Phạm vi TLCN — E-commerce Batch Data Lakehouse

## 0. Trạng thái và nguồn yêu cầu

Tài liệu này là nguồn yêu cầu hiện hành, ưu tiên cao nhất cho phạm vi Tiểu luận chuyên ngành (TLCN).

Quyết định kiến trúc cập nhật ngày 2026-08-07:

- TLCN sử dụng hai nguồn chính thức: 16 bảng MySQL OLTP và structured web access log.
- Access log được rotate/nén theo micro-batch 15 phút; clickstream event vẫn để ngoài TLCN.
- Apache Iceberg thay Delta Lake làm table format.
- Apache Polaris quản lý catalog; Trino là query layer cho Superset.
- [`lakehouse-plan.md`](lakehouse-plan.md) là kế hoạch Lakehouse chi tiết.
- [`../architecture/oltp-schema.md`](../architecture/oltp-schema.md) là logical schema OLTP chi tiết.
- [`web-plan.md`](web-plan.md) là kế hoạch triển khai source website tạo dữ liệu OLTP.
- [`../../skills/oltp-design/SKILL.md`](../../skills/oltp-design/SKILL.md) là nguyên tắc thiết kế tham khảo.

---

## 1. Tên đề tài

> Xây dựng Data Lakehouse xử lý theo lô cho dữ liệu OLTP và access log của website thương mại điện tử, phục vụ phân tích và dự đoán khả năng khách hàng mua lại.

Tên rút gọn:

> TLCN E-commerce Batch Data Lakehouse.

---

## 2. Bối cảnh và vấn đề

Website thương mại điện tử phát sinh dữ liệu giao dịch trong MySQL như customer, catalog, wishlist, cart, order, payment và inventory; đồng thời phát sinh access log về route, status code, latency, search/filter request và product request.

Nếu truy vấn phân tích trực tiếp trên primary OLTP sẽ:

- cạnh tranh tài nguyên với nghiệp vụ web;
- khó giữ snapshot lịch sử;
- khó chạy lại pipeline;
- khó đối soát dữ liệu theo cùng cutoff;
- làm tăng rủi ro ảnh hưởng transaction.

TLCN xây dựng pipeline batch để trích xuất MySQL và gom access log vào MinIO, quản lý Bronze–Silver–Gold bằng Iceberg/Polaris, xử lý bằng Spark và phục vụ Superset qua Trino mà không chạy analytics nặng trên OLTP.

Website chỉ là source application tối giản. Trọng tâm chính là Data Engineering trên dữ liệu OLTP và access log có contract rõ ràng.

---

## 3. Câu hỏi nghiên cứu

- **RQ1:** Trích xuất initial và incremental từ các bảng OLTP sang Lakehouse theo lô như thế nào mà không miss hoặc duplicate logical row?
- **RQ2:** Thu gom log rotate theo micro-batch như thế nào để không bỏ sót hoặc ingest trùng source file/request?
- **RQ3:** Thiết kế Bronze–Silver–Gold Iceberg cho dữ liệu OLTP mutable và access log append-only như thế nào?
- **RQ4:** Kiểm tra chất lượng, quarantine và đối soát hai nguồn tới Gold như thế nào?
- **RQ5:** Rerun, replay và backfill như thế nào mà không làm sai row count hoặc KPI?
- **RQ6:** Khi nào cần compact small files và làm sao chứng minh maintenance không thay đổi kết quả logic?
- **RQ7:** Mô hình fact/dimension nào phục vụ nghiệp vụ, web traffic/performance và ML mua lại?

---

## 4. Mục tiêu

### 4.1. Mục tiêu tổng quát

Xây dựng hệ thống Data Lakehouse xử lý theo lô cho MySQL OLTP và structured access log, có khả năng:

- initial/incremental extraction;
- log rotation và file-based micro-batch ingestion;
- lưu raw snapshot có lineage;
- chuẩn hóa và tích hợp dữ liệu;
- kiểm tra chất lượng và quarantine;
- xây dựng facts, dimensions và marts;
- đối soát source-to-target;
- rerun, replay và backfill;
- publish dữ liệu cho dashboard;
- query Iceberg qua Polaris/Trino;
- maintenance/compaction theo metric;
- tạo feature/label point-in-time cho ML mua lại.

### 4.2. Năng lực phải chứng minh

1. MySQL OLTP là system of record cho nghiệp vụ; access log là nguồn chính thức cho request behavior/performance.
2. Pipeline đọc OLTP bằng tài khoản read-only và ingest log bằng immutable file identity/checksum.
3. Mỗi bảng/file nguồn có grain, key/identity, mutability và cursor/window rõ ràng.
4. Bronze giữ raw representation và ingestion metadata.
5. Silver typed, deduplicated và tích hợp đúng business rule.
6. Gold có grain rõ và không sao chép schema OLTP một cách máy móc.
7. Pipeline idempotent theo run/input identity.
8. Reconciliation kiểm tra exact count và VND amount.
9. Dữ liệu ML point-in-time không dùng tương lai.
10. Dashboard phải truy vết được về 16 bảng OLTP hoặc access-log interval; ML mua lại chỉ dùng dữ liệu OLTP-derived trong Gold.
11. Spark và Trino phải phân giải cùng Iceberg table qua Polaris.
12. Compaction không được thay đổi row count, checksum hoặc KPI logic.

---

## 5. Phạm vi TLCN

### 5.1. Source website

Website tối giản hỗ trợ:

1. Đăng ký, đăng nhập và đăng xuất.
2. Xem category/product/variant.
3. Search/filter catalog; access log có thể giữ search/filter metadata đã sanitize theo contract.
4. Customer quản lý một wishlist mặc định chứa nhiều product.
5. Customer quản lý active cart.
6. Checkout với địa chỉ nhập trực tiếp.
7. Checkout hợp lệ có thể áp dụng một coupon, tạo order `paid`, payment `succeeded` và giảm inventory atomically.
8. Customer xem order history/detail, hủy order còn `paid` và review item của order `completed`.
9. Admin quản lý catalog, variant, inventory, coupon, review moderation, customer status và lifecycle `paid → confirmed → completed`.
10. Customer/admin hủy order `paid`; hệ thống hoàn inventory, full refund và release coupon atomically.

### 5.2. Nguồn dữ liệu TLCN

Pipeline có hai nguồn: MySQL schema `ecommerce` và structured web access log.

Các bảng được phép extract:

1. `customers`;
2. `categories`;
3. `products`;
4. `product_variants`;
5. `carts`;
6. `cart_items`;
7. `wishlist_items`;
8. `orders`;
9. `order_items`;
10. `payments`;
11. `order_status_history`;
12. `inventory`;
13. `coupons`;
14. `coupon_redemptions`;
15. `refunds`;
16. `product_reviews`.

`customer_credentials` thuộc OLTP nhưng bị loại hoàn toàn khỏi extraction vì chứa email đăng nhập/password hash và không có giá trị phân tích cần thiết.

Access log có grain một HTTP request hoàn tất, tối thiểu gồm `request_id`, thời điểm UTC, service, method, canonical route, status, latency, actor reference nullable, product/search/filter metadata nullable và schema version. Log không chứa password, token, cookie, authorization header, checkout body, email, phone hoặc address nguyên bản.

Log rotate mỗi 15 phút, nén `gzip` và ingest theo immutable source-file checksum. Clickstream frontend/mobile, analytics session, Kafka và CDC streaming nằm ngoài TLCN.

### 5.3. Data Engineering

TLCN bao gồm:

- source catalogue và data contract cho MySQL/access log;
- initial/incremental extraction;
- composite cursor `(timestamp, stable_pk)`;
- source high-watermark/cutoff;
- batch/run manifest;
- immutable Landing cho OLTP extracts và rotated log files;
- Bronze Iceberg cho raw OLTP rows và access logs;
- Silver domain tables;
- Gold facts, dimensions và marts;
- DQ, quarantine và reconciliation;
- rerun, replay và backfill;
- Apache Polaris catalog và Trino serving/query layer;
- Iceberg maintenance theo small-file/snapshot metrics;
- orchestration bằng Airflow;
- transformation bằng Spark/Iceberg trên MinIO.

### 5.4. BI

Dashboard ưu tiên:

- gross collected revenue;
- paid/confirmed/completed/cancelled order count;
- average order value;
- units sold;
- doanh thu theo ngày/category/product;
- customer mới và customer mua hàng;
- cart active/checked-out/abandoned theo định nghĩa OLTP;
- wishlist product popularity từ current/logical wishlist rows;
- inventory current/low-stock;
- tỷ lệ customer mua lại lịch sử;
- batch freshness và DQ status;
- request volume, error rate và latency percentiles;
- top route, product detail request, search và filter usage.

### 5.5. Machine Learning

Bài toán ML:

> Dự đoán khả năng một customer đã từng mua sẽ có thêm ít nhất một succeeded payment trong 30 ngày tiếp theo.

ML chỉ dùng feature từ Gold được suy ra từ OLTP; access log chưa dùng làm feature chính trong TLCN:

- recency, frequency, monetary;
- average basket value và units/order;
- category/product diversity;
- order completion history;
- cart count, checked-out count và abandoned-cart count;
- wishlist current count và product/category diversity;
- customer tenure;
- thời gian từ cart creation đến checkout khi có thể suy ra từ OLTP.


## 6. Nguyên tắc kiến trúc

1. MySQL OLTP là source of truth cho nghiệp vụ; access log là source of record cho HTTP request đã ghi nhận.
2. Iceberg Gold là nguồn phân tích chuẩn sau reconciliation.
3. Polaris là catalog; Spark là writer/transform engine; Trino là read/query engine.
4. Superset chỉ đọc Gold qua Trino; không chạy dashboard query trên primary OLTP.
5. Transaction web không gọi Airflow, Spark, Polaris hoặc Trino.
6. Extractor dùng account read-only và transaction/cutoff ngắn.
7. Mutable OLTP dùng `updated_at + PK`; log append-only dùng source file checksum và `request_id`.
8. Landing/Bronze append-only theo input identity; không overwrite source duplicate.
9. Silver chịu trách nhiệm parse, deduplicate, pseudonymize và merge theo source contract.
10. Gold publish chỉ xảy ra sau quality/reconciliation gate.
11. Mọi amount dùng integer VND; mọi persisted timestamp dùng UTC.
12. Customer PII, raw IP và secret không được xuất hiện trong Silver trusted/Gold/ML.
13. Spark là writer duy nhất cho Iceberg trong TLCN.
14. Maintenance dựa trên metric/threshold và phải bảo toàn logical result.

---

## 7. Tech stack chốt

| Khối | Công nghệ |
|---|---|
| Storefront | Next.js 15, TypeScript |
| Ecommerce API | FastAPI, SQLAlchemy 2, Alembic, Pydantic |
| OLTP | MySQL 8.4, InnoDB |
| Generator | Python 3.11, deterministic config/seed |
| Orchestration | Apache Airflow 2.10 |
| Transform | Apache Spark 3.5, PySpark |
| Table format | Apache Iceberg, runtime tương thích Spark |
| Object storage | MinIO |
| Catalog | Apache Polaris |
| Query/BI serving | Trino |
| Dashboard | Apache Superset |
| ML | pandas, scikit-learn, joblib |
| Dependency | uv workspace + `uv.lock` |
| Runtime | Docker Compose profiles |

MLflow không sử dụng.

---

## 8. Kiến trúc logical

```text
Next.js Storefront
        ↓ HTTP
FastAPI Ecommerce API
        ↓ transaction
MySQL ecommerce (OLTP)
        ↓ read-only initial/incremental batch
MinIO Landing ← structured access log JSONL.gz mỗi 15 phút
        ↓ Spark ingestion
Bronze Iceberg
        ↓ parse / dedup / merge
Silver Iceberg
        ↓ dimensional transformation
Gold Iceberg ←→ Polaris Catalog
        ├──→ Trino → Superset
        └──→ ML feature/label → train/score
```

Docker profiles:

- `core`: MySQL ecommerce, Ecommerce API, Storefront.
- `batch`: MinIO, Spark, Airflow, Polaris và PostgreSQL metadata.
- `bi`: Trino, Superset và PostgreSQL metadata.
- `tools`: deterministic OLTP data generator.

---

## 9. Logical schema OLTP

Logical schema có 17 bảng và được mô tả chi tiết tại [`../architecture/oltp-schema.md`](../architecture/oltp-schema.md).

| Nhóm | Bảng | Grain chính |
|---|---|---|
| Customer | `customers` | Một customer |
| Credential | `customer_credentials` | Một credential/customer; không extract |
| Catalog | `categories` | Một category |
| Catalog | `products` | Một product |
| Catalog | `product_variants` | Một size-color/product |
| Cart | `carts` | Một cart/customer |
| Cart | `cart_items` | Một variant/cart |
| Wishlist | `wishlist_items` | Một product từng wishlist/customer |
| Order | `orders` | Một checkout result |
| Order | `order_items` | Một variant line/order |
| Payment | `payments` | Một payment/order |
| Refund | `refunds` | Một full refund/payment |
| Promotion | `coupons` | Một coupon code |
| Promotion | `coupon_redemptions` | Một redemption/order |
| Review | `product_reviews` | Một review/order item |
| History | `order_status_history` | Một order transition |
| Inventory | `inventory` | Một balance/variant |

Web transaction, constraint, index và concurrency theo [`../architecture/oltp-schema.md`](../architecture/oltp-schema.md); pipeline không được sửa ngược OLTP.

---

## 10. Source contract và extraction

### 10.1. Phân loại nguồn

| Bảng | Mutability | Cursor đề xuất | Silver behavior |
|---|---|---|---|
| `customers` | Mutable | `(updated_at, customer_id)` | Merge current state, anonymize PII |
| `categories` | Mutable | `(updated_at, category_id)` | Merge current state |
| `products` | Mutable/archive terminal | `(updated_at, product_id)` | Merge current state và archive metadata |
| `product_variants` | Mutable | `(updated_at, variant_id)` | Merge current state |
| `carts` | Mutable | `(updated_at, cart_id)` | Merge current state, derive lifecycle fields |
| `cart_items` | Mutable/logical removal | `(updated_at, cart_item_id)` | Merge current state |
| `wishlist_items` | Mutable/logical removal | `(updated_at, wishlist_item_id)` | Merge current state |
| `orders` | Mutable paid→confirmed→completed hoặc paid→cancelled | `(updated_at, order_id)` | Merge current state, preserve timestamps |
| `order_items` | Append-only | `(created_at, order_item_id)` | Insert/dedup |
| `payments` | Append-only | `(created_at, payment_id)` | Insert/dedup |
| `order_status_history` | Append-only | `(created_at, order_status_history_id)` | Insert/dedup |
| `inventory` | Mutable | `(updated_at, variant_id)` | Merge current balance, snapshot downstream |
| `coupons` | Mutable/archive terminal | `(updated_at, coupon_id)` | Merge current configuration/counter và archive metadata |
| `coupon_redemptions` | Mutable | `(updated_at, coupon_redemption_id)` | Merge redeemed/released state |
| `refunds` | Append-only | `(created_at, refund_id)` | Insert/dedup |
| `product_reviews` | Mutable | `(updated_at, review_id)` | Merge moderation state |

### 10.2. Composite cursor

Điều kiện incremental chuẩn:

```sql
WHERE updated_at > :last_timestamp
   OR (updated_at = :last_timestamp AND primary_key > :last_pk)
ORDER BY updated_at, primary_key
```

Append-only table dùng `created_at` hoặc timestamp contract tương ứng.

### 10.3. Batch boundary

Mỗi OLTP run phải:

1. Capture high watermark của từng bảng.
2. Đọc từ committed cursor đến high watermark.
3. Ghi immutable extract vào Landing và hoàn tất manifest.
4. Commit Bronze Iceberg và validate.
5. Build Silver/Gold.
6. Reconcile và publish Gold snapshot.
7. Chỉ commit source cursor sau khi toàn bộ core pipeline thành công.

### 10.4. OLTP source metadata

Mỗi extracted row phải có:

- source system/schema/table;
- source PK/business key;
- source timestamp/cursor;
- extraction run ID;
- extracted/ingested time UTC;
- source high watermark;
- source file và raw row checksum;
- code/config version;
- `data_origin` nếu nguồn có trường này.

### 10.5. Access-log contract

Một access-log row có grain một HTTP request hoàn tất. Các trường tối thiểu gồm:

- unique `request_id`;
- `occurred_at_utc`, service, method và canonical route;
- `status_code` và `latency_ms`;
- actor type/reference nullable;
- product/search/filter metadata nullable;
- user-agent/client family;
- schema version, source file và emitted time.

Log rotate mỗi 15 phút, nén `gzip`, đặt vào `landing/logs/date=YYYY-MM-DD/hour=HH/window_start=<timestamp>/` và deduplicate theo source-file checksum cùng `request_id`. Password, token, cookie, authorization header, request body nhạy cảm và PII nguyên bản bị cấm. Chi tiết tại [`lakehouse-plan.md`](lakehouse-plan.md).

---

## 11. Synthetic OLTP generator

Generator phục vụ khối lượng dữ liệu, edge case và reproducibility.

Modes TLCN:

- `seed_master`: category, product, variant, opening inventory.
- `historical_transactions`: customer, cart, order, order item, payment, status history, inventory change.
- `repurchase_history`: lịch sử tối thiểu 12 tháng và rolling customer behavior từ OLTP.


Mỗi run có `scenario_id`, seed, anchor time, scale, generator version và logical identity. Cùng config/seed phải tạo cùng logical dataset. Generator phải xuất được file SQL import trực tiếp vào MySQL trong một transaction, giữ FK/CHECK và fail-fast khi import trùng. Phân phối dùng múi giờ nghiệp vụ `Asia/Ho_Chi_Minh` nhưng lưu UTC; dữ liệu có quan hệ giữa ngày sale/khung giờ 0h, segment khách, coupon, cancellation, review và wishlist conversion thay vì random độc lập.

---

## 12. Airflow DAG catalogue

### 12.1. `ingest_oltp_batch`

```text
check_mysql
→ capture_high_watermarks
→ extract_tables_to_landing
→ validate_landing_manifests
→ append_bronze_oltp
→ validate_bronze_oltp
→ build_silver_oltp
→ run_silver_oltp_dq
→ publish_oltp_interval
```

### 12.2. `ingest_access_logs`

Schedule mặc định mỗi 15 phút:

```text
discover_closed_log_files
→ verify_file_checksum
→ copy_to_landing
→ write_log_manifest
→ append_bronze_access_logs
→ parse_and_dedup_silver_logs
→ run_silver_log_dq
→ publish_log_interval
```

### 12.3. `build_gold`

```text
resolve_required_input_snapshots
→ build_dimensions
→ build_transaction_facts
→ build_web_request_fact
→ build_business_marts
→ build_web_marts
→ reconcile
→ validate_gold
→ publish_gold_snapshot
```

Gold được build theo data interval và input Iceberg snapshot đã cố định.

### 12.4. `maintain_iceberg_tables`

DAG đo file count/size, snapshot và manifest trước khi quyết định rewrite data files/manifests, expire snapshot hoặc remove orphan files. Compaction chỉ chạy khi vượt threshold theo table class và phải chứng minh không đổi logical result.

### 12.5. `repurchase_ml_batch`

ML là downstream riêng, chỉ nhận Gold snapshot đã qua quality/reconciliation gate. ML failure không rollback Gold publication.

---

## 13. Bronze layer

### 13.1. Trách nhiệm

- Đọc immutable Landing object.
- Commit raw source representation vào Iceberg append-only theo input identity.
- Giữ source duplicate để audit; không join hoặc tính KPI.
- Bổ sung run/file/checksum/cursor/schema metadata.
- Cho phép rebuild Silver mà không đọc lại MySQL hoặc source log directory.
- Ghi lỗi không thể deserialize/route vào technical quarantine.

### 13.2. Bronze tables

Bronze có đủ 16 bảng OLTP:

- `bronze_customers_batch`;
- `bronze_categories_batch`;
- `bronze_products_batch`;
- `bronze_product_variants_batch`;
- `bronze_carts_batch`;
- `bronze_cart_items_batch`;
- `bronze_wishlist_items_batch`;
- `bronze_orders_batch`;
- `bronze_order_items_batch`;
- `bronze_payments_batch`;
- `bronze_order_status_history_batch`;
- `bronze_inventory_batch`;
- `bronze_coupons_batch`;
- `bronze_coupon_redemptions_batch`;
- `bronze_refunds_batch`;
- `bronze_product_reviews_batch`.

Bảng log/audit:

- `bronze_access_logs`;
- `bronze_ingestion_errors`;
- `bronze_batch_audit`.

### 13.3. Partition

- OLTP Bronze ưu tiên `ingest_date` hoặc bounded extraction date.
- Log Bronze ưu tiên ngày/giờ của `occurred_at_utc` hoặc ingest date theo benchmark.
- Không partition theo customer, product, request ID hoặc UUID.
- Với dataset nhỏ, ưu tiên ít partition và file đủ lớn.

---

## 14. Silver layer

### 14.1. Silver OLTP

- Parse/cast và chuẩn hóa timestamp UTC.
- Deduplicate theo source identity.
- `MERGE` current state cho bảng mutable.
- Append/deduplicate cho bảng lịch sử.
- Validate status, amount, key và relationship.
- Pseudonymize hoặc loại PII không cần thiết.

### 14.2. Silver access log

- Parse JSON/text theo schema/parser version.
- Deduplicate theo `request_id`.
- Chuẩn hóa method, route, status và latency.
- Mask/hash IP và actor reference.
- Parse user-agent ở mức client/device family khi cần.
- Normalize search query/filter metadata và chạy PII sanitizer.
- Left join product/customer reference có kiểm soát.
- Không drop anonymous hoặc unresolved reference nếu record còn hợp lệ.

GeoIP external enrichment và clickstream event không thuộc TLCN.

### 14.3. Silver tables

- `silver_customers`;
- `silver_categories`;
- `silver_products`;
- `silver_product_variants`;
- `silver_carts`;
- `silver_cart_items`;
- `silver_wishlist_items`;
- `silver_orders`;
- `silver_order_items`;
- `silver_payments`;
- `silver_order_status_history`;
- `silver_inventory`;
- `silver_coupons`;
- `silver_coupon_redemptions`;
- `silver_refunds`;
- `silver_product_reviews`;
- `silver_order_lifecycle`;
- `silver_access_logs`;
- `silver_data_quarantine`;
- `silver_data_quality_results`.

---

## 15. Gold layer

### 15.1. Dimensions

- `dim_date`;
- `dim_customer` — pseudonymous key;
- `dim_category`;
- `dim_product`;
- `dim_variant`;
- `dim_route`;
- `dim_client` nếu client/device analysis được giữ trong dashboard.

Với scope nhỏ, descriptive attributes dùng Type 1 và transaction snapshot giữ lịch sử.
`dim_product` giữ current `is_archived`/`archived_at`; trạng thái coupon tương ứng được
giữ ở Silver và dùng khi dựng mart promotion. `archive_reason` được giữ ở Silver để
drill-down audit, không dùng làm dimension/cardinality tự do ở Gold. Không triển khai
SCD2 nếu chưa có câu hỏi phân tích cần thiết.

### 15.2. Facts

| Fact | Grain |
|---|---|
| `fact_order` | Một order |
| `fact_order_item` | Một order line |
| `fact_payment` | Một payment |
| `fact_cart` | Một cart |
| `fact_cart_item` | Một logical cart item/current extracted state |
| `fact_wishlist_item` | Một customer-product wishlist state |
| `fact_inventory_snapshot` | Một variant × snapshot date |
| `fact_web_request` | Một deduplicated HTTP request |

### 15.3. Marts

- `mart_sales_daily`;
- `mart_product_performance`;
- `mart_customer_summary`;
- `mart_cart_abandonment`;
- `mart_wishlist_product_interest`;
- `mart_inventory_daily`;
- `mart_web_traffic_daily`;
- `mart_web_performance_daily`;
- `mart_search_interest_daily`;
- `mart_data_freshness_quality`;
- `gold_customer_repurchase_features`;
- `gold_customer_repurchase_labels`;
- `gold_customer_repurchase_scores`.

---

## 16. KPI contract

### 16.1. Business KPI từ OLTP

- Gross collected revenue và refunded amount.
- Paid/confirmed/completed/cancelled order count.
- Units sold và average order value.
- Revenue theo date/category/product.
- Customer mới, customer mua hàng và historical repurchase rate.
- Cart abandonment theo grain cart.
- Wishlist popularity theo current/logical state.
- Inventory current/low-stock.

### 16.2. Access-log KPI

- Request count.
- Status-code distribution và 4xx/5xx rate.
- Latency average/p50/p95/p99.
- Top route và product-detail request.
- Search request, top normalized query và filter usage.
- Unique authenticated actor theo ngày/tháng khi coverage đủ.

Không dùng IP làm customer identity. Anonymous DAU/MAU không được công bố nếu không có anonymous key ổn định.

### 16.3. Funnel

Business funnel chuẩn:

```text
cart có item → order paid → order confirmed → order completed
```

Access log chỉ bổ sung traffic tới product/search/cart/checkout route. Không khẳng định chính xác `view → add-to-cart` nếu chưa có canonical event/action contract.

---

## 17. ML repurchase từ OLTP Gold

### 17.1. Population và label

- Population: customer có ít nhất một succeeded payment trước hoặc tại `as_of_time`.
- Observation window: chỉ dùng business/source time không vượt `as_of_time`.
- Prediction horizon: 30 ngày sau `as_of_time`.
- Label = 1 nếu có succeeded payment trong horizon đã đóng đầy đủ.

### 17.2. Feature

- recency, frequency, monetary;
- order/payment count và revenue theo cửa sổ 30/90/180 ngày;
- average order value và units/order;
- category/product diversity;
- customer tenure;
- cart/abandoned-cart count;
- current wishlist count;
- days since latest cart/wishlist update;
- completed-order ratio.

Access-log `view_count`, `search_count`, session và traffic-source feature không dùng cho model chính trong TLCN để giữ label/feature contract đơn giản và tránh identity coverage bias.

### 17.3. Model và evaluation

- Dummy baseline.
- Logistic Regression là model chính.
- Random Forest nhỏ chỉ là comparison nếu đủ thời gian.
- Temporal split; không random row split.
- Báo precision, recall, F1, ROC-AUC, PR-AUC, confusion matrix và calibration/Brier score khi phù hợp.
- Artifact/manifest lưu trên MinIO; không dùng MLflow.

---

## 18. Data quality và quarantine

### 18.1. Landing/Bronze checks

- Source object có checksum và manifest.
- Log file đã đóng; không ingest file đang ghi.
- Schema version được hỗ trợ.
- OLTP PK/cursor tồn tại.
- Row/line count khớp manifest.
- Không extract `customer_credentials`.
- Cùng source object không commit hai lần.

### 18.2. Silver OLTP checks

- PK/business key unique.
- FK relationship resolve theo policy.
- Amount không âm và order arithmetic đúng.
- Payment amount/status khớp order.
- Inventory/order transition hợp lệ.
- PII được pseudonymize.

### 18.3. Silver log checks

- `request_id` unique sau dedup.
- Timestamp, method, route, status và latency hợp lệ.
- Secret/PII scanner không phát hiện field cấm.
- Parser error và unresolved reference rate được báo cáo.
- Raw IP/actor key không đi vào trusted output.

### 18.4. Gold checks

- Fact grain unique và dimension key resolve.
- Revenue/units reconcile với Silver OLTP.
- Request totals reconcile với Silver log theo interval.
- Mart totals reconcile với facts.
- Không có raw PII trong Gold/ML.

### 18.5. Quarantine contract

Mỗi row quarantine có rule ID, layer, source type, source table/file/line hoặc PK reference, Bronze snapshot/reference, error code, severity, parser/schema version, run ID, quarantined time và reprocess status.

---

## 19. Reconciliation

### 19.1. OLTP

1. Source row count tại cutoff ↔ Landing/Bronze accepted rows.
2. Bronze distinct source identity ↔ Silver logical rows.
3. Orders/payments ↔ Gold facts.
4. Source VND totals ↔ Gold revenue.
5. Order item quantity ↔ Gold units sold.
6. Inventory current ↔ Silver/Gold snapshot.

Count và VND amount phải exact.

### 19.2. Access log

1. Closed source files ↔ Landing manifest files.
2. Source line count ↔ Bronze accepted + technical reject.
3. Bronze distinct `request_id` ↔ Silver request + semantic reject.
4. Silver request ↔ Gold `fact_web_request` theo interval.
5. Gold fact request ↔ web marts.

---

## 20. Rerun, replay và backfill

- Rerun cùng input identity không nhân logical row/KPI.
- Cùng log file checksum không ingest hai lần.
- Cùng `request_id` chỉ có một trusted request.
- Replay rebuild Silver/Gold chỉ từ Bronze + metadata.
- Backfill có source/date/range và namespace hoặc branch tách biệt.
- Cursor chỉ commit sau Gold publication thành công.
- Failed run không làm lộ partial Gold snapshot cho Trino/Superset.
- ML failure không rollback Gold publication.

---

## 21. Audit, observability và serving

Mỗi run lưu:

- run/DAG/task ID và data interval;
- source high watermark hoặc log window;
- source file/checksum;
- Iceberg input/output snapshot IDs;
- Polaris catalog/namespace/table;
- rows read/written/deduplicated/rejected/quarantined;
- bytes/file count trước và sau;
- min/max source/event time;
- duration/resource metrics;
- code/config/parser/schema version;
- DQ, reconciliation và publication status.

Trino đọc Iceberg qua Polaris. Superset chỉ query Gold marts/curated facts qua Trino; không còn bước publish sang MySQL analytics.

---

## 22. Iceberg maintenance

- Theo dõi số file nhỏ, average/median size, snapshot và manifest count.
- Compaction chỉ chạy khi vượt threshold cấu hình theo table class.
- Rewrite data files/manifests phải validate row count/checksum/KPI.
- Snapshot retention phải dài hơn replay/backfill/demo window.
- Orphan cleanup có safety window.
- Không mặc định dùng Z-order; ưu tiên Iceberg partition evolution, sort order và file rewrite theo benchmark.
- Airflow giới hạn một writer active cho cùng table/partition class.

---

## 23. Testing strategy

### Source

- Web business flows và OLTP invariant.
- MySQL schema/cursor compatibility.
- Log JSON schema, rotation và secret/PII exclusion.
- Duplicate/corrupt/truncated/late log file.

### Ingestion/Bronze

- Initial/incremental và same-timestamp cursor.
- Fixed high watermark.
- Duplicate run/file/checksum.
- Cursor chưa commit khi downstream fail.
- Landing/Bronze manifest reconciliation.

### Iceberg/Polaris/Trino

- Spark create/load/append/merge qua Polaris.
- Spark writer và Trino reader thấy cùng snapshot.
- Schema evolution compatibility.
- Commit conflict/retry.
- Compaction không đổi logical result.

### Silver/Gold

- Mutable merge và append-only dedup.
- Log parse/dedup/pseudonymize.
- Semantic quarantine.
- Fact/mart grain và reconciliation.
- Replay/backfill equivalence.

### BI/ML

- Superset chỉ đọc Trino.
- Dashboard không chạm primary OLTP.
- Point-in-time boundary, closed horizon và temporal split.
- Reproducible artifact/score lineage.

---

## 24. Phân công hai người

### Người A — Source và ingestion

- Website/API/MySQL và migration/seed.
- Deterministic OLTP generator.
- Structured access-log contract và rotation.
- OLTP/log Landing ingestion.
- Manifest, checksum, high watermark và cursor.
- Bronze và source-to-Bronze reconciliation.

### Người B — Lakehouse và analytics

- Spark/Iceberg/MinIO.
- Polaris catalog và Trino integration.
- Silver merge/parse/DQ/quarantine.
- Gold facts/dimensions/marts.
- Superset dashboard và Iceberg maintenance.
- ML feature/label/train/score.

### Làm chung

- Compatibility PoC và architecture review.
- Grain/KPI/privacy/reconciliation review.
- Replay/backfill/compaction test.
- Benchmark, report, slide và demo.

---

## 25. Roadmap 10 tuần

| Tuần | Người A | Người B | Mốc |
|---:|---|---|---|
| 1 | Freeze OLTP và log contract | Freeze KPI/Gold/ML contract | Scope hai nguồn ổn định |
| 2 | Hoàn thiện web/log rotation | Iceberg–Polaris–Trino PoC | Compatibility pass |
| 3 | Generator và fixtures | MinIO/Spark/Airflow base | Platform stable |
| 4 | OLTP/log Landing ingestion | Bronze Iceberg/audit | Bronze stable |
| 5 | Cursor/file idempotency | Silver OLTP/log | Silver stable |
| 6 | Source reconciliation | DQ/quarantine | Quality gate |
| 7 | Replay/backfill | Gold facts/dimensions | Gold accepted |
| 8 | Source fixes/benchmark | Marts/Trino/Superset | BI accepted |
| 9 | Failure/late-file scenarios | Maintenance và ML | Maintenance/ML accepted |
| 10 | Clean setup/runbook | Report/demo/performance | Final |

---

## 26. Deliverables

### Source

- Next.js storefront.
- FastAPI Ecommerce API.
- MySQL migrations/seeds cho 17-table logical schema.
- Deterministic OLTP generator.
- Structured JSONL access log và rotation/compression.

### Data platform

- Docker Compose profiles.
- OLTP/log ingestion DAGs.
- Immutable Landing manifests.
- Bronze/Silver/Gold Iceberg tables.
- Apache Polaris catalog.
- Trino query layer.
- DQ/quarantine/reconciliation.
- Replay/backfill và Iceberg maintenance.
- Pipeline audit/observability.
- Superset dashboard.
- ML feature/label/model/score artifacts.

### Tài liệu

- Architecture và compatibility matrix.
- MySQL/log source contracts.
- Cursor/cutoff/file identity contract.
- Bronze/Silver/Gold grain catalogue.
- KPI, DQ, reconciliation và privacy contracts.
- Iceberg maintenance/retention policy.
- ML leakage report và performance report.
- Setup/runbook, report, slide và demo script.

---

## 27. Acceptance criteria

### Website/OLTP/log

- Website business flows hoạt động và concurrent checkout không oversell.
- 17-table migration chạy từ clean database.
- Structured access log có required fields và không chứa secret/PII cấm.
- Log rotate/nén theo interval cấu hình.

### Pipeline

- Chỉ extract 16 bảng MySQL allowlist; không extract credentials.
- Initial/incremental không miss same-timestamp row.
- Duplicate log file/request không nhân trusted rows.
- Bronze đủ metadata để replay.
- Silver OLTP/log typed, deduplicated, merged và pseudonymized đúng.
- Quarantine không trộn vào Gold.
- Gold facts/marts có grain unique.
- Reconciliation hai nguồn pass.
- Cursor/publication commit sau quality gate.
- Spark và Trino đọc cùng Iceberg tables qua Polaris.

### Maintenance

- Small-file metric được thu thập.
- Compaction chỉ chạy khi vượt threshold.
- Row count/checksum/KPI không đổi sau maintenance.
- Snapshot retention đáp ứng replay/backfill.

### BI/ML

- Superset chỉ đọc Gold qua Trino.
- KPI khớp Gold snapshot và source interval.
- DAU/MAU chỉ dùng authenticated actor với coverage công bố.
- ML feature/label chỉ dùng OLTP-derived data trước cutoff.
- Temporal evaluation reproducible.
- Artifact/score có snapshot/run lineage.

---

## 28. Demo end-to-end

1. Khởi động `core`, `batch`, `bi`.
2. Thao tác website để tạo OLTP row và access log.
3. Xem MySQL source và log file đã rotate.
4. Chạy OLTP/log ingestion DAGs.
5. Xem Landing manifest và Bronze Iceberg snapshot.
6. Xem Silver typed/merged data và quarantine.
7. Xem Gold facts/marts.
8. Query Gold bằng Trino qua Polaris.
9. Xem Superset dashboard.
10. Chạy reconciliation.
11. Rerun cùng input để chứng minh idempotency.
12. Chạy compaction và chứng minh kết quả logic không đổi.
13. Replay/backfill một interval.
14. Chạy feature/label và ML evaluation.

---

## 29. Checklist

### Scope

- [ ] Hai nguồn chính thức: MySQL OLTP và structured access log.
- [ ] Clickstream/Kafka/Flink ngoài TLCN.

### Source

- [ ] 17-table OLTP schema/migration.
- [ ] Website flow và concurrency test.
- [ ] Generator OLTP reproducible.
- [ ] Log schema/rotation/compression/privacy contract.

### Data Engineering

- [ ] OLTP cursor/high watermark.
- [ ] Log file identity/checksum/window.
- [ ] Landing manifest.
- [ ] Bronze/Silver/Gold Iceberg.
- [ ] Polaris catalog và Trino integration.
- [ ] DQ/quarantine/reconciliation.
- [ ] Replay/backfill/maintenance.
- [ ] Audit/observability/performance.

### BI/ML

- [ ] Superset đọc Trino.
- [ ] Business và web-performance KPI.
- [ ] Point-in-time feature/label.
- [ ] Temporal evaluation.
- [ ] Artifact/score lineage.

### Final

- [ ] Clean setup.
- [ ] Runbook.
- [ ] Report/slide/demo.
