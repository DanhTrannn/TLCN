# Lakehouse local: Polaris, Iceberg, Spark và Trino

## 1. Thành phần và ranh giới

Stack local triển khai đúng dependency trong `lakehouse-plan.md`:

```text
MinIO ── lưu Landing + Iceberg data/metadata files
  ▲
  │ vended S3 credentials
Polaris 1.5.0 ── Iceberg REST Catalog ── PostgreSQL metadata
  ▲
  ├── Spark 3.5.9 + Iceberg 1.10.1: writer duy nhất
  ├── Trino 483: reader/query engine
  └── Polaris Console: quản trị catalog/RBAC

Superset ── SQLAlchemy/Trino ── Trino ── Polaris ── Iceberg
```

Polaris không chứa file Parquet và không chạy query. PostgreSQL Polaris chỉ giữ catalog/RBAC metadata; MinIO mới giữ file Iceberg. Superset không kết nối MySQL OLTP hoặc MinIO trực tiếp.

## 2. Chuẩn bị

```bash
cp .env.example .env
```

Đổi tối thiểu các biến sau trước khi dùng ngoài máy cá nhân:

- `MINIO_ROOT_PASSWORD`;
- `POLARIS_ROOT_CLIENT_SECRET`;
- `POLARIS_DB_PASSWORD`;
- `SUPERSET_SECRET_KEY`;
- `SUPERSET_ADMIN_PASSWORD`.

Nếu truy cập bằng hostname/IP khác `localhost`, cập nhật đồng bộ:

- `POLARIS_PUBLIC_API_URL=http://<host>:8181`;
- `POLARIS_CONSOLE_ORIGIN=http://<host>:8183`;

Console gọi thẳng Polaris từ trình duyệt, nên origin CORS phải khớp chính xác.

## 3. Khởi động

Catalog và compute/query layer:

```bash
docker compose --profile batch --profile bi up -d --build
```

Khởi động luôn source web:

```bash
docker compose --profile core --profile batch --profile bi up -d --build
```

Lần đầu cần tải các image lớn và build hai image local:

- `lakehouse-spark:3.5.9-iceberg-1.10.1`;
- `polaris-console:1.4.0-e5fea020` từ commit đã pin của `apache/polaris-tools`.

## 4. Bootstrap tự động

Thứ tự startup được khóa bằng health/dependency condition:

1. `minio-init` tạo private bucket `web-lakehouse`;
2. `polaris-bootstrap` tạo schema JDBC và realm `POLARIS` trong PostgreSQL;
3. `polaris-init` tạo catalog `lakehouse` trỏ tới `s3://web-lakehouse/warehouse`;
4. tạo namespaces `bronze`, `silver`, `gold`, `quarantine`, `system`;
5. tạo `spark_writer` với `CATALOG_MANAGE_CONTENT`;
6. tạo `trino_reader` chỉ có metadata/read-data privileges;
7. credential được giữ trong named volume `polaris-client-credentials`, không commit vào repository.

Bootstrap có thể chạy lại. Nếu credential volume còn hợp lệ, script tái sử dụng credential thay vì rotate.

## 5. Địa chỉ local

| Thành phần | URL | Ghi chú |
|---|---|---|
| Airflow | `http://localhost:8080` | Orchestration |
| Spark master UI | `http://localhost:8082` | Compute status |
| Spark worker UI | `http://localhost:8083` | Executor status |
| Trino | `http://localhost:8084` | Query engine |
| Superset | `http://localhost:8088` | BI |
| Polaris API | `http://localhost:8181` | REST/Management API |
| Polaris health | `http://localhost:8182/q/health` | Management port |
| Polaris Console | `http://localhost:8183` | Catalog/RBAC UI |
| MinIO Console | `http://localhost:9001` | Object storage UI |

Đăng nhập Polaris Console bằng `POLARIS_ROOT_CLIENT_ID`, `POLARIS_ROOT_CLIENT_SECRET` và realm `POLARIS` trong `.env`. Không dùng root credential cho Spark/Trino; hai service dùng principal riêng do bootstrap tạo.

## 6. Smoke test end-to-end

Khởi động thêm Trino, sau đó chạy:

```bash
./scripts/lakehouse_smoke.sh
```

Script thực hiện:

1. Spark tạo/append bảng Iceberg `lakehouse.system.stack_smoke` qua Polaris;
2. Iceberg ghi data/metadata file vào MinIO;
3. Trino reader query cùng bảng qua Polaris.

Kiểm tra thủ công:

```bash
docker compose --profile batch --profile bi exec trino \
  trino --execute "SHOW SCHEMAS FROM lakehouse"

docker compose --profile batch --profile bi exec trino \
  trino --execute "SELECT * FROM lakehouse.system.stack_smoke"
```

Trino không có quyền tạo, sửa hoặc xóa bảng. Nếu cần thao tác ghi, dùng Spark client/pipeline.

## 7. Quan sát và xử lý lỗi

```bash
docker compose --profile batch --profile bi ps
docker compose --profile batch logs --tail=200 postgres-polaris polaris-bootstrap polaris polaris-init
docker compose --profile batch logs --tail=200 minio minio-init spark-master spark-worker
docker compose --profile bi logs --tail=200 trino superset-init superset
```

Các lỗi thường gặp:

- Console bị CORS: kiểm tra `POLARIS_CONSOLE_ORIGIN` khớp URL đang mở;
- Spark/Trino báo OAuth: kiểm tra `polaris-init` hoàn tất và volume credential tồn tại;
- Spark/Trino không truy cập được object storage: kiểm tra catalog đang cấp endpoint nội bộ `http://minio:9000`;
- đổi root secret trên database cũ: phải giữ secret cũ hoặc dựng lại volume Polaris trong môi trường local;
- thay phiên bản Polaris: đọc release note và chạy schema upgrade theo admin-tool, không tự nâng image trên metadata cũ.

## 8. Dừng và reset

Giữ dữ liệu:

```bash
docker compose --profile core --profile batch --profile bi down
```

Reset toàn bộ môi trường local, gồm MySQL, MinIO, Polaris metadata, Airflow và Superset:

```bash
docker compose --profile core --profile batch --profile bi --profile tools --profile lakehouse-tools \
  down -v --remove-orphans
```

Không xóa object trực tiếp dưới `web-lakehouse/warehouse`; maintenance phải chạy bằng Iceberg procedure để không làm lệch metadata.

## 9. Nguồn cấu hình tham chiếu

- [Apache Polaris 1.5.0](https://polaris.apache.org/downloads/1.5.0/);
- [Apache Polaris Tools](https://github.com/apache/polaris-tools);
- [Polaris Console README](https://github.com/apache/polaris-tools/blob/main/console/README.md);
- [Iceberg Spark catalog configuration](https://iceberg.apache.org/docs/latest/spark-configuration/#catalogs);
- [Trino Iceberg REST catalog](https://trino.io/docs/current/object-storage/metastores.html#iceberg-rest-catalog).
