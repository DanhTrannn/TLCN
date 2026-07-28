# KẾ HOẠCH TIỂU LUẬN CHUYÊN NGÀNH — OLTP-ONLY DATA LAKEHOUSE

## 0. Trạng thái và nguồn yêu cầu

Tài liệu này là nguồn yêu cầu hiện hành, ưu tiên cao nhất cho phạm vi Tiểu luận chuyên ngành (TLCN).

Quyết định scope ngày 2026-07-28:

- TLCN chỉ sử dụng dữ liệu có cấu trúc từ MySQL OLTP của website.
- Log của API chỉ phục vụ vận hành và debug, không phải nguồn Lakehouse.
- `schema.md` là logical schema OLTP chi tiết.
- `web-plan.md` là kế hoạch triển khai source website tạo dữ liệu OLTP.
- `skills/oltp-design.md` là nguyên tắc thiết kế tham khảo.

---

## 1. Tên đề tài

> Xây dựng Data Lakehouse xử lý theo lô cho dữ liệu OLTP của website thương mại điện tử và dự đoán khả năng khách hàng mua lại.

Tên rút gọn:

> TLCN OLTP Batch Data Lakehouse.

---

## 2. Bối cảnh và vấn đề

Website thương mại điện tử phát sinh dữ liệu giao dịch trong MySQL như customer, catalog, wishlist, cart, order, payment và inventory.

Nếu truy vấn phân tích trực tiếp trên primary OLTP sẽ:

- cạnh tranh tài nguyên với nghiệp vụ web;
- khó giữ snapshot lịch sử;
- khó chạy lại pipeline;
- khó đối soát dữ liệu theo cùng cutoff;
- làm tăng rủi ro ảnh hưởng transaction.

TLCN xây dựng một pipeline batch để trích xuất dữ liệu MySQL sang Lakehouse, chuẩn hóa tại Silver, mô hình hóa tại Gold và phục vụ dashboard/ML mà không chạy analytics nặng trên OLTP.

Website chỉ là source application tối giản. Trọng tâm chính là Data Engineering trên dữ liệu OLTP.

---

## 3. Câu hỏi nghiên cứu

- **RQ1:** Trích xuất initial và incremental từ các bảng OLTP sang Lakehouse theo lô như thế nào mà không miss hoặc duplicate logical row?
- **RQ2:** Thiết kế Bronze–Silver–Gold cho dữ liệu mutable và append-only của OLTP như thế nào?
- **RQ3:** Kiểm tra chất lượng, quarantine và đối soát source-to-Gold như thế nào?
- **RQ4:** Rerun, replay và backfill như thế nào mà không làm sai row count hoặc KPI?
- **RQ5:** Mô hình fact/dimension nào phục vụ doanh thu, sản phẩm, cart, wishlist và inventory?
- **RQ6:** Tạo dữ liệu point-in-time cho bài toán dự đoán customer mua lại trong 30 ngày như thế nào để tránh leakage?

---

## 4. Mục tiêu

### 4.1. Mục tiêu tổng quát

Xây dựng hệ thống Data Lakehouse xử lý theo lô, chỉ dùng nguồn MySQL OLTP, có khả năng:

- initial/incremental extraction;
- lưu raw snapshot có lineage;
- chuẩn hóa và tích hợp dữ liệu;
- kiểm tra chất lượng và quarantine;
- xây dựng facts, dimensions và marts;
- đối soát source-to-target;
- rerun, replay và backfill;
- publish dữ liệu cho dashboard;
- tạo feature/label point-in-time cho ML mua lại.

### 4.2. Năng lực phải chứng minh

1. OLTP là system of record.
2. Pipeline chỉ đọc OLTP bằng tài khoản read-only.
3. Mỗi bảng nguồn có grain, key, mutability và cursor rõ ràng.
4. Bronze giữ raw representation và ingestion metadata.
5. Silver typed, deduplicated và tích hợp đúng business rule.
6. Gold có grain rõ và không sao chép schema OLTP một cách máy móc.
7. Pipeline idempotent theo run/input identity.
8. Reconciliation kiểm tra exact count và VND amount.
9. Dữ liệu ML point-in-time không dùng tương lai.
10. Toàn bộ dashboard và ML phải truy vết được về 12 bảng nguồn OLTP.

