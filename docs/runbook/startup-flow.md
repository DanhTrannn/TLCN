# Quá trình khởi động theo service

Tài liệu mô tả từng service làm gì khi khởi động, theo thứ tự chạy trong
`docker-compose.yml`. Mọi container khởi động tạm đều là one-shot, idempotent và
chạy lại an toàn sau restart.

## Profile `core`

| Service | Việc làm khi khởi động |
|---|---|
| `mysql-ecommerce` | Khởi động MySQL 8.4 (utf8mb4, TZ UTC). Chạy script trong `/docker-entrypoint-initdb.d` (chỉ lần đầu tạo volume): `01-create-de-reader.sh` tạo user chỉ đọc `ecommerce_de_reader` cho pipeline. |
| `ecommerce-api` | Chờ `mysql-ecommerce` healthy → `alembic upgrade head` (migration) → seed catalog → bootstrap admin từ `API_BOOTSTRAP_ADMIN_*` → chạy uvicorn. Healthcheck qua `/health/ready`. |
| `storefront` | Chờ `ecommerce-api` healthy → chạy Next.js server. |

## Profile `tools`

| Service | Việc làm khi khởi động |
|---|---|
| `generator` | One-shot (chạy thủ công bằng `docker compose run`): export SQL/access log theo config, ghi vào volume `/data/generator`. |

## Profile `batch`

### Chuỗi MinIO → Polaris

| Service | Việc làm khi khởi động |
|---|---|
| `minio` | Khởi động S3 server và console. |
| `minio-init` | One-shot: `mc alias set` → tạo bucket `web-lakehouse` (nếu chưa có) → set anonymous none → liệt kê bucket. |
| `fluent-bit` | Chờ bucket sẵn sàng → tail stdout của containers tại `/var/lib/docker/containers`, buffer trên volume, gzip và upload lên MinIO sau tối đa khoảng 15 phút. |
| `postgres-polaris` | Khởi động Postgres 17 lưu metadata Polaris. |
| `polaris-bootstrap` | One-shot: chạy `polaris-admin-tool bootstrap` tạo realm (mặc định `POLARIS`) và root client credential. Idempotent: bỏ qua nếu realm đã tồn tại. |
| `polaris` | Chờ `polaris-bootstrap` và `minio-init` → khởi động REST catalog (`:8181`) và management API (`:8182`), CORS cho Polaris Console. |
| `polaris-init` | One-shot `bootstrap.sh`: tạo catalog `lakehouse` trỏ S3/MinIO → tạo principal role `spark_writer_role`/`trino_reader_role` và catalog role tương ứng → tạo service principals `spark_writer`, `trino_reader`, lưu credentials vào volume `polaris-client-credentials` (tái sử dụng nếu còn hợp lệ) → grant quyền tối thiểu (Spark `CATALOG_MANAGE_CONTENT`; Trino read privileges) → tạo 5 namespace `bronze`, `silver`, `gold`, `quarantine`, `system` → ghi `clients.env` và marker ready. |
| `polaris-console` | Chờ `polaris-init` → chạy web UI quản trị Polaris (`:8183`). |

### Spark

| Service | Việc làm khi khởi động |
|---|---|
| `spark-master` | Khởi động Spark master (`:7077`, UI `:8082`). |
| `spark-worker` | Chờ master → đăng ký worker (2 core, 2g mặc định, UI `:8083`). |
| `spark-client` (profile `lakehouse-tools`) | One-shot smoke test: chờ `clients.env` → `with-polaris-credentials.sh` thêm credential `spark_writer` và header `Polaris-Realm` vào `spark-defaults.conf` → chạy `spark-sql -f smoke.sql` (ghi bảng smoke qua Polaris). |

### Airflow

| Service | Việc làm khi khởi động |
|---|---|
| `postgres-airflow` | Khởi động Postgres 16 cho Airflow. |
| `airflow-init` | One-shot: `airflow db migrate` và tạo admin user. |
| `airflow-webserver` | Chờ `airflow-init` → chạy webserver (`:8080`). |
| `airflow-scheduler` | Chờ `airflow-init` → chạy scheduler (LocalExecutor, `LOAD_EXAMPLES=false`, DAG mặc định paused). |

## Profile `bi`

| Service | Việc làm khi khởi động |
|---|---|
| `trino` | `start.sh`: chờ `clients.env` → nạp credential `trino_reader` vào env → chạy Trino với catalog `lakehouse` (Polaris + MinIO). Healthcheck `/v1/info`. |
| `postgres-superset` | Chờ `trino` healthy → khởi động Postgres 16 cho Superset. |
| `superset-init` | One-shot: `superset db upgrade` → tạo admin → `superset init` → `import_datasources` (nạp datasource Trino từ `datasources.yml`). |
| `superset` | Chờ `superset-init` → chạy gunicorn webserver (`:8088`). |

## Chuỗi phụ thuộc tóm tắt

```text
mysql-ecommerce → ecommerce-api → storefront
minio-init → (fluent-bit, polaris)
polaris-bootstrap → polaris → polaris-init → (polaris-console, spark-master, spark-worker, trino, airflow)
spark-worker → spark-client
trino → superset-init → superset
```

## Ghi chú

- Credentials Polaris được tạo một lần rồi tái sử dụng qua volume `polaris-client-credentials`; restart container không làm mất catalog metadata.
- Chuỗi init đều idempotent nên `docker compose up` lặp lại không tạo trùng entity.
- Khởi động đầy đủ: `docker compose --profile core --profile batch --profile bi up -d --build`, sau đó kiểm tra bằng `./scripts/lakehouse_smoke.sh`.