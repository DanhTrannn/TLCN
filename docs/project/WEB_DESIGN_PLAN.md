# D — Source Web Application Design

The Next.js/FastAPI application is the transactional source and dashboard interface for the D&K Data Engineering project. This document describes the current code; deferred capabilities are listed separately.

## 1. Application boundaries

| Component | Responsibility | Source |
|---|---|---|
| Next.js App Router | Storefront, admin/store operations, POS, BI Hub | [pages](../../apps/storefront/src/app) |
| React / Tailwind / ECharts | UI, role dashboards, charts and table interaction | [components](../../apps/storefront/src/components) |
| FastAPI routers / schemas | HTTP contract, validation, authentication dependencies | [modules](../../services/ecommerce-api/app/modules) |
| Domain services / Unit of Work | Business rules, transactions and retry | [uow.py](../../services/ecommerce-api/app/db/uow.py) |
| MySQL / SQLAlchemy | OLTP persistence, 28 tables | [DDL](../../database/schema.sql), [models](../../services/ecommerce-api/app/models) |
| Trino analytics client | Read historical Gold and expose source/degraded status | [analytics](../../services/ecommerce-api/app/modules/analytics) |
| Access middleware / Kafka producer | Structured request events for the log stream | [core](../../services/ecommerce-api/app/core) |

Browsers call FastAPI over HTTP/JSON. The UI does not connect directly to MySQL, Trino, Spark or Polaris. FastAPI uses MySQL for operational transactions and Trino for selected analytical views; batch pipelines do not run inside API requests. Compose currently uses the application MySQL user for batch reads, rather than a separate SELECT-only account.

## 2. Functional modules

| Area | Implemented behavior |
|---|---|
| Auth | Registration, login/logout, current user; JWT cookies and Argon2 password hashes |
| Catalog / location | Product search/filter/detail, categories/facets, city/store availability |
| Wishlist / cart | Authenticated item presence and quantities; no stock reservation on add |
| Checkout | Quote, idempotent order creation, coupon validation, central stock decrement and cost snapshots |
| Orders | Owned history/detail, early paid-order cancellation, receipt confirmation; admin fulfillment |
| POS | Product lookup and completed counter sales using store inventory |
| Admin / inbound | Product/variant management, customer roles/status, branch stock, inbound receipts and weighted costs |
| Coupons / reviews | Promotion management and post-publication moderation |
| Logistics / returns | Delivery staff, shipments/attempts, COD risk, refund-only return workflow |
| Analytics | Seven role views, sales trend, store scope, Gold/MySQL source and fallback status |

Category data is readable and seedable; category CRUD/archive endpoints are not implemented. Registration/current-user endpoints do not provide customer self-service profile editing. Payment success is simulated in code; no external bank callback is integrated.

## 3. Roles and access

Seven staff roles are defined alongside `customer`: `admin`, `store_manager`, `sales_manager`, `marketing_manager`, `inventory_manager`, `operations_manager`, `system_admin`.

- Analytics: admin can select all views; other staff roles can request their own view. Store managers are scoped to their assigned store by FastAPI.
- Products/inbound: inventory manager or admin for writes; product listing is available to staff.
- Coupons/reviews: marketing manager or admin.
- Order administration, logistics and return administration: admin at the API layer.
- Store endpoints: store manager assigned to a store, or admin selecting/defaulting a store.
- POS API: staff assigned to the requested store; admin/system admin bypass this assignment check. UI route permissions are narrower.
- Branch stock writes: PATCH permits admin/assigned store manager; refill POST requires admin. Both routes currently flush without commit, so persistence is incomplete; see the admin router and database dependency.

The UI currently permits operations managers to open order/logistics/returns routes, while those APIs require admin. This mismatch is a current limitation, not evidence of authorized write access. Delivery staff are records, not separately authenticated website users. Source: [API dependencies](../../services/ecommerce-api/app/db/deps.py), [UI permissions](../../apps/storefront/src/lib/role-routes.ts).