---

## 5. Phạm vi TLCN

### 5.1. Source website

Website tối giản hỗ trợ:

1. Đăng ký, đăng nhập và đăng xuất.
2. Xem category/product/variant.
3. Search/filter catalog để sử dụng web; search query không được lưu làm dữ liệu phân tích TLCN.
4. Customer quản lý một wishlist mặc định chứa nhiều product.
5. Customer quản lý active cart.
6. Checkout với địa chỉ nhập trực tiếp.
7. Checkout hợp lệ tạo order `paid`, payment `succeeded` và giảm inventory atomically.
8. Xem order history/detail.
9. Admin tối thiểu quản lý catalog, variant, inventory view, order completion và customer status.

### 5.2. Nguồn dữ liệu TLCN

Nguồn duy nhất của pipeline là MySQL schema `ecommerce`.

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
12. `inventory`.

`customer_credentials` thuộc OLTP nhưng bị loại hoàn toàn khỏi extraction vì chứa email đăng nhập/password hash và không có giá trị phân tích cần thiết.

### 5.3. Data Engineering

TLCN bao gồm:

- source catalogue và data contract cho MySQL;
- initial/incremental extraction;
- composite cursor `(timestamp, stable_pk)`;
- source high-watermark/cutoff;
- batch/run manifest;
- Bronze Delta cho raw OLTP rows;
- Silver domain tables;
- Gold facts, dimensions và marts;
- DQ, quarantine và reconciliation;
- rerun, replay và backfill;
- publish sang MySQL analytics;
- orchestration bằng Airflow;
- transformation bằng Spark/Delta trên MinIO.

### 5.4. BI

Dashboard ưu tiên:

- gross collected revenue;
- paid/completed order count;
- average order value;
- units sold;
- doanh thu theo ngày/category/product;
- customer mới và customer mua hàng;
- cart active/checked-out/abandoned theo định nghĩa OLTP;
- wishlist product popularity từ current/logical wishlist rows;
- inventory current/low-stock;
- tỷ lệ customer mua lại lịch sử;
- batch freshness và DQ status.

### 5.5. Machine Learning

Bài toán ML:

> Dự đoán khả năng một customer đã từng mua sẽ có thêm ít nhất một succeeded payment trong 30 ngày tiếp theo.

ML chỉ dùng feature từ Gold được suy ra từ OLTP:

- recency, frequency, monetary;
- average basket value và units/order;
- category/product diversity;
- order completion history;
- cart count, checked-out count và abandoned-cart count;
- wishlist current count và product/category diversity;
- customer tenure;
- thời gian từ cart creation đến checkout khi có thể suy ra từ OLTP.


## 6. Nguyên tắc kiến trúc

1. MySQL OLTP là source of truth.
2. Delta Gold là nguồn phân tích chuẩn sau reconciliation.
3. MySQL analytics chỉ là serving copy cho Superset.
4. Không chạy dashboard query trên primary OLTP.
5. Transaction web không gọi Airflow, Spark hoặc analytics database.
6. Extractor dùng account read-only và transaction/cutoff ngắn.
7. Mutable source dùng `updated_at + PK`; append-only source dùng `created_at/business_time + PK`.
8. Bronze append-only theo ingestion run, không overwrite source duplicate.
9. Silver chịu trách nhiệm deduplicate và merge theo source contract.
10. Gold publish chỉ xảy ra sau quality/reconciliation gate.
11. Mọi amount dùng integer VND.
12. Customer PII phải pseudonymize trước Gold/ML.

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
| Table format | Delta Lake 3.3 |
| Object storage | MinIO |
| BI serving | MySQL analytics |
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
        ↓ read-only batch extraction
Bronze Delta
        ↓ parse / dedup / merge
Silver Delta
        ↓ dimensional transformation
Gold Delta
        ├──→ MySQL analytics → Superset
        └──→ ML feature/label → train/score
