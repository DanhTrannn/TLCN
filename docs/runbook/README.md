# Runbook

- [`lakehouse-local.md`](lakehouse-local.md): khởi động, bootstrap RBAC, smoke test và xử lý lỗi Polaris–Iceberg–Spark–Trino.
- [`startup-flow.md`](startup-flow.md): tóm tắt từng service làm gì khi khởi động theo profile.

Runbook TLCN bao phủ clean setup, service health, OLTP seed/generator, scheduled/manual batch run, rerun, replay, backfill, partial failure, fallback dataset và teardown.

## Base commands

```bash
cp .env.example .env
docker compose --profile core up -d --build
./scripts/grant_de_reader.sh
docker compose --profile batch up -d --build
docker compose --profile bi up -d --build
```

Profile `core` chỉ gồm MySQL ecommerce, Ecommerce API và Storefront.
Script grant chạy sau migration, cấp `SELECT` theo allowlist 16 bảng OLTP và
không cấp quyền đọc `customer_credentials`.

## Generator OLTP

```bash
docker compose --profile tools build generator
docker compose --profile tools run --rm generator export-sql \
  --config /app/configs/small.yml \
  --output /data/generator/small.sql
./scripts/import_generated_sql.sh data/generator/small.sql
```

File SQL nằm tại `data/generator/small.sql`, chạy trong một transaction và không được import lặp lại trên cùng database. Tài khoản demo được in ra terminal sau khi export.

## Access logs

Web/API thật phát một JSON event sau mỗi completed request. Fluent Bit tail Docker stdout,
buffer trên volume và upload gzip lên MinIO sau tối đa khoảng 15 phút:

```bash
docker compose --profile core --profile batch up -d --build
docker compose --profile batch logs -f fluent-bit
```

Sinh lịch sử access log deterministic, cùng identity master với SQL:

```bash
docker compose --profile tools run --rm generator export-logs \
  --config /app/configs/small.yml \
  --output-directory /data/generator/access-logs \
  --expected-requests 60000
./scripts/upload_generated_logs.sh data/generator/access-logs
```

Output local ở `data/generator/access-logs/landing/logs/`. Chi tiết về contract,
privacy, boundary 15 phút và cách kiểm tra Landing nằm tại
[`docs/architecture/access-logs.md`](../architecture/access-logs.md).

## Source web/admin

- Storefront: `http://localhost:3000`;
- API docs: `http://localhost:8000/docs`;
- Admin: `http://localhost:3000/admin`;
- Local admin: `admin@web.local` / `Admin@12345`.

Migration và bootstrap admin tự chạy khi `ecommerce-api` khởi động.

## Validation

```bash
uv lock --check
docker compose --profile core --profile batch --profile bi --profile tools config --quiet
uv run --locked --package ecommerce-api --extra dev -- pytest services/ecommerce-api/tests
uv run --locked --package data-generator --extra dev -- pytest generator/tests
npm --prefix apps/storefront ci --no-audit --no-fund
npm --prefix apps/storefront run typecheck
npm --prefix apps/storefront run build
```

GitHub Actions chạy cùng các kiểm tra này tại [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml). Không đưa secret production vào workflow; CI hiện chỉ cần quyền đọc repository.
