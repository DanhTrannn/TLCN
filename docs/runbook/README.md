# Runbook

Runbook TLCN bao phủ clean setup, service health, OLTP seed/generator, scheduled/manual batch run, rerun, replay, backfill, partial failure, fallback dataset và teardown.

## Base commands

```bash
cp .env.example .env
docker compose --profile core up -d --build
./scripts/grant_de_reader.sh
docker compose --profile batch up -d --build
docker compose --profile bi up -d --build
python3 scripts/validate_structure.py
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

## Source web/admin

- Storefront: `http://localhost:3000`;
- API docs: `http://localhost:8000/docs`;
- Admin: `http://localhost:3000/admin`;
- Local admin: `admin@tlcn.local` / `Admin@12345`.

Migration và bootstrap admin tự chạy khi `ecommerce-api` khởi động.

## Validation

```bash
uv lock --check
python3 scripts/validate_structure.py
docker compose --profile core --profile batch --profile bi --profile tools config --quiet
UV_PROJECT_ENVIRONMENT=.venv-ecommerce uv run --locked --package tlcn-ecommerce-api --extra dev -- pytest services/ecommerce-api/tests
UV_PROJECT_ENVIRONMENT=.venv-generator uv run --locked --package tlcn-data-generator --extra dev -- pytest generator/tests
npm --prefix apps/storefront ci --no-audit --no-fund
npm --prefix apps/storefront run typecheck
npm --prefix apps/storefront run build
```

GitHub Actions chạy cùng các kiểm tra này tại [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml). Không đưa secret production vào workflow; CI hiện chỉ cần quyền đọc repository.
