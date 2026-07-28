# TLCN OLTP Batch Data Lakehouse

Monorepo cho đề tài:

> Xây dựng Data Lakehouse xử lý theo lô cho dữ liệu MySQL OLTP và dự đoán khả năng khách hàng mua lại trên website thương mại điện tử tối giản.

## Phạm vi hiện hành

TLCN chỉ dùng dữ liệu từ MySQL OLTP:

- customer và catalog;
- wishlist và cart;
- order, order item và payment;
- order status history;
- inventory.


## Trạng thái

Repository đã có Storefront, Ecommerce API, MySQL migration/seed, admin console và source transaction flow. Hạ tầng Airflow, Spark/Delta/MinIO, Superset và ML đang được tổ chức để tiếp tục triển khai pipeline OLTP-only.

## Bắt đầu

Yêu cầu:

- Docker Engine và Docker Compose v2;
- `uv` 0.11.32 trở lên nếu chạy Python trực tiếp;
- khoảng 8 GB RAM nếu chạy đồng thời `core`, `batch` và `bi`.

```bash
cp .env.example .env
docker compose --profile core up -d --build
./scripts/grant_de_reader.sh
```

Profile `core` gồm:

- MySQL ecommerce;
- Ecommerce API;
- Storefront.

Địa chỉ:

| Thành phần | URL |
|---|---|
| Storefront | `http://localhost:3000` |
| Admin console | `http://localhost:3000/admin` |
| Ecommerce API docs | `http://localhost:8000/docs` |

Script grant chỉ cho DE reader đọc 12 bảng nguồn OLTP; bảng
`customer_credentials` không được đưa vào pipeline.

Admin local mặc định:

- Email: `admin@tlcn.local`
- Password: `Admin@12345`

Đổi credential mặc định trước khi dùng ngoài môi trường local.

## Chạy platform

```bash
docker compose --profile core --profile batch --profile bi up -d --build
```

| Profile | Thành phần |
|---|---|
| `core` | MySQL ecommerce, API, Storefront |
| `tools` | OLTP generator |
| `batch` | MinIO, Spark, Airflow |
| `bi` | MySQL analytics, Superset |

Các URL bổ sung:

| Thành phần | URL |
|---|---|
| Airflow | `http://localhost:8080` |
| MinIO console | `http://localhost:9001` |
| Spark master UI | `http://localhost:8082` |
| Superset | `http://localhost:8088` |

## Generator OLTP

Sinh file SQL deterministic trên host:

```bash
docker compose --profile tools build generator
docker compose --profile tools run --rm generator export-sql \
  --config /app/configs/small.yml \
  --output /data/generator/small.sql
```

Import sau khi `core` healthy:

```bash
./scripts/import_generated_sql.sh data/generator/small.sql
```

`small.yml` tạo 500 customer, 60 product, 240 variant và 3.000 order trong 12 tháng. CLI in tài khoản demo sau khi export. Chi tiết tại `generator/README.md`.

## Phát triển Python với uv

Kiểm tra lockfile:

```bash
uv lock --check
```

Test Ecommerce API:

```bash
UV_PROJECT_ENVIRONMENT=.venv-ecommerce uv run --locked --package tlcn-ecommerce-api --extra dev -- pytest services/ecommerce-api/tests
```

Chạy CLI:

```bash
UV_PROJECT_ENVIRONMENT=.venv-generator uv run --locked --package tlcn-data-generator -- tlcn-generator --help
UV_PROJECT_ENVIRONMENT=.venv-batch uv run --locked --package tlcn-batch-pipeline -- tlcn-pipeline --help
UV_PROJECT_ENVIRONMENT=.venv-ml uv run --locked --package tlcn-repurchase-ml -- tlcn-repurchase-ml --help
```


## Kiểm tra

```bash
python3 scripts/validate_structure.py
docker compose --profile core --profile batch --profile bi config --quiet
docker compose --profile core --profile batch --profile bi ps
```

Xem log:

```bash
docker compose --profile core logs -f ecommerce-api storefront mysql-ecommerce
```

Dừng nhưng giữ volume:

```bash
docker compose --profile core --profile batch --profile bi down
```

Xóa cả persistent volumes chỉ khi muốn dựng lại môi trường sạch:

```bash
docker compose --profile core --profile batch --profile bi --profile tools down -v --remove-orphans
```

## Tài liệu nguồn

- `remake.md`: phạm vi TLCN OLTP-only và acceptance hiện hành.
- `schema.md`: logical schema OLTP và transaction catalogue.
- `web-plan.md`: implementation plan của source website.
- `PROJECT_STRUCTURE.md`: kiến trúc monorepo và dependency boundary.
- `skills/oltp-design.md`: nguyên tắc thiết kế OLTP.