```

Docker profiles:

- `core`: MySQL ecommerce, Ecommerce API, Storefront.
- `batch`: MinIO, Spark, Airflow, PostgreSQL metadata.
- `bi`: MySQL analytics, Superset, PostgreSQL metadata.
- `tools`: deterministic OLTP data generator.

---

## 9. Logical schema OLTP

Logical schema có 13 bảng và được mô tả chi tiết tại `schema.md`.

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
| History | `order_status_history` | Một order transition |
| Inventory | `inventory` | Một balance/variant |

Web transaction, constraint, index và concurrency theo `schema.md`; pipeline không được sửa ngược OLTP.

---

## 10. Source contract và extraction

### 10.1. Phân loại nguồn

| Bảng | Mutability | Cursor đề xuất | Silver behavior |
|---|---|---|---|
| `customers` | Mutable | `(updated_at, customer_id)` | Merge current state, anonymize PII |
| `categories` | Mutable | `(updated_at, category_id)` | Merge current state |
| `products` | Mutable | `(updated_at, product_id)` | Merge current state |
| `product_variants` | Mutable | `(updated_at, variant_id)` | Merge current state |
| `carts` | Mutable | `(updated_at, cart_id)` | Merge current state, derive lifecycle fields |
| `cart_items` | Mutable/logical removal | `(updated_at, cart_item_id)` | Merge current state |
| `wishlist_items` | Mutable/logical removal | `(updated_at, wishlist_item_id)` | Merge current state |
| `orders` | Mutable paid→completed | `(updated_at, order_id)` | Merge current state, preserve timestamps |
| `order_items` | Append-only | `(created_at, order_item_id)` | Insert/dedup |
| `payments` | Append-only | `(created_at, payment_id)` | Insert/dedup |
| `order_status_history` | Append-only | `(created_at, order_status_history_id)` | Insert/dedup |
| `inventory` | Mutable | `(updated_at, variant_id)` | Merge current balance, snapshot downstream |

### 10.2. Composite cursor

Điều kiện incremental chuẩn:

```sql
WHERE updated_at > :last_timestamp
   OR (updated_at = :last_timestamp AND primary_key > :last_pk)
ORDER BY updated_at, primary_key
```

Append-only table dùng `created_at` hoặc timestamp contract tương ứng.

### 10.3. Batch boundary

Mỗi run phải:

1. Capture high watermark của từng bảng.
2. Đọc từ committed cursor đến high watermark.
3. Ghi Bronze và validate.
4. Build Silver/Gold.
5. Reconcile và publish.
6. Chỉ commit source cursor sau khi toàn bộ core pipeline thành công.

### 10.4. Source metadata

Mỗi extracted row phải có:

- source system/schema/table;
- source PK/business key;
- source timestamp/cursor;
- extraction run ID;
- extracted/ingested time UTC;
- source high watermark;
- raw row checksum;
- code/config version;
- `data_origin` nếu nguồn có trường này.

---

## 11. Synthetic OLTP generator

Generator phục vụ khối lượng dữ liệu, edge case và reproducibility.

Modes TLCN:

- `seed_master`: category, product, variant, opening inventory.
- `historical_transactions`: customer, cart, order, order item, payment, status history, inventory change.
- `repurchase_history`: lịch sử tối thiểu 12 tháng và rolling customer behavior từ OLTP.
- `failure_fixtures`: source rows/batch conditions phục vụ DQ, cursor, duplicate extraction và constraint boundary.


Mỗi run có `scenario_id`, seed, anchor time, scale, generator version và logical identity. Cùng config/seed phải tạo cùng logical dataset. Generator phải xuất được file SQL import trực tiếp vào MySQL trong một transaction, giữ FK/CHECK và fail-fast khi import trùng.

---

## 12. Airflow DAG

Core DAG OLTP-only:

```text
check_services
→ capture_mysql_high_cursors
→ extract_mysql
→ write_bronze
→ validate_bronze
→ build_silver_domain
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


ML DAG là downstream riêng, chỉ nhận Gold publication đã thành công.

---

## 13. Bronze layer

### 13.1. Trách nhiệm

- Giữ raw OLTP row theo extraction run.
- Giữ source duplicate để audit.
- Bổ sung ingestion metadata.
- Cho phép rebuild Silver không đọc lại OLTP.
- Không join, tính KPI hoặc ML feature.

### 13.2. Bronze tables

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
- `bronze_ingestion_errors`;
- `bronze_batch_audit`.


### 13.3. Bronze error

`bronze_ingestion_errors` dùng cho lỗi kỹ thuật như:

- không đọc được source page;
- schema/source column mismatch;
- serialization/cast metadata lỗi;
- row thiếu routing/PK cần thiết;
- checksum hoặc batch manifest không hợp lệ.