## 4. Transaction design

Online checkout requires authentication, CSRF and a client `Idempotency-Key`. The service checks the customer before looking up an existing order. New orders validate catalog, pricing, coupon and inventory inside the Unit of Work. Order/items/payment/history/redemption, central inventory and ledger changes commit together; failures roll back. Retry handling applies to configured lock/deadlock errors, not every possible failure.

VietQR creates a paid order and succeeded payment locally; COD creates confirmed/pending. Dispatch accepts paid or confirmed; delivery precedes customer completion. Cancellation is limited to paid orders and restores stock/releases coupons/records a refund. See [business requirements](BUSINESS_REQUIREMENTS.md) for the return window, third delivery failure and partial-refund behavior.

POS deducts store inventory and creates completed/succeeded records in one transaction. Its generated internal idempotency key does not provide client-retry deduplication equivalent to online checkout. Inbound receipts update central balances and moving weighted costs; historical order items retain their captured cost.

Money is stored as integer VND. MySQL runs with READ COMMITTED in the configured API engine. Row locks and database constraints support consistency; no load-test result or absolute concurrency guarantee is asserted here.

## 5. Access logging and analytical serving

The API emits selected completed-request events to JSON stdout and asynchronously enqueues them to Kafka. GET liveness/readiness probes are excluded. Log fields include `request.id`, timestamp/service/event metadata, canonical route/status, actor and allowlisted commerce context. Raw request/response bodies, credentials and IP addresses are not included; search/user-agent handling uses bounded sanitization, not a blanket guarantee that arbitrary text cannot contain PII.

The producer has a local DLQ path when unavailable/enqueue fails; there is no automated replay job or end-to-end exactly-once guarantee from HTTP completion. Flink writes four log tables through one StatementSet; Spark rolls up three marts. Uploaded historical JSONL is a separate raw source and is not automatically consumed by the Kafka job. See [access-log design](../architecture/ACCESS_LOG_DESIGN.md).

Executive/sales use Gold; marketing combines Gold events and MySQL signals; store/inventory/operations use MySQL; system compares MySQL with Gold. Responses declare `data_source`, `is_degraded`, `degraded_reason`. Dashboard refresh reloads the API without triggering batch processing. Reconciliation charts use one axis per metric, separating order counts from VND.

## 6. Deployment and configuration

Docker builds Next.js standalone output and the FastAPI service. A fresh MySQL volume imports `database/schema.sql`; API startup then runs the catalog/admin seed. Existing volumes are not automatically altered. There is no application schema migration runner.

Frontend public variables are build-time settings: `NEXT_PUBLIC_API_BASE_URL` and `NEXT_PUBLIC_CSRF_COOKIE_NAME`. Backend settings use `API_*`; Kafka producer settings use `KAFKA_*`. Browser requests use cookies and `X-CSRF-Token` where the route enables verification. The store confirm/cancel routes currently omit that CSRF dependency.

Compose is a local HTTP deployment. API defaults and several Compose values still include development credentials; production secret-manager injection, TLS termination, enforced Secure cookies, rate limiting and network isolation are not a completed deployment package. Dedicated MinIO/Polaris workload identities do not remove those limitations.

## 7. Data generation and deferred work

The generator creates configured synthetic SQL history and access logs; the traffic script exercises actual APIs to feed Kafka. Deterministic generation depends on matching configuration/version, not a guarantee for all interactive runtime requests. Scale settings are inputs, not measured row counts or throughput.

ML training/scoring, recommendations, forecasts, exchange-size/color processing, external payment verification and complete supplier/production management are outside current implementation. Documentation must not describe these as working features.

## References

[API usage](../../services/ecommerce-api/README.md) · [Storefront routes](../../apps/storefront/README.md) · [OLTP schema](../architecture/OLTP_SCHEMA.md) · [architecture](../architecture/SYSTEM_ARCHITECTURE_VISUAL.md) · [setup](../runbook/SETUP.md)
