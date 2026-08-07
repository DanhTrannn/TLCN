# TLCN E-commerce Data Platform

Monorepo cho đề tài **Data Lakehouse xử lý theo lô từ MySQL OLTP và structured web access log, phục vụ BI và dự đoán khả năng khách hàng mua lại**. Website **D&K** đóng vai trò hệ thống nguồn, tạo dữ liệu có kiểm soát cho phần Data Engineering, BI và ML.

## Phạm vi

Nguồn dữ liệu chính thức của TLCN gồm 16 bảng MySQL OLTP và structured web access log được rotate/nén theo micro-batch. Clickstream frontend/mobile, analytics session, Kafka và streaming nằm ngoài giai đoạn này.

Hệ thống nguồn đã hỗ trợ:

- đăng ký, đăng nhập và phân quyền customer/admin;
- catalog theo product/variant, search, filter và sort;
- wishlist và anonymous/customer cart;
- checkout có kiểm tra tồn kho, coupon và ghi order/payment atomically;
- lifecycle `paid → confirmed → completed`, hủy order `paid`, full refund và hoàn tồn kho;
- review sau mua với moderation, cùng wishlist/search/filter;
- admin có dashboard vận hành riêng; quản lý/search catalog, inventory, coupon, review, customer và order;
- seed catalog và generator xuất bộ dữ liệu SQL deterministic.

Phạm vi và tiêu chí nghiệm thu được chốt tại [`docs/project/scope.md`](docs/project/scope.md); kiến trúc Lakehouse mục tiêu nằm tại [`docs/project/lakehouse-plan.md`](docs/project/lakehouse-plan.md).

## Trạng thái triển khai

| Khối | Trạng thái | Vai trò |
|---|---|---|
| Storefront, API, MySQL | Hoạt động | Tạo và quản lý dữ liệu OLTP |
| SQL data generator | Hoạt động | Sinh dữ liệu lịch sử có thể tái lập |
| Batch/Lakehouse | Khung triển khai | Extract, Bronze, Silver, Gold, reconciliation |
| BI/ML | Khung triển khai | Dashboard và bài toán mua lại |

Không chạy truy vấn phân tích nặng trên primary OLTP. Pipeline chỉ được đọc các bảng nằm trong source allowlist bằng tài khoản DE reader.

## Kiến trúc

```text
Customer/Admin
      │
      ▼
Next.js Storefront ──HTTP──▶ FastAPI Ecommerce API
                                   │
                              short transaction
                                   │
                                   ▼
                              MySQL OLTP ───────┐
                                               │
Structured access log ──15-minute files───────┤
                                               ▼
                         MinIO Landing → Spark → Iceberg
                                               │
                                  Polaris → Trino → Superset
                                               └──────→ ML

SQL Generator ──file .sql──▶ MySQL OLTP
```

Các boundary và dependency rule chi tiết nằm tại [`docs/architecture/project-structure.md`](docs/architecture/project-structure.md).

## Tech stack

| Lớp | Công nghệ |
|---|---|
| Web | Next.js 15, React 19, TypeScript, Tailwind CSS |
| API | FastAPI, SQLAlchemy 2, Alembic, Pydantic |
| OLTP | MySQL 8.4, InnoDB, UTC, VND |
| Python workspace | Python 3.11, uv |
| Data platform mục tiêu | Airflow, Spark, Apache Iceberg, Apache Polaris, MinIO |
| Serving/BI mục tiêu | Trino, Apache Superset |
| Local runtime | Docker Engine, Docker Compose v2 |

## Cấu trúc repository

```text
apps/                  Giao diện người dùng và admin
services/              Business API và application services
database/              Alembic migrations và catalog seed
generator/             Synthetic OLTP SQL generator
pipelines/             Batch extraction và transformation
airflow/               DAG và cấu hình orchestration
ml/                    Feature, training và scoring workflow
dashboards/            BI assets và dashboard exports
quality/               Data-quality rules, fixtures và reports
infrastructure/        Docker image, MySQL và Superset config
docs/                  Scope, architecture, contract và runbook
scripts/               Lệnh vận hành dùng lại được
skills/                Nguyên tắc thiết kế tái sử dụng
tests/                 Test cross-component và test data
```

Không đặt source code, tài liệu thiết kế hoặc dữ liệu sinh trực tiếp ở thư mục gốc. Root chỉ giữ entrypoint và cấu hình cấp repository.

## Chạy nhanh

### 1. Yêu cầu

- Docker Engine và Docker Compose v2;
- Git;
- `uv` 0.11.32 nếu phát triển Python trực tiếp;
- Node.js 22 nếu phát triển Storefront ngoài Docker.

### 2. Khởi tạo môi trường

```bash
cp .env.example .env
docker compose --profile core up -d --build
```

`ecommerce-api` tự chạy Alembic migration, seed catalog và bootstrap tài khoản admin khi khởi động.

Kiểm tra trạng thái:

```bash
docker compose --profile core ps
curl -fsS http://localhost:8000/health/ready
```

### 3. Truy cập

