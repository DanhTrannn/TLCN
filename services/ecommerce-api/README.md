# Ecommerce API Service

The Ecommerce API is a FastAPI backend service that encapsulates retail business logic, transactional invariants, and structured access logging for the D&K E-Commerce Platform.

## Module Structure

| Directory | Responsibility |
|---|---|
| `app/common/` | Money representation (integer VND) and cursor pagination primitives |
| `app/core/` | Application configuration, security (JWT/Argon2), exception handlers, and structured access logging |
| `app/db/` | Database session management, FastAPI dependencies, and Unit of Work abstractions |
| `app/models/` | SQLAlchemy 2.0 ORM models mapping to all 17 OLTP tables |
| `app/modules/` | Domain endpoints and services (auth, catalog, wishlist, cart, checkout, orders, reviews, admin) |

---

## Running the Service

### Docker Compose (Recommended)

From the repository root:

```bash
docker compose --profile core up -d --build ecommerce-api
```

The container performs the following sequence on startup:
1. Waits for MySQL to pass health checks.
2. Applies pending Alembic database migrations (`alembic upgrade head`).
3. Seeds initial catalog categories and products if empty.
4. Bootstraps the default administrator account (`admin@web.local`).
5. Starts the Uvicorn ASGI server on port 8000.

### Local Development with `uv`

```bash
# Set environment variables
export API_DATABASE_URL="mysql+pymysql://ecommerce_app:password@localhost:3306/ecommerce"
export API_SECRET_KEY="local-development-secret-key-at-least-32-characters"

# Run migrations and start server
uv run --package ecommerce-api alembic -c database/alembic.ini upgrade head
uv run --package ecommerce-api uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Service Endpoints

| Endpoint | Method | Authentication | Description |
|---|---|---|---|
| `/health/live` | GET | None | Liveness probe returning `{"status": "ok"}` |
| `/health/ready` | GET | None | Readiness probe verifying database connectivity |
| `/docs` | GET | None | Interactive Swagger UI API documentation |
| `/api/v1/auth/login` | POST | None | Customer and admin login issuing HttpOnly JWT |
| `/api/v1/auth/register` | POST | None | Customer account registration |
| `/api/v1/auth/me` | GET | Authenticated | Current authenticated profile |
| `/api/v1/products` | GET | None | Catalog listing with category/price/stock/sort filters |
| `/api/v1/products/{slug}` | GET | None | Product detail with variants and stock availability |
| `/api/v1/cart` | GET / POST / DELETE | Optional | Shopping cart management |
| `/api/v1/wishlist` | GET / POST / DELETE | Customer | Saved items management |
| `/api/v1/checkout` | POST | Customer | Atomic checkout with stock deduction and coupon validation |
| `/api/v1/orders` | GET | Customer | Order history and detail tracking |
| `/api/v1/reviews` | GET / POST | Public / Customer | Approved reviews reading and post-purchase review submission |
| `/api/v1/admin/*` | ALL | Admin | Store operations (catalog, archive, orders, coupons, reviews) |

---

## Testing

Run the test suite using `pytest` (63 tests):

```bash
uv run --locked --package ecommerce-api --extra dev -- pytest services/ecommerce-api/tests
```

All transactional rules and schema constraints are documented in [`../../docs/architecture/OLTP_SCHEMA.md`](../../docs/architecture/OLTP_SCHEMA.md).
Structured access log contracts are documented in [`../../docs/architecture/ACCESS_LOG_DESIGN.md`](../../docs/architecture/ACCESS_LOG_DESIGN.md).
