# Mô hình Data Lakehouse hiện tại

Tài liệu mô tả bảng và luồng có trong mã nguồn. Kiến trúc tổng thể ở [System Architecture](../architecture/SYSTEM_ARCHITECTURE_VISUAL.md), công thức ở [Metrics Catalog](../architecture/METRICS_CATALOG.md).

## 1. Catalog và storage

Polaris quản lý catalog `lakehouse` với sáu namespace: `landing`, `bronze`, `silver`, `gold`, `quarantine`, `system`. MinIO lưu file; Iceberg quản lý bảng/snapshot. PostgreSQL lưu metadata dịch vụ Polaris/Airflow.

| Vùng | Nội dung |
|---|---|
| `landing/oltp/<table>/...` | Parquet và manifest của từng lần trích xuất MySQL |
| `landing/logs/...` | JSONL.gz lịch sử đã upload; chưa có job tự đọc file thô vào Gold |
| `warehouse/` | Iceberg data/metadata theo vị trí do catalog quản lý |
| State/checkpoint prefixes | Cursor batch, checkpoint Flink và trạng thái tác vụ |
| `quarantine` | Dữ liệu lỗi schema/nghiệp vụ đã xử lý PII theo quy tắc |
| `system.data_quality_results` | Bằng chứng kiểm tra chất lượng và đối soát |

Prefix raw Landing là vị trí file. Namespace `lakehouse.landing` còn chứa bảng Iceberg streaming access log; đây là hai dạng lưu trữ khác nhau.

## 2. Batch OLTP

Nguồn là 27 bảng trong [default.yml](../../pipelines/config/default.yml), loại `customer_credentials` khỏi 28 bảng OLTP.

- **Extract:** Spark dùng cursor `(cursor_field, pk)`, lookback mặc định 10 phút, giới hạn high watermark và ghi manifest.
- **Bronze:** Đọc Landing, giữ lịch sử/lineage, kiểm tra bản ghi hỏng và đưa dữ liệu lỗi vào quarantine.
- **Silver:** Chuẩn hóa kiểu, khử trùng, MERGE dữ liệu mutable, xử lý PII và kiểm tra ràng buộc.
- **Gold:** Xây dimension/fact/mart từ Silver và gắn `_gold_ingested_at`, `_source_run_id`.
- **Gates:** Đối soát MySQL–Silver trước Gold và parity/khóa/lineage sau Gold. Vi phạm làm tác vụ thất bại và được ghi vào bảng audit.

Cursor không tự phát hiện mọi hard delete ở nguồn. Bronze CDC có lưu delete/tombstone riêng; việc áp dụng chúng vào Silver/Gold chưa tự động hóa.

## 3. Gold OLTP: 15 bảng

Nguồn DDL: [gold_ddl.py](../../pipelines/src/lakehouse/oltp/gold_ddl.py). Nguồn biến đổi: [gold.py](../../pipelines/src/lakehouse/oltp/gold.py).

### Sáu dimension

| Bảng | Grain / nội dung |
|---|---|
| `dim_date` | Một ngày; thuộc tính lịch |
| `dim_customer` | Một customer; thuộc tính đã pseudonymize |
| `dim_product` | Một product, kèm danh mục |
| `dim_variant` | Một SKU/variant |
| `dim_store` | Một cửa hàng, kèm city |
| `dim_delivery_staff` | Một nhân viên giao vận |

### Năm fact

| Bảng | Grain / nội dung |
|---|---|
| `fact_order` | Một đơn; order totals, giá vốn, trạng thái và revenue flags |
| `fact_order_item` | Một chi tiết đơn; số lượng, giá bán và cost snapshot |
| `fact_shipment` | Một shipment; trạng thái, mốc giao hàng và COD |
| `fact_return_exchange` | Một return item; request cha, variant, action và refund |
| `fact_inventory_daily_snapshot` | Ngày snapshot × variant × địa điểm kho/cửa hàng |

Tên bảng snapshot không chứng minh đang có đầy đủ lịch sử mọi ngày. Cần kiểm tra dữ liệu thực tế và cách ghi của lần chạy trước khi diễn giải chuỗi thời gian.

### Bốn mart

| Bảng | Grain chính |
|---|---|
| `mart_sales_daily` | Ngày × kênh × cửa hàng × danh mục |
| `mart_logistics_performance` | Ngày shipment × nhân viên giao vận |
| `mart_product_returns` | Ngày trả × variant × action × reason |
| `mart_inventory_health` | Ngày snapshot × loại địa điểm × địa điểm × danh mục |

Order count ở mart sales không được cộng qua các danh mục để suy ra số đơn distinct. Công thức revenue order-level và item-level có khác biệt; xem Metrics Catalog.

## 4. Access logs và CDC

| Nhóm | Bảng / cách xử lý |
|---|---|
| Log Landing | `landing.access_logs`, nguồn streaming Kafka |
| Log Bronze | `bronze.web_events` |
| Log Silver | `silver.silver_logs` |
| Log Gold fact | `gold.fact_web_events` |
| Log Gold marts | `mart_hourly_route_metrics`, `mart_daily_product_demand`, `mart_marketing_funnel_daily` |
| CDC Bronze | `bronze.oltp_cdc_events`; envelope, operation, before/after, event_id và replay coordinates |

Job Flink access log sử dụng StatementSet để ghi các tầng của log. Spark `build_logs_gold` thực hiện rollup mart; DAG streaming maintenance chạy mỗi hai giờ.

CDC log có thể chứa nhiều thay đổi của cùng khóa nguồn. Đếm sự kiện không tương đương đếm bản ghi hiện tại. CDC chưa nối trực tiếp vào các Silver/Gold OLTP ở mục 3.

## 5. Bảo trì và quyền

DAG OLTP maintenance chạy 03:00 hằng ngày; streaming maintenance chạy hai giờ/lần. Các tác vụ gồm compaction, snapshot expiration, orphan cleanup và retention quarantine 30 ngày theo cấu hình.

Polaris dùng bốn principal tách biệt; MinIO có bảy identity theo workload. `trino_reader` phục vụ truy vấn đọc, `trino_admin` dùng khi cần quản trị. Credential mỗi consumer nằm trong volume riêng.

Số dòng từng bảng và hiệu năng không được cố định trong tài liệu thiết kế. Khi báo cáo, truy vấn snapshot/run cụ thể và ghi lại môi trường thực thi.

