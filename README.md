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
- review verified-purchase hiển thị ngay và admin hậu kiểm ẩn/khôi phục, cùng
  wishlist/search/filter;
- admin có dashboard vận hành riêng; quản lý/search catalog, inventory, coupon, review, customer và order;
- structured access log ở biên FastAPI, Fluent Bit buffer/đóng gzip 15 phút vào MinIO;
- seed catalog và generator xuất SQL cùng access log deterministic.

Phạm vi và tiêu chí nghiệm thu được chốt tại [`docs/project/scope.md`](docs/project/scope.md); kiến trúc Lakehouse mục tiêu nằm tại [`docs/project/lakehouse-plan.md`](docs/project/lakehouse-plan.md).

## Trạng thái triển khai

| Khối | Trạng thái | Vai trò |
|---|---|---|
| Storefront, API, MySQL | Hoạt động | Tạo và quản lý dữ liệu OLTP |
| SQL data generator | Hoạt động | Sinh dữ liệu lịch sử có thể tái lập |
| Access-log source | Hoạt động | FastAPI JSON contract, Fluent Bit → MinIO và synthetic log generator |
| Catalog/storage | Hoạt động | MinIO, Polaris 1.6.0, PostgreSQL 16.8 metadata và Polaris Console |
| Compute/query | Hoạt động | Spark 3.5.9 + Iceberg 1.10.1, Trino reader/admin và smoke test end-to-end |
| Pipeline/BI/ML assets | Đang phát triển | DAG, transformation, dashboard và model |

Không chạy truy vấn phân tích nặng trên primary OLTP. Phân tích được thực hiện trên tầng Lakehouse (Iceberg/Trino/Superset).

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
FastAPI stdout ──Fluent Bit──15-minute gzip───┤
                                                ▼
                         MinIO Landing → Spark → Iceberg
                                                │
                                   Polaris → Trino → Superset
                                                └──────→ ML

Generator (host CLI) ──file .sql──▶ MySQL OLTP
                     └─JSONL.gz + manifest──▶ Landing/replay
```

Các boundary và dependency rule chi tiết nằm tại [`docs/architecture/project-structure.md`](docs/architecture/project-structure.md).

## Tech stack

| Lớp | Công nghệ |
|---|---|
| Web | Next.js 15, React 19, TypeScript, Tailwind CSS |
| API | FastAPI, SQLAlchemy 2, Alembic, Pydantic |
| OLTP | MySQL 8.4.5, InnoDB, UTC, VND |
| Python workspace | Python 3.11, uv (uv workspace: `ecommerce-api`, `data-generator`, `batch-pipeline`) |
| Metadata DB | PostgreSQL 16.8 (hợp nhất cho Polaris, Airflow, Superset) |
| Data platform | Airflow 2.10.5, Spark 3.5.9, Iceberg 1.10.1, Polaris 1.6.0, MinIO |
| Serving/BI | Trino 483, Apache Superset 4.1.2 |
| Local runtime | Docker Engine, Docker Compose v2 |

## Cấu trúc repository

```text
apps/                  Giao diện người dùng và admin (Storefront Next.js)
services/              Business API (FastAPI) và application services
database/              Alembic migrations và catalog seed
generator/             Synthetic OLTP SQL và access-log generator (CLI package)
pipelines/             Spark batch jobs và lakehouse module (batch-pipeline)
airflow/               DAG và cấu hình orchestration
infrastructure/        Docker images, configs (Spark, Trino, Polaris, Superset, Fluent Bit, Postgres)
docs/                  Scope, architecture, contract, design system và runbook
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
Email:    admin@web.local
Password: Admin@12345
```

Đây chỉ là credential mặc định cho môi trường local. Hãy thay các secret trong `.env` trước khi deploy ra môi trường khác.

## Sinh và import dữ liệu

Chạy generator trực tiếp trên máy host qua `uv`:

```bash
# 1. Sinh dữ liệu SQL nhỏ
uv run --locked --package data-generator -- generator export-sql \
  --config generator/configs/small.yml \
  --output data/generator/small.sql

# 2. Import vào MySQL
./scripts/import_generated_sql.sh data/generator/small.sql
```

`small.yml` tạo 500 customer, 60 product, 240 variant và 3.000 order trong 12 tháng. Profile có mùa vụ Tết/ngày đôi, peak 0h theo giờ Việt Nam, coupon theo campaign, review, cancellation và wishlist conversion có quan hệ phân tích. File SQL chạy trong một transaction, giữ nguyên FK/CHECK và không được import lặp lại trên cùng database. Chi tiết tại [`generator/README.md`](generator/README.md).

Sinh thêm access log cùng danh tính master và mùa vụ:

```bash
uv run --locked --package data-generator -- generator export-logs \
  --config generator/configs/small.yml \
  --output-directory data/generator/access-logs \
  --expected-requests 60000
