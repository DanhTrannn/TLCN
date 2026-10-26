# Local Lakehouse Setup

This runbook covers the local deployment, RBAC bootstrapping, catalog inspection, and troubleshooting for the Polaris-Iceberg-Spark-Trino lakehouse stack.

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

---

## 3. Startup Sequence

Launch the services selected by `.env` (the example environment enables core, batch and streaming):

```bash
docker compose up -d --build
```

To run the complete system including batch processing, real-time streaming, and the e-commerce storefront:

```bash
docker compose --profile core --profile batch --profile streaming up -d --build
```

### Automated Bootstrap Workflow

1. `minio-init` creates the private `lakehouse` bucket if not present, then converges MinIO identities: it creates **seven service users** (`lakehouse-polaris`, `lakehouse-spark`, `lakehouse-flink`, `lakehouse-airflow`, `lakehouse-trino`, `lakehouse-trino-admin`, `lakehouse-uploader`), each attached to **exactly one of the seven matching policies**. All `lakehouse-*` users and policies are recreated on every run, so stale `lakehouse-*` entries that are no longer managed disappear, while anything outside that prefix (including `root`) is never touched. Access keys come from the `MINIO_*_ACCESS_KEY` / `MINIO_*_SECRET_KEY` variables in `.env`.
2. `postgres` provisions isolated databases for `polaris` and `airflow`.
3. `polaris-bootstrap` initializes the JDBC metadata store and default `POLARIS` realm.
4. `polaris-init` creates the `lakehouse` catalog mapped to `s3://lakehouse/warehouse` and registers the namespaces (`landing`, `bronze`, `silver`, `gold`, `quarantine`, `system`).
5. `polaris-init` provisions **four dedicated service principals** (`spark_writer`, `flink_writer`, `trino_reader`, `trino_admin`) from `infrastructure/polaris/rbac.yml`. Each consumer receives its **own private `clients.env`** written to `polaris-spark-client-credentials`, `polaris-spark-airflow-credentials`, `polaris-flink-credentials`, `polaris-trino-reader-credentials`, or `polaris-trino-admin-credentials` (per-consumer Docker volumes, `0600` files). Principal credentials are also cached in a **root-only state file** under `polaris-credential-state` (`/run/polaris-state/`) so restarts reuse existing credentials without rotating them. There is no shared credential volume anymore.
6. `mysql-cdc-init` provisions the dedicated replication account; `debezium-init` idempotently registers the MySQL connector.
7. `flink-cdc-submit` starts the continuous Kafka-to-Iceberg Bronze CDC job alongside access-log streaming.

---

## 4. Local Service Endpoints

| Service | Local URL | Port | Description |
|---|---|---|---|
| **Storefront** | `http://localhost:3000` | 3000 | Consumer shopping UI |
| **Admin Console** | `http://localhost:3000/admin` | 3000 | Store operations (`admin@web.local` / `Admin@12345`) |
| **Ecommerce API** | `http://localhost:8000/docs` | 8000 | Backend Swagger UI |
| **LibreDB Studio (SQL IDE)** | `http://localhost:3001` | 3001 | Web-based SQL editor for MySQL, PostgreSQL, and Trino |
| **Airflow UI** | `http://localhost:8080` | 8080 | DAG orchestration UI (`airflow` / `password`) |
| **Spark Master UI** | `http://localhost:8082` | 8082 | Compute cluster status |
| **Trino Web UI** | `http://localhost:8084` | 8084 | Query execution status |
| **Polaris Console** | `http://localhost:8183` | 8183 | Catalog & RBAC UI (`root` / value of `POLARIS_ROOT_CLIENT_SECRET` in `.env`; Realm: `POLARIS`) |
| **MinIO Console** | `http://localhost:9001` | 9001 | S3 Object browser (`minio-root` / the value of `MINIO_ROOT_PASSWORD` in `.env`) |
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
