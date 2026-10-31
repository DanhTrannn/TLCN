# Ecommerce API Service

FastAPI service for D&K source transactions, structured access logs and analytical serving. [app/models](app/models) maps 28 OLTP tables; [database/schema.sql](../../database/schema.sql) defines the physical schema. Router registration: [app/api/router.py](app/api/router.py).

## Structure

| Directory | Responsibility |
|---|---|
| `app/core/` | Settings, JWT/Argon2, errors, middleware and Kafka producer |
| `app/db/` | SQLAlchemy sessions, role/CSRF dependencies and Unit of Work |
| `app/models/` | Transactional model mappings |
| `app/modules/` | Domain routers, request/response schemas and services |
| `app/common/` | Money and pagination helpers |

## Run with Docker

From the repository root, copy `.env.example` to `.env` if it does not exist, configure the values, then run:

```bash
docker compose --profile core up -d --build ecommerce-api
curl -fsS http://localhost:8000/health/ready
```

Profiles are additive with COMPOSE_PROFILES. On a fresh volume MySQL imports the SQL schema; API startup seeds catalog/admin and runs Uvicorn. Existing schemas are not upgraded. API readiness checks MySQL connectivity, not Kafka, Trino or completion of Gold processing. See [SETUP](../../docs/runbook/SETUP.md).

## Run on the host

Start MySQL first. Set `API_DATABASE_URL` to the host-reachable MySQL URL using your configured credentials/database; replace the placeholders below. URL-encode credential characters when necessary. Select a local API secret of at least 32 characters.

```bash
docker compose --profile core up -d --wait mysql
export API_DATABASE_URL='mysql+pymysql://<MYSQL_USER>:<MYSQL_PASSWORD>@127.0.0.1:3306/<MYSQL_DATABASE>'
export API_SECRET_KEY='local-development-secret-key-at-least-32-characters'
export KAFKA_ENABLED=false
uv run --locked --package ecommerce-api -- python -m database.seeds.seed_catalog
uv run --locked --package ecommerce-api -- uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

With Kafka disabled, the current producer path routes access events to the local DLQ. For streaming from a host API, enable Kafka and use its externally advertised listener (default `localhost:9094`), rather than Docker DNS `kafka:9092`. Set the CORS origin for the frontend. A host analytics process also needs a host-reachable Trino URL; see the analytics client configuration below.

For host analytics set `API_TRINO_URL=http://localhost:8084` (or your Trino host port). Docker defaults to `http://trino:8080`; the client also attempts the default host URL when no explicit URL was supplied.

## Settings and request conventions

Backend settings are defined in [config.py](app/core/config.py) and use `API_*`; [Kafka settings](app/core/kafka_producer.py) use `KAFKA_*`. [Trino settings](app/modules/analytics/trino_client.py) use their own environment names. Compose only forwards the variables explicitly listed under its API service; adding a new API_* line to the project `.env` does not automatically inject it into that container.

JWT is stored in the HttpOnly `web_access` cookie by default. The readable `web_csrf` cookie is copied into `X-CSRF-Token` for routes that enable double-submit verification. The endpoint table marks those routes. Local cookies are not Secure by default. Internal order confirmation uses `X-Internal-Secret`.

Checkout `Idempotency-Key` must contain 1–59 characters. Other workflows validate their own key requirements; POS generates an internal key and does not deduplicate client retries in the same way. VietQR and refund success are recorded locally, without an external payment provider callback.

## Endpoint reference

Paths and methods below are registered in source. Authentication columns describe router dependencies plus documented store scope; ownership, state and fine-grained analytics checks still apply in services. `CSRF` identifies an explicit verify_csrf dependency. Swagger UI is `/docs` when API_ENABLE_DOCS is enabled; the OpenAPI document is `/openapi.json`.