Readable row có lỗi nghiệp vụ vẫn vào Bronze chuẩn và được đánh giá tại Silver.

### 13.4. Partition

- Partition theo `ingest_date` hoặc bounded extraction date.
- Không partition theo customer/product/UUID.
- Với dataset nhỏ, ưu tiên ít partition và file đủ lớn để tránh small-files.

---

## 14. Silver layer

### 14.1. Trách nhiệm

- Parse và cast kiểu dữ liệu.
- Chuẩn hóa timestamp về UTC.
- Deduplicate theo source identity/run semantics.
- Merge mutable current state.
- Giữ append-only order/payment/history.
- Validate status, amount, key và relationship.
- Pseudonymize hoặc loại PII không cần thiết.
- Ghi semantic quarantine và DQ results.

### 14.2. Silver tables

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
- `silver_order_lifecycle`;
- `silver_data_quarantine`;
- `silver_data_quality_results`.

Không có Silver session, web event hoặc request-log table trong TLCN.

---

## 15. Gold layer

### 15.1. Dimensions

- `dim_date`;
- `dim_customer` — pseudonymous key;
- `dim_category`;
- `dim_product`;
- `dim_variant`.

SCD strategy phải được chốt theo KPI. Với scope nhỏ, Type 1 cho descriptive current attributes và transaction snapshot cho lịch sử là đủ; không triển khai SCD2 nếu không có câu hỏi phân tích cần thiết.

### 15.2. Facts

| Fact | Grain |
|---|---|
| `fact_order` | Một order |
| `fact_order_item` | Một order line |
| `fact_payment` | Một payment/order |
| `fact_cart` | Một cart |
| `fact_cart_item` | Một logical cart item/current extracted state |
| `fact_wishlist_item` | Một customer-product wishlist state |
| `fact_inventory_snapshot` | Một variant × snapshot date |


### 15.3. Marts

- `mart_sales_daily`;
- `mart_product_performance`;
- `mart_customer_summary`;
- `mart_cart_abandonment`;
- `mart_wishlist_product_interest`;
- `mart_inventory_daily`;
- `mart_data_freshness_quality`;
- `gold_customer_repurchase_features`;
- `gold_customer_repurchase_labels`;
- `gold_customer_repurchase_scores`.

---

## 16. KPI contract

### 16.1. Sales

- Gross collected revenue = sum successful payment amount.
- Paid/completed order count.
- Units sold.
- Average order value.
- Revenue theo date/category/product.

### 16.2. Cart

Cart abandonment được tính theo cart OLTP:

- cart có ít nhất một present item hoặc từng có item theo extracted state khả dụng;
- không có order cho cart;
- không cập nhật trong 24 giờ tại cutoff.

Phải công bố limitation: batch snapshot của mutable `cart_items` không bảo tồn mọi mutation trung gian.

### 16.3. Wishlist

- Current wishlist product count.
- Customer có wishlist.
- Product/category popularity theo current/logical state.
- Không suy diễn số lần add/remove từ trạng thái cuối của mutable row.

### 16.4. Inventory

- Current on-hand.
- Low-stock variant count.
- Sold units đối soát với opening/current inventory.

## 17. ML repurchase OLTP-only

### 17.1. Population và label

- Population: customer có ít nhất một succeeded payment trước hoặc tại `as_of_time`.
- Observation window: chỉ dùng dữ liệu có business/source time không vượt `as_of_time`.
- Prediction horizon: 30 ngày sau `as_of_time`.
- Label = 1 nếu có succeeded payment trong horizon đã đóng đầy đủ.

### 17.2. Feature

Bắt buộc:

- days since last purchase;
- order/payment count 30/90/180 ngày;
- revenue 30/90/180 ngày;
- average order value;
- units/order;
- distinct category/product count;
- customer tenure;
- cart count và abandoned cart count;
- current wishlist count;
- days since latest cart/wishlist update;
- completed-order ratio.

Không có session_count, view_count, search_count hoặc traffic-source feature.

### 17.3. Model và evaluation

