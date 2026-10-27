# Kiến trúc Web và Data Lakehouse

Hệ thống xử lý giao dịch thương mại điện tử và xây dựng dữ liệu phân tích. Trọng tâm đồ án là đường dữ liệu từ nguồn đến Lakehouse và lớp SQL phục vụ báo cáo.

Bản vẽ tổng quan: [system-architecture.drawio](../diagrams/system-architecture.drawio). Chi tiết bảng: [Lakehouse Design](../project/LAKEHOUSE_DESIGN_PLAN.md). Công thức: [Metrics Catalog](METRICS_CATALOG.md).

## 1. Thành phần và ranh giới

| Khối | Trách nhiệm |
|---|---|
| Next.js 15 / React 19 | Storefront, POS, Admin và BI Hub dùng ECharts; gọi FastAPI |
| FastAPI / SQLAlchemy | Auth, RBAC, giao dịch ngắn với MySQL, access log và API analytics |
| MySQL 8.4 | 28 bảng OLTP; nguồn batch và binlog CDC |
| Debezium / Kafka Connect | Snapshot ban đầu và thu row binlog của 27 bảng phân tích |
| Kafka 3.8 | Topic access log và các topic CDC theo bảng |
| Flink 1.19 | Job access log và job CDC độc lập; checkpoint định kỳ |
| Airflow 2.10 / Spark 3.5 | Điều phối/thực thi batch, biến đổi, đối soát và bảo trì |
| MinIO | Lưu file Landing, data/metadata Iceberg và state |
| Iceberg 1.10 | Định dạng bảng, snapshot, schema và commit |
| Polaris 1.6 / PostgreSQL | REST catalog, quyền truy cập và metadata quản trị |
| Trino 483 | Đọc Iceberg qua Polaris/MinIO để phục vụ SQL |
| LibreDB Studio | Giao diện SQL cho người vận hành |

Frontend không truy cập MySQL/Trino trực tiếp. FastAPI đọc Trino cho báo cáo lịch sử và MySQL cho chỉ số vận hành. API không gọi Spark để xử lý từng request.

## 2. Ba đường dữ liệu

| Luồng | Đường đi | Điểm ra và giới hạn |
|---|---|---|
| Batch OLTP | MySQL → Spark → Landing Parquet/manifest → Bronze → Silver → Gold | DAG có cursor tăng dần và quality gate |
| CDC OLTP | MySQL binlog → Debezium → Kafka → Flink | Append-only `bronze.oltp_cdc_events`; chưa tự materialize CDC thành Silver/Gold |
| Access log | FastAPI middleware → Kafka → Flink | Ghi các bảng log Landing/Bronze/Silver/Gold bằng StatementSet |

`customer_credentials` bị loại khỏi batch và CDC. PII của các bảng phân tích cần được xử lý trước khi phục vụ ở Silver/Gold.

Batch xây dữ liệu phân tích có đối soát; CDC lưu lịch sử để truy vết/replay. Bản ghi xóa trong binlog không đồng nghĩa Silver batch đã tự áp dụng xóa đó.

JSONL lịch sử do `generator export-logs` tạo và upload lên `landing/logs/` là file thô. Job Flink hiện tại đọc Kafka; upload file không tự kích hoạt xử lý sang Gold.

## 3. Lưu trữ và chất lượng

Catalog `lakehouse` có sáu namespace: `landing`, `bronze`, `silver`, `gold`, `quarantine`, `system`.

- Batch Landing: `s3://lakehouse/landing/oltp/<table>/...`.
- Iceberg warehouse: `s3://lakehouse/warehouse/`; vị trí bảng do catalog/Iceberg quản lý.
- Cursor/checkpoint/state có prefix riêng trong bucket.
- Bronze giữ dữ liệu nguồn và lineage. Silver chuẩn hóa, khử trùng, MERGE và pseudonymize. Gold tạo dimension/fact/mart.
- Quarantine lưu bản ghi không hợp lệ; system lưu kết quả đối soát/chất lượng.

Gate trước Gold so sánh MySQL/Silver. Gate sau Gold kiểm tra parity, khóa, tham chiếu và lineage. Kết quả ghi vào `lakehouse.system.data_quality_results`; lỗi gate làm DAG thất bại. Đây là logic vận hành của pipeline.

## 4. Lịch chạy và độ mới

| Thành phần | Cấu hình mã nguồn |
|---|---|
| `lakehouse_oltp_pipeline` | Hằng ngày 02:00, Asia/Ho_Chi_Minh |
| `lakehouse_oltp_maintenance` | Hằng ngày 03:00 |
| `lakehouse_streaming_maintenance` | Mỗi 2 giờ |
| Flink access logs/CDC | Liên tục, checkpoint 10 giây |
| BI Hub | Một số vai trò tự tải lại sau 60 giây khi trang hoạt động |

Checkpoint và chu kỳ tải lại UI không phải cam kết latency end-to-end. Gold OLTP thay đổi theo batch thực tế. Ngưỡng freshness 15/60 phút trên trang system là ngưỡng hiển thị; batch hằng ngày không đáp ứng ngưỡng 15 phút liên tục.

## 5. Serving và phân quyền

