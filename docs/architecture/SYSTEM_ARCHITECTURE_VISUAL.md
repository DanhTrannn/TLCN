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

API kiểm tra vai trò/phạm vi cửa hàng, đọc SQL, rồi trả dữ liệu cho BI Hub cùng `data_source`, `is_degraded`, `degraded_reason`.

Executive/sales/system chủ yếu đọc Gold. Marketing đọc `fact_web_events` trong 30 ngày. Store/inventory/operations dùng MySQL cho tình trạng hiện tại. Khi nguồn chính không khả dụng, API có thể trả OLTP fallback có đánh dấu.

MinIO có bảy identity theo workload. Polaris có `spark_writer`, `flink_writer`, `trino_reader`, `trino_admin`; credential tách theo consumer. Code batch chỉ đọc OLTP, nhưng Compose mặc định dùng `MYSQL_USER` của ứng dụng; chưa tách MySQL user chỉ có quyền SELECT.

## 6. Triển khai cục bộ

Profile chính: `core`, `batch`, `streaming`. `lakehouse-tools` cung cấp Spark SQL client; `trino-admin` là engine quản trị tùy chọn. `.env.example` bật ba profile chính.

Stack local dùng HTTP. TLS, Secure cookie và secret manager production chưa được đóng gói đầy đủ trong Compose hiện tại.

Nguồn: [docker-compose.yml](../../docker-compose.yml), [DAGs](../../airflow/dags), [jobs](../../pipelines/src/jobs), [Polaris RBAC](../../infrastructure/polaris/rbac.yml).