- Dummy baseline.
- Logistic Regression là model chính.
- Random Forest nhỏ chỉ là comparison nếu đủ thời gian.
- Temporal split; không random row split.
- Báo precision, recall, F1, ROC-AUC, PR-AUC, confusion matrix và calibration/Brier score khi phù hợp.
- Model artifact/manifest lưu trên MinIO, không dùng MLflow.

---

## 18. Data quality và quarantine

### 18.1. Bronze technical checks

- Source table/schema đúng contract.
- PK và cursor field tồn tại.
- Raw row checksum hợp lệ.
- Batch manifest/high watermark hợp lệ.
- Không extract `customer_credentials`.

### 18.2. Silver semantic checks

- PK/business key unique.
- FK relationship có thể resolve.
- Amount không âm và order arithmetic đúng.
- Payment amount/status khớp order.
- Order item line total đúng.
- `0 <= on_hand <= opening_on_hand`.
- Wishlist/cart logical removal nhất quán.
- Order transition hợp lệ.

### 18.3. Gold checks

- Fact grain unique.
- Dimension key resolve.
- Revenue và sold units reconcile với Silver.
- Không có raw PII trong Gold/ML.
- Mart totals reconcile với facts.

### 18.4. Quarantine contract

Mỗi row quarantine có rule ID, layer, source table/PK, Bronze reference, raw value/payload reference, error code, severity, run ID và quarantined time.

---

## 19. Reconciliation

Bắt buộc:

1. Source row count tại cutoff ↔ Bronze accepted rows.
2. Bronze distinct source identity ↔ Silver logical rows.
3. Source orders/payments ↔ Silver ↔ Gold facts.
4. Source VND totals ↔ Gold revenue totals.
5. Order items quantity ↔ Gold units sold.
6. `opening_on_hand - succeeded sold units = on_hand` theo variant.
7. Source inventory current ↔ Silver inventory.
8. Gold fact totals ↔ marts.
9. Eligible ML customer count ↔ feature rows.
10. Positive label count ↔ succeeded payment trong đúng horizon.

Count và VND amount phải exact.

---

## 20. Rerun, replay và backfill

- Rerun cùng input identity không nhân logical rows/KPI.
- Replay rebuild Silver/Gold chỉ từ Bronze + metadata.
- Backfill có source table/date/PK range và namespace riêng.
- Mutable affected partition được recompute có kiểm soát.
- Cursor chỉ commit sau Gold/publish thành công.
- ML failure không rollback Gold publication.

---

## 21. Audit, observability và publish

Mỗi run lưu:

- run/batch ID;
- logical date;
- source high watermarks;
- input/output table versions;
- rows read/written/rejected/quarantined;
- min/max cursor;
- duration/resource metrics;
- code/config version;
- reconciliation result;
- publish status.

Operational application logs được dùng để debug service nhưng không ingest vào Bronze trong TLCN.

Publish BI dùng staging + validate + atomic switch/upsert strategy. Dashboard chỉ đọc MySQL analytics.

---

## 22. Testing strategy

### Source

- auth/catalog/wishlist/cart/checkout/order/admin;
- amount/inventory invariants;
- idempotency và concurrent last-item checkout;
- migration từ database rỗng.

### Extraction/Bronze

- initial load;
- same-timestamp composite cursor;
- update đúng high watermark;
- duplicate run;
- cursor chưa commit khi downstream fail;
- credentials không bị extract.

### Silver/Gold

- merge mutable rows;
- dedup append-only rows;
- semantic quarantine;
- amount/inventory reconciliation;
- fact/mart grain;
- replay/backfill equivalence.

### ML

- point-in-time boundary;
- closed horizon;
- temporal split;
- no leakage;
- reproducible feature/label/model output.


---

## 23. Phân công hai người

### Người A — Source và Ingestion

- website/API/MySQL;
- schema/migration/seed;
- deterministic OLTP generator;
- source contracts;
- high watermark/cursor;
- extraction và Bronze;
- source/Bronze reconciliation.

### Người B — Transformation và Analytics

- Spark/Delta/MinIO;
- Silver merge/DQ/quarantine;
- Gold facts/dimensions/marts;
- analytics publish/Superset;
- ML feature/label/train/score;
- performance report.

### Làm chung

- architecture và grain review;
- reconciliation rules;
- replay/backfill test;
- report, slide và demo.

---

## 24. Roadmap 10 tuần

