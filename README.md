# D&K E-Commerce Data Lakehouse

Đồ án tập trung vào Data Engineering: thu thập dữ liệu giao dịch và access log, xử lý theo mô hình Landing → Bronze → Silver → Gold, rồi cung cấp dữ liệu phân tích qua Trino và dashboard.

Website thương mại điện tử/POS là hệ thống nguồn. Dữ liệu phát sinh từ thao tác trên ứng dụng hoặc bộ sinh dữ liệu tổng hợp trong `generator/`.

## Thành phần chính

| Thành phần | Vai trò |
|---|---|
| Next.js + FastAPI + MySQL | Website, API nghiệp vụ, 28 bảng OLTP |
| Debezium + Kafka | Thu thay đổi MySQL binlog và truyền sự kiện |
| Flink | Xử lý access log liên tục; lưu CDC vào Bronze |
| Airflow + Spark | Điều phối batch, trích xuất 27 bảng, biến đổi và đối soát |
| MinIO + Iceberg + Polaris | Lưu file, quản lý bảng và catalog/quyền truy cập |
| Trino + ECharts | Truy vấn SQL và trực quan hóa chỉ số |

Kiến trúc chi tiết: [System Architecture](docs/architecture/SYSTEM_ARCHITECTURE_VISUAL.md). Bản vẽ chỉnh sửa được: [system-architecture.drawio](docs/diagrams/system-architecture.drawio).

## Ba đường dữ liệu

1. **Batch OLTP:** MySQL → Spark → Landing Parquet/manifest → Bronze → Silver → Gold.
2. **CDC OLTP:** MySQL binlog → Debezium → Kafka → Flink → `bronze.oltp_cdc_events`.
3. **Access logs:** FastAPI → Kafka → Flink → các bảng Iceberg Landing/Bronze/Silver/Gold của log.

CDC hiện lưu lịch sử thay đổi để truy vết/replay. Các bảng Silver/Gold của OLTP vẫn được Spark batch xây dựng.

## Chạy hệ thống

Yêu cầu Docker Compose; dùng Python 3.11 + uv cho CLI Python và Node.js 22 + npm 10 trở lên cho phát triển frontend.

```bash
cp .env.example .env
./scripts/start_all.sh --build
```

| Dịch vụ | Địa chỉ mặc định |
|---|---|
| Storefront / Admin / BI | http://localhost:3000 /admin /admin/analytics |
| API và Swagger | http://localhost:8000/docs |
| Airflow | http://localhost:8080 |
| Spark Master | http://localhost:8082 |
| Trino | http://localhost:8084 |
| Flink | http://localhost:8085 |
| Debezium Connect | http://127.0.0.1:8086 |
| MinIO Console | http://localhost:9001 |
| Polaris Console | http://localhost:8183 |
| LibreDB Studio | http://localhost:3001 |

Tài khoản admin khởi tạo theo `API_BOOTSTRAP_ADMIN_*` trong `.env`. Các tài khoản nghiệp vụ khác cần được tạo và gán vai trò/cửa hàng qua chức năng quản trị.

## Nguồn dữ liệu và chạy batch

```bash
./scripts/backfill_data.sh --mode oltp

docker compose exec -T airflow-scheduler airflow dags unpause lakehouse_oltp_pipeline
docker compose exec -T airflow-scheduler airflow dags trigger lakehouse_oltp_pipeline

uv run --locked --package data-generator -- python scripts/simulate_web_traffic.py \
  --config generator/configs/small.yml --concurrency 5 --duration 300
```

Bộ sinh dữ liệu được mô tả trong [generator/README.md](generator/README.md). File JSONL lịch sử được upload vào MinIO là nguồn Landing thô; job Flink hiện tại đọc Kafka, nên việc upload file không tự đưa các file đó vào Gold.

## Dữ liệu phân tích và chỉ số

Gold OLTP có 6 dimension, 5 fact và 4 mart. Nhóm log có `fact_web_events` cùng 3 mart. Số dòng thực tế phụ thuộc bộ dữ liệu và các lần chạy pipeline.

[Danh mục chỉ số](docs/architecture/METRICS_CATALOG.md) mô tả công thức, grain, nguồn và giới hạn của doanh thu, giá vốn, tồn kho, chuyển đổi, độ trễ request, độ mới dữ liệu và sai lệch đối soát.

Dashboard lấy dữ liệu lịch sử qua Trino; các chỉ số vận hành cửa hàng/kho/giao vận lấy MySQL. API trả `data_source`, `is_degraded`, `degraded_reason` để thể hiện nguồn và trạng thái fallback.

## Tài liệu

- [Mục lục tài liệu](docs/README.md)
- [Phạm vi đồ án](docs/project/SCOPE.md)
- [Mô hình Lakehouse](docs/project/LAKEHOUSE_DESIGN_PLAN.md)
- [Schema OLTP](docs/architecture/OLTP_SCHEMA.md)
- [Hợp đồng access log](docs/architecture/ACCESS_LOG_DESIGN.md)
- [CDC](docs/architecture/CDC_DASHBOARD_DATA_SPEC.md)
- [Triển khai và vận hành](docs/runbook/README.md)
- [Sơ đồ cho tiểu luận](docs/diagrams/README.md)

CI hiện chạy kiểm tra cấu hình, cú pháp, lint, typecheck và build. Xem [CI runbook](docs/runbook/CI.md). Machine Learning nằm ngoài phạm vi triển khai hiện tại.
