# Local Lakehouse Setup

This runbook covers local startup dependencies, data operations, RBAC bootstrapping, catalog inspection, and troubleshooting. Run commands from the repository root. See the [root README](../../README.md#development-commands) for development commands and CI.

## 1. Component Boundaries

The local stack implements the decoupled architecture defined in the lakehouse plan:

- **MinIO S3:** Stores Landing zone files, Iceberg metadata, and Parquet data files under bucket `lakehouse`.
- **Apache Polaris (v1.6.0):** Acts as the Iceberg REST Catalog, backed by PostgreSQL 16.8 for realm and RBAC metadata.
- **Apache Spark (v3.5.9 + Iceberg v1.10.1):** The batch writer engine responsible for ETL and table commits; Flink independently handles streaming writes.
- **Trino (v483):** The distributed SQL query engine for read-only serving.
- **LibreDB Studio (vlatest):** Web-based SQL IDE for MySQL, PostgreSQL, and Trino (`:3001`).
- **Debezium Connect (v3.0.8):** Captures committed changes from the MySQL row binlog and publishes per-table Kafka topics (`:8086`, localhost only).
- **Polaris Web Console:** Catalog and RBAC management UI (`:8183`).

*Note: Polaris does not store Parquet files or execute queries. PostgreSQL holds only catalog/RBAC metadata, not actual Iceberg data.*

---

## 2. Environment Configuration

Copy the example environment file:

```bash
cp .env.example .env
```

If exposing services beyond `localhost`, update the following variables to avoid CORS issues with the Polaris Console:
- `POLARIS_PUBLIC_API_URL=http://<host>:8181`
- `POLARIS_CONSOLE_ORIGIN=http://<host>:8183`

Review browser-facing NEXT_PUBLIC_API_BASE_URL and API_CORS_ORIGINS together. NEXT_PUBLIC_* values are frontend build arguments; rebuild the image after changing them. Compose forwards only the listed API variables; adding API_COOKIE_SECURE or API_INTERNAL_SECRET to the root .env alone does not inject them into the API container.

The seven MinIO access-key names are validated by minio-init as the managed lakehouse-* identities; secret keys must meet its length checks. Replace development secrets, but do not arbitrarily rename these accounts without updating bootstrap/policies. The actual LibreDB port variable is **LIBREDB_PORT**, default 3001; LIBREDB_STUDIO_PORT in the current example file is unused by Compose.

Validate interpolation without displaying rendered secrets:

```bash
docker compose --env-file .env.example --profile core --profile batch --profile streaming --profile lakehouse-tools config --quiet
```

This validates the example configuration, not running services or production security. Several Compose secrets still have development defaults; secret-manager injection, TLS, enforced Secure cookies and rate limiting are not currently provisioned. Several database/compute/broker ports are host-published without a loopback-only bind; the default network is not fully isolated from the host's public interfaces.

---

## 3. Startup Sequence

The recommended launcher starts `core`, `batch`, and `streaming`, waits for readiness, and initializes missing Gold schemas:

```bash
./scripts/start_all.sh --build
make ps
```

Schema initialization does not populate analytical results. Source history must be loaded and the batch pipeline run separately.

The launcher probes mostly fixed default host ports (8000, 3000, 8084, 9000, 8183, 8080, 8085). With custom ports, start Compose directly and check configured endpoints; the script does not resolve every .env override into its probes. --no-wait skips readiness and Gold initialization; --allow-degraded continues after failed checks and does not prove platform health.

Alternatively, launch Compose services directly using the profiles selected by `.env` (the example environment enables core, batch and streaming):

```bash
docker compose up -d --build
```

To run the complete system including batch processing, real-time streaming, and the e-commerce storefront:

```bash
docker compose --profile core --profile batch --profile streaming up -d --build
```

Explicit `--profile` flags add to `COMPOSE_PROFILES`; they do not restrict the environment selection to a single profile. Direct Compose startup does not perform the launcher's additional Gold-schema check.

### MySQL Initialization

On an empty MySQL volume, the official entrypoint creates the configured database/user and imports [`database/schema.sql`](../../database/schema.sql) from `/docker-entrypoint-initdb.d/10-ecommerce-schema.sql`. The database uses `utf8mb4_0900_ai_ci` and UTC. Existing volumes keep their schema and records; see the [database guide](../../database/README.md).

After MySQL becomes healthy, `ecommerce-api` initializes the catalog/admin if needed and starts FastAPI. The API expects the schema to exist and does not apply schema upgrades. `storefront` waits for API readiness at `/health/ready`.

### Automated Bootstrap Workflow

1. `minio-init` creates the private `lakehouse` bucket if not present, then converges MinIO identities: it creates **seven service users** (`lakehouse-polaris`, `lakehouse-spark`, `lakehouse-flink`, `lakehouse-airflow`, `lakehouse-trino`, `lakehouse-trino-admin`, `lakehouse-uploader`), each attached to **exactly one of the seven matching policies**. All `lakehouse-*` users and policies are recreated on every run, so stale `lakehouse-*` entries that are no longer managed disappear, while anything outside that prefix (including `root`) is never touched. Access keys come from the `MINIO_*_ACCESS_KEY` / `MINIO_*_SECRET_KEY` variables in `.env`.
2. On a fresh volume, `postgres` provisions databases for `polaris` and `airflow`; its initialization script also retains a legacy `hue` database definition. There is no active Hue service in this Compose stack.
3. `polaris-bootstrap` initializes the JDBC metadata store and default `POLARIS` realm.
4. `polaris-init` creates the `lakehouse` catalog mapped to `s3://lakehouse/warehouse` and registers the namespaces (`landing`, `bronze`, `silver`, `gold`, `quarantine`, `system`).
5. `polaris-init` provisions **four dedicated service principals** (`spark_writer`, `flink_writer`, `trino_reader`, `trino_admin`) from `infrastructure/polaris/rbac.yml`. Each consumer receives its **own private `clients.env`** written to `polaris-spark-client-credentials`, `polaris-spark-airflow-credentials`, `polaris-flink-credentials`, `polaris-trino-reader-credentials`, or `polaris-trino-admin-credentials` (per-consumer Docker volumes, `0600` files). Principal credentials are also cached in a **root-only state file** under `polaris-credential-state` (`/run/polaris-state/`) so restarts reuse existing credentials without rotating them. There is no shared credential volume anymore.
6. `mysql-cdc-init` provisions the dedicated replication account; `debezium-init` idempotently registers the MySQL connector.
7. `flink-cdc-submit` starts the continuous Kafka-to-Iceberg Bronze CDC job alongside access-log streaming.

### Service Dependencies and Profiles

Compose waits for health checks or successful completion of initialization jobs where configured. The main dependencies are:

| Group / profile | Startup dependencies |
|---|---|
| Shared storage/catalog (`batch`, `streaming`) | Healthy `postgres` → `polaris-bootstrap`; healthy `minio` → `minio-init`; successful bootstrap/init jobs → `polaris` → `polaris-init` |
| Query tools (`batch`, `streaming`) | Successful `polaris-init` → `trino` and `polaris-console`; healthy MySQL/PostgreSQL/Trino → `libredb-studio` |
| Spark (`batch`, `streaming`) | `spark-master` → `spark-worker`; jobs use dedicated Polaris credentials |
| Airflow (`batch`, `streaming`) | Healthy `postgres` → `airflow-init` (metadata migration, admin user and `spark_default` connection) → webserver/scheduler using `LocalExecutor` |
| Web (`core`) | Healthy `mysql` → `ecommerce-api` → `storefront`; when Kafka is enabled, the API also waits for Kafka health |
| CDC (`streaming`) | Healthy MySQL → `mysql-cdc-init`; healthy Kafka plus successful MySQL CDC init → `debezium-connect` → `debezium-init` |
| Flink (`streaming`) | Healthy Kafka/Polaris plus successful `polaris-init` → JobManager → TaskManager; access-log submission waits for `kafka-init`, CDC submission for `debezium-init`; both wait for JobManager health and TaskManager startup |
| Spark SQL (`lakehouse-tools`) | Successful `polaris-init` → utility `spark-client`, using its own credential volume |
| Administrative SQL (`trino-admin`, optional) | Successful `polaris-init` → `trino-admin` with a separate administrative principal |

`minio` and `mysql` are also available to `core`. Exact profile membership and dependency conditions are defined in [`docker-compose.yml`](../../docker-compose.yml).

---

## 4. Local Service Endpoints

| Service | Local URL | Port | Description |
|---|---|---|---|
| **Storefront** | `http://localhost:3000` | 3000 | Consumer shopping UI |
| **Admin Console** | `http://localhost:3000/admin` | 3000 | Store operations; bootstrap account from `API_BOOTSTRAP_ADMIN_*` |
| **Ecommerce API** | `http://localhost:8000/docs` | 8000 | Backend Swagger UI |
| **LibreDB Studio (SQL IDE)** | `http://localhost:3001` | 3001 | Web-based SQL editor for MySQL, PostgreSQL, and Trino |
| **Airflow UI** | `http://localhost:8080` | 8080 | DAG orchestration UI (`AIRFLOW_ADMIN_USER` / `AIRFLOW_ADMIN_PASSWORD`) |
| **Spark Master UI** | `http://localhost:8082` | 8082 | Compute cluster status |
| **Trino Web UI** | `http://localhost:8084` | 8084 | Query execution status |
| **Flink Dashboard** | `http://localhost:8085` | 8085 | Streaming jobs and task status |
| **Polaris Console** | `http://localhost:8183` | 8183 | Catalog & RBAC UI (`POLARIS_ROOT_CLIENT_ID` / `POLARIS_ROOT_CLIENT_SECRET`; Realm: `POLARIS`) |
| **MinIO Console** | `http://localhost:9001` | 9001 | S3 Object browser (`MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD`) |
| **Trino Admin (optional)** | `http://localhost:8087` | 8087 | Administrative Trino engine (profile `trino-admin`, not started by default) |
| **Debezium Connect** | `http://127.0.0.1:8086` | 8086 | CDC connector lifecycle/status API |

### Starting the Optional Trino Admin Engine

The default startup provisions `trino` with the read-only `trino_reader` principal. An administrative Trino engine using the `trino_admin` principal (full catalog management) can be started on demand — it is **not** part of the default startup:

```bash
docker compose --profile trino-admin up -d trino-admin
```

It serves on host port `8087` (`http://localhost:8087`). The read-only `trino` reader engine remains the default query engine.

---

## 5. Inspect Catalog and Data

Use the Trino CLI to browse the catalog and available Gold tables:

```bash
docker compose exec trino trino --execute "SHOW SCHEMAS FROM lakehouse;"
docker compose exec trino trino --execute "SHOW TABLES FROM lakehouse.gold;"
```

LibreDB Studio at `http://localhost:3001` also provides a SQL interface. Airflow and Flink dashboards show the state of batch and streaming jobs.

### Load Source History and Run Batch

The [root README](../../README.md#historical-data-backfill) contains automated and manual SQL/log backfill commands; the [generator guide](../../generator/README.md) describes dataset configuration and account mapping. Uploaded historical JSONL files remain raw Landing assets because the current Flink job reads Kafka.

After loading source data, unpause and trigger the OLTP DAG (DAGs start paused by default):

```bash
docker compose exec -T airflow-scheduler airflow dags unpause lakehouse_oltp_pipeline
docker compose exec -T airflow-scheduler airflow dags trigger lakehouse_oltp_pipeline
```

Inspect the run in Airflow and query its quality audit before considering Gold ready. Batch commits cursors after Bronze; a later failure does not automatically rewind them or roll back Gold tables together. The source is live during per-table extraction/reconciliation, not frozen in one global MySQL snapshot. See [Lakehouse Design](../project/LAKEHOUSE_DESIGN_PLAN.md).

Maintenance DAGs are also initially paused. Enable them explicitly when required:

```bash
docker compose exec -T airflow-scheduler airflow dags unpause lakehouse_oltp_maintenance
docker compose exec -T airflow-scheduler airflow dags unpause lakehouse_streaming_maintenance
```

OLTP maintenance targets 15 Gold and 8 Silver tables; log maintenance targets four log tables. Bronze CDC and the remaining tables are not automatically covered. The streaming monitor accepts a RUNNING job, so verify both named streams separately rather than treating this task alone as proof of their health.

### Inspect Streaming and CDC

With `core` and `streaming` enabled, live API traffic feeds the access-log pipeline. Check Flink and the CDC connector:

```bash
docker compose --profile streaming logs --tail=200 flink-jobmanager
curl -fsS http://127.0.0.1:8086/connectors/mysql-ecommerce-cdc/status
curl -fsS http://localhost:8085/jobs/overview
```

CDC currently appends events to Bronze; Silver/Gold still use Spark batch. See the [CDC specification](../architecture/CDC_DASHBOARD_DATA_SPEC.md) for event semantics, inspection SQL, and recovery rules, and the [access-log design](../architecture/ACCESS_LOG_DESIGN.md) for log contracts and processing boundaries.

---

## 6. Polaris RBAC as Code (`rbac.yml`)

The platform manages Polaris access control declaratively using `infrastructure/polaris/rbac.yml`. Changes made to this YAML file are automatically reconciled by `infrastructure/polaris/sync_polaris_rbac.py` inside `polaris-init`.

### Configuration Structure (`infrastructure/polaris/rbac.yml`)
- **`catalog`**: Defines catalog settings, S3 endpoints, and default warehouse locations.
- **`namespaces`**: Pre-created Iceberg namespaces (`landing`, `bronze`, `silver`, `gold`, `quarantine`, `system`).
- **`catalog_roles`**: Defines catalog-level roles and their granted privileges (e.g. `CATALOG_MANAGE_CONTENT`, `TABLE_READ_DATA`).
- **`principal_roles`**: Maps principal roles to catalog roles (e.g., binding `spark_writer_role` to `spark_writer_catalog_role`).
- **`principals`**: Defines exactly four principals (`spark_writer`, `flink_writer`, `trino_reader`, `trino_admin`), their role bindings, and target environment variable names in their `clients.env`.
- **`credential_outputs`**: Maps each principal to its private output directory under `/run/polaris-output/` (one per consumer: `spark-client`, `spark-airflow`, `flink`, `trino-reader`, `trino-admin`) with the owning UID/GID. Each consumer mounts **only** its own `clients.env` — never another consumer's credentials.
- **Reader least privilege**: `trino_reader_catalog_role` gets only metadata/listing and data read privileges (`CATALOG_READ_PROPERTIES`, `NAMESPACE_LIST`, `NAMESPACE_READ_PROPERTIES`, `TABLE_LIST`, `TABLE_READ_PROPERTIES`, `TABLE_READ_DATA`, `VIEW_LIST`, `VIEW_READ_PROPERTIES`) — no write, drop, or management privileges.
- **Writer scope**: Spark/Flink writers have CATALOG_MANAGE_CONTENT at catalog level, not per-table write allowlists. The batch reader URL uses application MYSQL_USER; the separate CDC account has replication/SELECT grants on *.*, although the connector captures only 27 tables.
- **`purge_unmanaged_principals: true`**: Automatically removes any unmanaged principals (excluding `root`).
- **`purge_unmanaged_roles: true`**: Automatically removes any unmanaged principal roles and catalog roles.
- **`prune_unmanaged_privileges: true`**: Revokes any privilege granted outside this file.

`rbac.yml` is authoritative: if you manually create a principal or role in Polaris, the next `polaris-init` run removes it.

### Applying RBAC Changes on Demand
Whenever you add, modify, or remove roles, privileges, or principals in `rbac.yml`, apply the changes immediately with:

```bash
docker compose run --rm polaris-init
```

The reconciler:
1. Re-authenticates as Polaris `root`.
2. Verifies and applies changes to catalog, catalog roles, grants, and principal roles.
3. Preserves existing valid credentials in the per-consumer `clients.env` files and the root-only state file without rotating unnecessarily.
4. Generates credentials for new principals, writes each consumer's private `clients.env` (`0600`, owned by the consumer UID from `credential_outputs`), and updates the root-only state file.
5. Purges any unmanaged principals/roles and prunes unmanaged privileges if enabled.

---

## 7. Troubleshooting

### Container Logs

```bash
# Check container status
docker compose --profile core --profile batch --profile streaming ps

# Polaris and Database logs
docker compose --profile batch logs --tail=200 postgres polaris-bootstrap polaris polaris-init

# Spark cluster logs
docker compose --profile batch logs --tail=200 spark-master spark-worker

# Trino query engine logs
docker compose logs --tail=200 trino
```

### Common Issues

- **CORS Errors in Polaris Console:** Ensure `POLARIS_CONSOLE_ORIGIN` matches the exact browser URL origin.
- **Authentication Failures in Spark/Trino:** Check that `polaris-init` exited with code 0 and that your consumer mounts its own private credential volume (`polaris-spark-client-credentials`, `polaris-spark-airflow-credentials`, `polaris-flink-credentials`, `polaris-trino-reader-credentials`, or `polaris-trino-admin-credentials`) — there is no shared credential volume. Each `clients.env` is written `0600` and owned by the consumer UID; a service that cannot read its file **fails startup** rather than falling back, so a startup failure usually means a UID/permission mismatch, not missing data.
- **Upgrading an Existing Deployment (Polaris root secret):** The Polaris `root` client secret is baked into the Polaris metadata database at first bootstrap. On an existing `postgres-data` volume, keep your current `POLARIS_ROOT_CLIENT_SECRET` in `.env` even if `.env.example` now ships a new default — `polaris-init` does not auto-rotate the root secret, and using the new default against an existing realm fails `root` authentication and blocks startup. Only brand-new installs (no `postgres-data` volume) pick up the `.env.example` value.
- **S3 Connectivity Errors:** Ensure container network connectivity to `http://minio:9000`. Each consumer must use its own dedicated MinIO service user (`lakehouse-*`); MinIO root credentials are not mounted into any workload.
- **UI/API role mismatch:** operations_manager can open order/logistics/return UI routes but those APIs require admin. A 403 is not a Trino/Iceberg failure. Store confirm/cancel routes also lack the explicit CSRF dependency.
- **Branch stock changes return 204 but do not persist:** branch-inventory PATCH and inventory/refill POST currently only flush; get_db closes the session without committing. This is an application transaction limitation, not a CDC lag symptom. See [API limits](../../services/ecommerce-api/README.md#current-limits).
- **COD payment changes missing in Silver:** payments uses a created_at cursor even though completion updates status. Old updates outside lookback can be missed; CDC alone does not update Silver/Gold.
- **Flink recovery/replay:** submission does not pass a checkpoint/savepoint restore path. A new access-log submission starts at earliest; CDC uses group offsets with earliest fallback. Inspect restore state and offsets explicitly. The access producer has a local DLQ without automatic replay.
- **Gold freshness warning after successful batch:** system UI uses 15/60-minute thresholds, whereas Gold is scheduled daily. Dashboard refresh reloads API data without running the DAG.

### Rebuild a changed frontend

The production image does not mount local source. Apply UI/source or NEXT_PUBLIC_* changes without rebuilding other services:

```bash
docker compose up -d --no-deps --build storefront
curl -fsS http://localhost:3000/admin/analytics -o /dev/null
```

HTTP success only verifies that the page is served. Sign in with an appropriate role to inspect KPI requests, source/degraded labels and system reconciliation. Order counts and VND use separate metric charts; full monetary values are available in tooltips/table cells.

---

## 8. Teardown and Environment Reset

To stop services while keeping data intact:

```bash
docker compose --profile core --profile batch --profile streaming down
```

To perform a complete factory reset (erasing all MySQL records, MinIO objects, Polaris metadata, and Airflow state):

```bash
docker compose --profile core --profile batch --profile streaming --profile lakehouse-tools down -v --remove-orphans
```