| Tuần | Người A | Người B | Mốc |
|---:|---|---|---|
| 1 | Freeze OLTP source/schema | Freeze KPI/Gold/ML contract | Scope OLTP-only |
| 2 | Hoàn thiện web/migration | Delta/MinIO PoC | Source stable |
| 3 | Generator OLTP | Spark/Airflow base | Platform stable |
| 4 | Initial/incremental extract | Bronze tables/audit | Bronze stable |
| 5 | Cursor/retry/failure | Silver domain merge | Silver base |
| 6 | Source reconciliation | DQ/quarantine | Quality gate |
| 7 | Backfill/replay | Gold facts/dims | Gold accepted |
| 8 | Handoff/fixes | Marts/publish/dashboard | BI accepted |
| 9 | Performance support | ML feature/train/score | ML accepted |
| 10 | Clean setup/runbook | Reports/demo | Final |

---

## 25. Deliverables

### Source

- Next.js storefront;
- FastAPI Ecommerce API;
- MySQL migrations/seeds;
- 13-table OLTP schema;
- deterministic OLTP generator.

### Data platform

- Docker profiles;
- Airflow OLTP-only DAG;
- initial/incremental extractor;
- Bronze/Silver/Gold Delta tables;
- DQ/quarantine/reconciliation;
- replay/backfill;
- pipeline audit;
- MySQL analytics publish;
- Superset dashboard;
- ML feature/label/model/score artifacts.

### Tài liệu

- architecture;
- source catalogue/data dictionary;
- cursor/cutoff contract;
- Bronze/Silver/Gold grain catalogue;
- KPI contract;
- DQ/reconciliation rules;
- ML contract/leakage report;
- performance report;
- setup/runbook;
- report/slide/demo script.


---

## 26. Acceptance criteria

### Website/OLTP

- Login, catalog, wishlist, cart, checkout, order và admin hoạt động.
- Checkout hợp lệ tạo order/payment/items/history và giảm inventory atomically.
- Checkout bị từ chối không tạo order/payment và không giảm stock.
- Concurrent checkout không oversell.
- 13-table migration chạy từ clean database.

### Pipeline

- Chỉ extract 12 bảng phân tích cho phép; không extract credentials.
- Initial/incremental không miss same-timestamp rows.
- Rerun không nhân logical rows.
- Bronze giữ raw row và metadata đủ replay.
- Silver typed/merged/deduplicated đúng.
- Quarantine không trộn vào Gold.
- Gold facts/marts có grain unique.
- Reconciliation source-to-Gold pass.
- Cursor commit sau publish thành công.

### BI/ML

- Dashboard chỉ đọc serving database.
- KPI khớp Gold và source cutoff.
- Feature/label chỉ dùng dữ liệu OLTP trước cutoff.
- Temporal evaluation reproducible.
- Model artifact và score có version/lineage.

## 27. Demo end-to-end

1. Khởi động `core`, `batch`, `bi`.
2. Thao tác website để tạo customer/cart/order/payment/inventory data.
3. Kiểm tra MySQL source trước pipeline.
4. Capture high watermarks và chạy DAG.
5. Xem raw row + metadata tại Bronze.
6. Xem typed/merged row và quarantine tại Silver.
7. Xem facts/marts tại Gold.
8. Chạy reconciliation.
9. Xem dashboard Superset.
10. Chạy feature/label và ML evaluation.
11. Rerun cùng input để chứng minh idempotency.
12. Replay từ Bronze hoặc backfill một range.


---

## 28. Checklist

### Scope

- [ ] Source duy nhất là MySQL OLTP.

### Source

- [ ] 13-table schema/migration.
- [ ] Website flow và concurrency test.
- [ ] Generator OLTP reproducible.

### Data Engineering

- [ ] Source contract/cursor/high watermark.
- [ ] Bronze raw/audit/error.
- [ ] Silver merge/DQ/quarantine.
- [ ] Gold facts/dims/marts.
- [ ] Reconciliation/replay/backfill.
- [ ] Publish/audit/performance.

### BI/ML

- [ ] Dashboard OLTP-derived KPI.
- [ ] Point-in-time feature/label.
- [ ] Temporal evaluation.
- [ ] Artifact/score lineage.

### Final

- [ ] Clean setup.
- [ ] Runbook.
- [ ] Report/slide/demo.