| Thành phần | Địa chỉ |
|---|---|
| Storefront | `http://localhost:3000` |
| Product catalog | `http://localhost:3000/products` |
| Admin console | `http://localhost:3000/admin` |
| OpenAPI | `http://localhost:8000/docs` |

Tài khoản admin local:

```text
Email:    admin@tlcn.local
Password: Admin@12345
```

Đây chỉ là credential mặc định cho môi trường local. Hãy thay các secret trong `.env` trước khi deploy ra môi trường khác.

## Sinh và import dữ liệu

Build generator và xuất bộ dữ liệu nhỏ:

```bash
docker compose --profile tools build generator
docker compose --profile tools run --rm generator export-sql \
  --config /app/configs/small.yml \
  --output /data/generator/small.sql
```

Import vào chính MySQL mà API đang sử dụng:

```bash
./scripts/import_generated_sql.sh data/generator/small.sql
```

`small.yml` tạo 500 customer, 60 product, 240 variant và 3.000 order trong 12 tháng. Profile có mùa vụ Tết/ngày đôi, peak 0h theo giờ Việt Nam, coupon theo campaign, review, cancellation và wishlist conversion có quan hệ phân tích. File SQL chạy trong một transaction, giữ nguyên FK/CHECK và không được import lặp lại trên cùng database. Chi tiết tại [`generator/README.md`](generator/README.md).

## Lệnh vận hành

| Profile | Thành phần |
|---|---|
| `core` | MySQL ecommerce, Ecommerce API, Storefront |
| `tools` | SQL data generator |
| `batch` | Hiện là scaffold MinIO/Spark/Airflow; mục tiêu bổ sung Iceberg và Polaris |
| `bi` | Hiện là scaffold; mục tiêu Trino và Superset |

Xem log core:

```bash
docker compose --profile core logs -f ecommerce-api storefront mysql-ecommerce
```

Khởi động phần mở rộng Batch/BI sau khi profile `core` đã healthy:

```bash
./scripts/grant_de_reader.sh
docker compose --profile core --profile batch --profile bi up -d --build
```

Dừng container nhưng giữ volume:

```bash
docker compose --profile core --profile batch --profile bi down
```

Xóa toàn bộ volume để dựng lại môi trường sạch:

```bash
docker compose --profile core --profile batch --profile bi --profile tools \
  down -v --remove-orphans
```

Lệnh cuối xóa dữ liệu MySQL, Airflow, MinIO và Superset trên máy local.

## Phát triển

### Python với uv

Kiểm tra lockfile:

```bash
uv lock --check
```

Chạy test Ecommerce API trong environment riêng:

```bash
UV_PROJECT_ENVIRONMENT=.venv-ecommerce \
  uv run --locked --package tlcn-ecommerce-api --extra dev -- \
  pytest services/ecommerce-api/tests
```

Chạy generator trực tiếp:

```bash
UV_PROJECT_ENVIRONMENT=.venv-generator \
  uv run --locked --package tlcn-data-generator -- \
  tlcn-generator --help
```

### Storefront

```bash
cd apps/storefront
npm install
npm run dev
```

API mặc định phải chạy tại `http://localhost:8000`. Hướng dẫn component tại [`apps/storefront/README.md`](apps/storefront/README.md) và [`services/ecommerce-api/README.md`](services/ecommerce-api/README.md).

## Kiểm tra repository

```bash
python3 scripts/validate_structure.py
docker compose --profile core --profile batch --profile bi --profile tools config --quiet
```

Trước khi tạo commit nên chạy thêm:

```bash
UV_PROJECT_ENVIRONMENT=.venv-ecommerce \
  uv run --locked --package tlcn-ecommerce-api --extra dev -- \
  pytest services/ecommerce-api/tests

npm --prefix apps/storefront run typecheck
npm --prefix apps/storefront run build
```

## Tài liệu

| Tài liệu | Mục đích |
|---|---|
| [`docs/project/scope.md`](docs/project/scope.md) | Nguồn yêu cầu và acceptance ưu tiên cao nhất |
| [`docs/project/lakehouse-plan.md`](docs/project/lakehouse-plan.md) | Kế hoạch Iceberg, Polaris, Trino, Medallion, DQ và maintenance |
| [`docs/architecture/oltp-schema.md`](docs/architecture/oltp-schema.md) | Logical schema, invariant, transaction và index |
| [`docs/project/web-plan.md`](docs/project/web-plan.md) | Kế hoạch triển khai source website |
| [`docs/architecture/project-structure.md`](docs/architecture/project-structure.md) | Kiến trúc monorepo và dependency boundary |
| [`docs/runbook/README.md`](docs/runbook/README.md) | Setup, vận hành và xử lý sự cố |
| [`docs/source-contracts/README.md`](docs/source-contracts/README.md) | Contract nguồn MySQL OLTP và access log |
| [`skills/oltp-design/SKILL.md`](skills/oltp-design/SKILL.md) | Nguyên tắc thiết kế OLTP tái sử dụng |

Mục lục đầy đủ: [`docs/README.md`](docs/README.md).