BI Hub `/admin/analytics` gọi FastAPI; API xác thực vai trò và cửa hàng, đọc Trino/MySQL rồi trả JSON cho ECharts. Trino đọc Iceberg qua Polaris/MinIO; MySQL cung cấp trạng thái vận hành hiện tại. Frontend không gọi các engine xử lý dữ liệu trực tiếp.

### Vai trò và nguồn dữ liệu

| Vai trò hiển thị | Vai trò tài khoản | Nguồn chính / nội dung |
|---|---|---|
| Executive | `admin` | Gold fact_order và mart trả hàng; doanh thu, cost/profit, đơn; bổ sung COD đang giao từ OLTP |
| Sales | `sales_manager` | Gold fact_order/fact_order_item/mart_sales_daily; doanh thu kênh, cửa hàng, sản phẩm |
| Marketing | `marketing_manager` | Gold fact_web_events trong 30 ngày; bổ sung coupon/review từ OLTP |
| Store | `store_manager` | MySQL theo cửa hàng; doanh thu hôm nay, số đơn, stockout |
| Inventory | `inventory_manager` | MySQL; lượng/giá trị tồn, inbound, depletion |
| Operations | `operations_manager` | MySQL; đơn chờ, shipment, COD lỗi, return |
| System | `system_admin` | Gold freshness và đối soát count/tiền với MySQL |

Admin có quyền truy cập các dashboard; các vai trò khác bị giới hạn bởi `validate_role_access`. Store manager bị cố định theo cửa hàng được gán bằng `resolve_effective_store_id`. Đây là lọc ở ứng dụng/API, không phải row-level security tự động trong Trino.

### API và trạng thái nguồn

| Endpoint | Mục đích |
|---|---|
| `GET /api/v1/admin/analytics/role-metrics` | Chỉ số theo vai trò và store hợp lệ |
| `GET /api/v1/admin/analytics/stores` | Danh sách cửa hàng theo quyền |
| `GET /api/v1/admin/analytics/sales-trend` | Biểu đồ theo ngày, quyền admin/sales_manager |
| `GET /api/v1/admin/analytics/overview` | Tổng quan OLTP, quyền admin |

Response chỉ số có `data_source`, `is_degraded`, `degraded_reason`. Trino lỗi có thể dẫn đến OLTP fallback; marketing không có event trong cửa sổ cũng có thể fallback. Công thức fallback có thể khác Gold, nên UI cần hiển thị nguồn. [Metrics Catalog](METRICS_CATALOG.md) định nghĩa công thức, grain và giới hạn diễn giải; dữ liệu generator vẫn là dữ liệu tổng hợp sau khi xử lý qua pipeline.

Store/inventory/operations ưu tiên OLTP ngay cả khi Trino đang hoạt động. Marketing/store/inventory/operations tự tải lại 60 giây khi trang hoạt động; việc reload không khiến batch Gold tự chạy.

BI Hub tổ chức từng góc nhìn theo tổng quan → xu hướng (khi có API phù hợp) → phân nhóm/bảng chi tiết → bước kiểm tra. Bộ chọn 7/30/90 ngày chỉ tác động biểu đồ và bảng xu hướng, không đổi KPI toàn nguồn. Bộ chọn cửa hàng áp dụng góc nhìn store theo quyền của API. Tìm kiếm, sắp xếp và xuất CSV giới hạn trong từng bảng.

Giao diện tách thời điểm nhận phản hồi (UTC+7) khỏi tuổi dữ liệu Gold, hiển thị nguồn/fallback riêng cho xu hướng, và cung cấp từ điển chỉ số theo nguồn phản hồi. Không dựng target/delta khi API chưa cung cấp. Các bước marketing được trình bày như lượng sự kiện/proxy, các nhóm giao vận có thể chồng lặp không dùng làm cơ cấu đơn. Khi system dùng fallback, giá trị Gold/variance thay thế không được diễn giải như kết quả đối soát đã đo. Các hành động là hướng dẫn hoặc liên kết tới màn hình nghiệp vụ có quyền truy cập.

Nguồn serving: [router](../../services/ecommerce-api/app/modules/analytics/router.py), [service](../../services/ecommerce-api/app/modules/analytics/service.py), [schemas](../../services/ecommerce-api/app/modules/analytics/schemas.py), [BI Hub](../../apps/storefront/src/app/admin/analytics/page.tsx).

### Quyền truy cập storage và catalog

MinIO có bảy identity theo workload. Polaris có `spark_writer`, `flink_writer`, `trino_reader`, `trino_admin`; credential tách theo consumer. Code batch chỉ đọc OLTP, nhưng Compose mặc định dùng `MYSQL_USER` của ứng dụng; chưa tách MySQL user chỉ có quyền SELECT. Cách bootstrap và áp dụng RBAC nằm trong [SETUP](../runbook/SETUP.md).

## 6. Triển khai cục bộ

Profile chính: `core`, `batch`, `streaming`. `lakehouse-tools` cung cấp Spark SQL client; `trino-admin` là engine quản trị tùy chọn. `.env.example` bật ba profile chính.

Stack local dùng HTTP. TLS, Secure cookie và secret manager production chưa được đóng gói đầy đủ trong Compose hiện tại.

Nguồn: [docker-compose.yml](../../docker-compose.yml), [DAGs](../../airflow/dags), [jobs](../../pipelines/src/jobs), [Polaris RBAC](../../infrastructure/polaris/rbac.yml).