| Method | Path | Authentication | CSRF |
|---|---|---|---|
| GET | `/api/v1/admin/overview` | Admin | — |
| GET | `/api/v1/admin/products` | Staff | — |
| POST | `/api/v1/admin/products` | Inventory / admin | Yes |
| PATCH | `/api/v1/admin/products/{public_id}` | Inventory / admin | Yes |
| DELETE | `/api/v1/admin/products/{public_id}` | Inventory / admin | Yes |
| PATCH | `/api/v1/admin/variants/{public_id}` | Inventory / admin | Yes |
| GET | `/api/v1/admin/orders` | Admin | — |
| GET | `/api/v1/admin/orders/{order_number}` | Admin | — |
| POST | `/api/v1/admin/orders/{order_number}/confirm` | Admin | Yes |
| POST | `/api/v1/admin/orders/{order_number}/cancel` | Admin | Yes |
| POST | `/api/v1/admin/orders/{order_number}/dispatch` | Admin | Yes |
| POST | `/api/v1/admin/orders/{order_number}/deliver` | Admin | Yes |
| POST | `/api/v1/admin/orders/{order_number}/failed-delivery` | Admin | Yes |
| GET | `/api/v1/admin/customers` | Admin | — |
| PATCH | `/api/v1/admin/customers/{public_id}` | Admin | Yes |
| POST | `/api/v1/admin/customers/{customer_id}/reinstate-cod` | Admin | Yes |
| GET | `/api/v1/admin/branch-inventory` | Staff | — |
| PATCH | `/api/v1/admin/branch-inventory` | Admin / assigned store manager | Yes |
| POST | `/api/v1/admin/inventory/refill` | Admin | Yes |
| GET | `/api/v1/admin/analytics/stores` | Staff, analytics role/store checks | — |
| GET | `/api/v1/admin/analytics/overview` | Admin | — |
| GET | `/api/v1/admin/analytics/role-metrics` | Staff, analytics role/store checks | — |
| GET | `/api/v1/admin/analytics/sales-trend` | Sales manager / admin | — |
| POST | `/api/v1/auth/register` | Public | — |
| POST | `/api/v1/auth/login` | Public | — |
| POST | `/api/v1/auth/logout` | Public | Yes |
| GET | `/api/v1/auth/me` | Authenticated user | — |
| GET | `/api/v1/cart` | Authenticated user | — |
| PUT | `/api/v1/cart/items/{variant_public_id}` | Authenticated user | Yes |
| DELETE | `/api/v1/cart/items/{variant_public_id}` | Authenticated user | Yes |
| GET | `/api/v1/categories` | Public | — |
| GET | `/api/v1/catalog/facets` | Public | — |
| GET | `/api/v1/products` | Public | — |
| GET | `/api/v1/products/{slug}` | Public | — |
| POST | `/api/v1/checkout/quote` | Authenticated user | — |
| POST | `/api/v1/checkout` | Authenticated user | Yes |
| GET | `/api/v1/coupons/available` | Authenticated user | — |
| GET | `/api/v1/admin/coupons` | Marketing / admin | — |
| POST | `/api/v1/admin/coupons` | Marketing / admin | Yes |
| PATCH | `/api/v1/admin/coupons/{public_id}` | Marketing / admin | Yes |
| DELETE | `/api/v1/admin/coupons/{public_id}` | Marketing / admin | Yes |
| POST | `/api/v1/admin/inbound/receipts` | Inventory / admin | Yes |
| GET | `/api/v1/admin/inbound/receipts` | Inventory / admin | — |
| GET | `/api/v1/admin/inbound/receipts/{receipt_code}` | Inventory / admin | — |
| GET | `/api/v1/locations/cities` | Public | — |
| GET | `/api/v1/locations/cities/{city_code}/stores` | Public | — |
| GET | `/api/v1/catalog/products/{slug}/availability` | Public | — |
| GET | `/api/v1/admin/delivery-staff` | Admin | — |
| POST | `/api/v1/admin/delivery-staff` | Admin | Yes |
| PATCH | `/api/v1/admin/delivery-staff/{staff_id}` | Admin | Yes |
| GET | `/api/v1/admin/shipments` | Admin | — |
| GET | `/api/v1/admin/shipments/{order_number}` | Admin | — |
| GET | `/api/v1/orders` | Authenticated user | — |
| GET | `/api/v1/orders/{order_number}` | Authenticated user | — |
| POST | `/api/v1/orders/{order_number}/cancel` | Authenticated user | Yes |
| POST | `/api/v1/orders/{order_number}/complete` | Authenticated user | Yes |
| POST | `/internal/v1/orders/{order_number}/confirm` | Internal secret | — |
| GET | `/api/v1/pos/products` | Staff, POS store scope | — |
| POST | `/api/v1/pos/transactions` | Staff, POS store scope | Yes |
| POST | `/api/v1/orders/{order_number}/returns` | Authenticated user | Yes |
| GET | `/api/v1/returns` | Authenticated user | — |
| GET | `/api/v1/returns/{return_code}` | Authenticated user | — |
| POST | `/api/v1/returns/{return_code}/cancel` | Authenticated user | Yes |
| GET | `/api/v1/admin/returns` | Admin | — |
| GET | `/api/v1/admin/returns/{return_code}` | Admin | — |
| POST | `/api/v1/admin/returns/{return_code}/review` | Admin | Yes |
| POST | `/api/v1/admin/returns/{return_code}/receive` | Admin | Yes |
| POST | `/api/v1/admin/returns/{return_code}/inspect-and-resolve` | Admin | Yes |
| GET | `/api/v1/products/{slug}/reviews` | Public (optional login) | — |
| POST | `/api/v1/orders/{order_number}/items/{order_item_public_id}/review` | Authenticated user | Yes |
| GET | `/api/v1/admin/reviews` | Marketing / admin | — |
| PATCH | `/api/v1/admin/reviews/{public_id}` | Marketing / admin | Yes |
| GET | `/api/v1/admin/store/dashboard` | Store manager / admin, store scope | — |
| GET | `/api/v1/admin/store/orders` | Store manager / admin, store scope | — |
| GET | `/api/v1/admin/store/orders/{order_number}` | Store manager / admin, store scope | — |
| POST | `/api/v1/admin/store/orders/{order_number}/confirm` | Store manager / admin, store scope | — |
| POST | `/api/v1/admin/store/orders/{order_number}/cancel` | Store manager / admin, store scope | — |
| GET | `/api/v1/admin/store/inventory` | Store manager / admin, store scope | — |
| GET | `/api/v1/admin/store/staff` | Store manager / admin, store scope | — |
| GET | `/api/v1/wishlist` | Authenticated user | — |
| PUT | `/api/v1/wishlist/products/{product_public_id}` | Authenticated user | Yes |
| DELETE | `/api/v1/wishlist/products/{product_public_id}` | Authenticated user | Yes |
| GET | `/health/live` | Public | — |
| GET | `/health/ready` | Public | — |

## Current limits

- Admin order, delivery and return APIs require admin. Operations managers have a dashboard/UI menu but do not currently have these API write permissions.
- Store confirm/cancel routes enforce store scope/idempotency, but omit the CSRF dependency.
- Branch inventory PATCH and inventory/refill POST currently flush without committing in their router or get_db dependency. A 204 response is not proof those writes persisted. See [admin router](app/modules/admin/router.py).
- Category CRUD, customer self-service profile editing, separate shipper login and size/color exchange workflows are not implemented.
- Local HTTP, development defaults and published service ports are not a completed production security setup.

## References

[Business requirements](../../docs/project/BUSINESS_REQUIREMENTS.md) · [OLTP schema](../../docs/architecture/OLTP_SCHEMA.md) · [access logs](../../docs/architecture/ACCESS_LOG_DESIGN.md) · [metric definitions](../../docs/architecture/METRICS_CATALOG.md)
