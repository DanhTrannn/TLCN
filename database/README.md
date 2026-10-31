# Schema MySQL và dữ liệu khởi tạo

`database/schema.sql` là file DDL vật lý duy nhất của hệ thống nguồn, dành cho MySQL 8.4. File tạo 28 bảng cùng khóa chính, khóa ngoại, index, CHECK, cột sinh tự động và timestamp mặc định/`ON UPDATE`.

Schema chỉ chứa định nghĩa cấu trúc. Catalog/admin do seed tạo; lịch sử giao dịch tổng hợp do generator nạp.

## Cấu trúc thư mục

| Đường dẫn | Vai trò |
|---|---|
| [schema.sql](schema.sql) | Tạo schema cuối cùng trên database trống |
| [seeds/](seeds/) | Catalog, tồn mở đầu và bootstrap admin |
| [OLTP_SCHEMA.md](../docs/architecture/OLTP_SCHEMA.md) | Tham chiếu cột, quan hệ và quy tắc nghiệp vụ |
| [ORM models](../services/ecommerce-api/app/models/) | Ánh xạ SQLAlchemy dùng trong API |

## Khởi tạo bằng Docker Compose

Từ thư mục gốc repo, trong lần cài đặt đầu tiên:

```bash
cp .env.example .env
docker compose --profile core up -d --wait mysql
```

Compose mount file SQL read-only tại:

```text
database/schema.sql
  → /docker-entrypoint-initdb.d/10-ecommerce-schema.sql
```

MySQL tự tạo database/user theo `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD`, rồi chạy SQL khi data directory trống. File không cố định tên database bằng lệnh `USE`.

Sau khi MySQL sẵn sàng, API chạy `database.seeds.seed_catalog` rồi khởi động FastAPI. Seed có thể chạy lại bằng:

```bash
docker compose exec -T ecommerce-api python -m database.seeds.seed_catalog
```

Seed không tạo bảng. Schema phải tồn tại trước khi chạy seed. `make seed` chạy bằng uv trên host; cần API_DATABASE_URL tới port MySQL trên host và API_SECRET_KEY hợp lệ, không dùng hostname mysql của mạng Docker từ host.

## Nạp SQL thủ công

Chỉ dùng với database trống đã được tạo. Với MySQL chạy trong Compose:

```bash
docker compose exec -T mysql sh -c \
  'MYSQL_PWD="$MYSQL_PASSWORD" exec mysql --user="$MYSQL_USER" --database="$MYSQL_DATABASE"' \
  < database/schema.sql
```

File dùng `CREATE TABLE` và không có `DROP TABLE` hoặc dữ liệu mẫu. Nó tạm tắt kiểm tra FK trong session để tạo các bảng có tham chiếu vòng, rồi khôi phục cấu hình FK.

## Database đang có dữ liệu

- Docker chỉ chạy thư mục init khi data directory trống. Restart container hoặc sửa file SQL không tự cập nhật volume đã có.
- Database đã khớp schema hiện tại tiếp tục dùng được; dữ liệu và bảng quản lý phiên bản cũ, nếu có, được giữ nguyên.
- Với database khác cấu trúc, so sánh `SHOW CREATE TABLE` với file SQL và áp dụng các câu `ALTER TABLE` phù hợp.
- API không tự nâng cấp schema. Không import file bootstrap lên database đã có bảng.

## Khi thay đổi schema

1. Cập nhật `database/schema.sql`.
2. Cập nhật các SQLAlchemy model tương ứng.
3. Áp dụng `ALTER TABLE` riêng cho database hiện có cần thay đổi.
4. Cập nhật tài liệu schema và ERD.

DDL hiện có 28 bảng, 315 cột, 50 FK, 49 UNIQUE key và 79 CHECK. [ERD hiện tại](../docs/diagram/13-erd-mysql-physical.drawio) dùng FK vật lý; quan hệ `orders.staff_id → customers.customer_id` hiện chỉ có trong ORM, chưa được cưỡng chế bởi FK trong SQL.

## Biên giới Data Engineering

Batch/CDC lấy 27 trong 28 bảng; `customer_credentials` bị loại vì chứa thông tin xác thực. Các bảng fact/dimension/mart nằm ở Iceberg, không được tạo bởi file MySQL này.

Metadata của Airflow và Polaris nằm ở PostgreSQL và vẫn do các dịch vụ tương ứng quản lý.