```

Contract, cơ chế 15 phút và giới hạn phân tích nằm tại
[`docs/architecture/access-logs.md`](docs/architecture/access-logs.md).

## Lệnh vận hành

| Profile | Thành phần |
|---|---|
| `core` | MySQL, Ecommerce API, Storefront |
| `batch` | Fluent Bit, MinIO, PostgreSQL, Polaris, Polaris Console, Spark và Airflow |
| `bi` | Trino, PostgreSQL và Superset |
| `lakehouse-tools` | Spark client dùng cho smoke test/SQL ghi qua Polaris |

Xem log core:

```bash
docker compose --profile core logs -f ecommerce-api storefront mysql
```

Khởi động Lakehouse/BI sau khi profile `core` đã healthy:

```bash
docker compose --profile core --profile batch --profile bi up -d --build
./scripts/lakehouse_smoke.sh
```

Lần build đầu tải image lớn và build Polaris Console trực tiếp từ commit đã pin của `apache/polaris-tools`. Hướng dẫn, URL, RBAC và troubleshooting nằm tại [`docs/runbook/lakehouse-local.md`](docs/runbook/lakehouse-local.md).

Dừng container nhưng giữ volume:

```bash
docker compose --profile core --profile batch --profile bi down
```

Xóa toàn bộ volume để dựng lại môi trường sạch:

```bash
docker compose --profile core --profile batch --profile bi --profile tools --profile lakehouse-tools \
  down -v --remove-orphans
```

Lệnh cuối xóa dữ liệu MySQL, Airflow, MinIO và Superset trên máy local.

## Phát triển

### Python với uv

Kiểm tra lockfile:

```bash
uv lock --check
```

Chạy test Ecommerce API:

```bash
uv run --locked --package ecommerce-api --extra dev -- \
  pytest services/ecommerce-api/tests
```

Chạy generator trực tiếp:

```bash
uv run --locked --package data-generator -- \
  generator --help
```

### Storefront

```bash
cd apps/storefront
npm ci
npm run dev
```

API mặc định phải chạy tại `http://localhost:8000`. Hướng dẫn component tại [`apps/storefront/README.md`](apps/storefront/README.md) và [`services/ecommerce-api/README.md`](services/ecommerce-api/README.md).

## Kiểm tra repository

```bash
docker compose --profile core --profile batch --profile bi --profile tools --profile lakehouse-tools config --quiet
```

Trước khi tạo commit nên chạy thêm:

```bash
uv run --locked --package ecommerce-api --extra dev -- \
  pytest services/ecommerce-api/tests

uv run --locked --package data-generator --extra dev -- \
  pytest generator/tests

npm --prefix apps/storefront ci --no-audit --no-fund
npm --prefix apps/storefront run typecheck
npm --prefix apps/storefront run build
```

## Continuous Integration

Workflow [`.github/workflows/ci.yml`](.github/workflows/ci.yml) chạy khi push vào `main`/`master`, khi mở hoặc cập nhật pull request và khi chạy thủ công.

Ba job độc lập:

- `Repository validation`: kiểm tra Docker Compose config;
- `Python tests`: chạy test Ecommerce API và data generator bằng `uv.lock`;
- `Storefront checks`: cài bằng `npm ci`, type-check và production build.

Workflow chỉ có quyền `contents: read`, tự hủy run cũ trên cùng ref và dùng cache dependency của `uv`/npm.

## Tài liệu

| Tài liệu | Mục đích |
|---|---|
| [`docs/project/scope.md`](docs/project/scope.md) | Nguồn yêu cầu và acceptance ưu tiên cao nhất |
| [`docs/project/lakehouse-plan.md`](docs/project/lakehouse-plan.md) | Kế hoạch Iceberg, Polaris, Trino, Medallion, DQ và maintenance |
| [`docs/architecture/oltp-schema.md`](docs/architecture/oltp-schema.md) | Logical schema, invariant, transaction và index |
| [`docs/project/web-plan.md`](docs/project/web-plan.md) | Kế hoạch triển khai source website |
| [`docs/architecture/project-structure.md`](docs/architecture/project-structure.md) | Kiến trúc monorepo và dependency boundary |
| [`docs/runbook/README.md`](docs/runbook/README.md) | Mục lục setup và vận hành |
| [`docs/runbook/lakehouse-local.md`](docs/runbook/lakehouse-local.md) | Chạy Polaris/Iceberg/Spark/Trino và smoke test |
| [`skills/oltp-design/SKILL.md`](skills/oltp-design/SKILL.md) | Nguyên tắc thiết kế OLTP tái sử dụng |

Mục lục đầy đủ: [`docs/README.md`](docs/README.md).
