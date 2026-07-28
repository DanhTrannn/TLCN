# Ecommerce API

FastAPI service sở hữu nghiệp vụ và transaction của MySQL ecommerce. Storefront không truy cập database trực tiếp.

## Module

```text
app/common/       Money và pagination primitives
app/core/         Config, security, error và logging
app/db/           Session, dependency và unit of work
app/models/       SQLAlchemy OLTP models
app/modules/      Auth, catalog, wishlist, cart, checkout, order, admin
```

## Chạy bằng Docker

Từ repository root:

```bash
docker compose --profile core up -d --build ecommerce-api
```

Container tự chạy migration, catalog seed và bootstrap admin trước khi khởi động Uvicorn.

- Readiness: `http://localhost:8000/health/ready`
- OpenAPI: `http://localhost:8000/docs`

## Test với uv

```bash
UV_PROJECT_ENVIRONMENT=.venv-ecommerce \
  uv run --locked --package tlcn-ecommerce-api --extra dev -- \
  pytest services/ecommerce-api/tests
```

Không giữ database transaction trong khi gọi external service. Invariant liên bảng phải được bảo vệ trong service transaction và được mô tả tại [`../../docs/architecture/oltp-schema.md`](../../docs/architecture/oltp-schema.md).
