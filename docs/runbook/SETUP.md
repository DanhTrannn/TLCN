# Local Lakehouse Setup

This runbook covers the local deployment, RBAC bootstrapping, smoke testing, and troubleshooting for the Polaris-Iceberg-Spark-Trino lakehouse stack.

## 1. Component Boundaries

The local stack implements the decoupled architecture defined in the lakehouse plan:

- **MinIO S3:** Stores Landing zone files, Iceberg metadata, and Parquet data files under bucket `lakehouse`.
- **Apache Polaris (v1.6.0):** Acts as the Iceberg REST Catalog, backed by PostgreSQL 16.8 for realm and RBAC metadata.
- **Apache Spark (v3.5.9 + Iceberg v1.10.1):** The exclusive writer engine responsible for ETL and table commits.
- **Trino (v483):** The distributed SQL query engine for read-only serving.
- **LibreDB Studio (vlatest):** Web-based SQL IDE for MySQL, PostgreSQL, and Trino (`:3001`).
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

Launch the default catalog, storage, Trino, and LibreDB Studio:

```bash
docker compose up -d --build
```

To run the complete system including batch processing, BI dashboards, and the e-commerce storefront:

```bash
docker compose --profile core --profile batch --profile bi up -d --build
```

### Automated Bootstrap Workflow

1. `minio-init` creates the private `lakehouse` bucket if not present.
2. `postgres` provisions isolated databases for `polaris` and `airflow`.
3. `polaris-bootstrap` initializes the JDBC metadata store and default `POLARIS` realm.
4. `polaris-init` creates the `lakehouse` catalog mapped to `s3://lakehouse/warehouse` and registers the namespaces (`bronze`, `silver`, `gold`, `quarantine`, `system`).
5. `polaris-init` provisions 3 dedicated service principals (`trino_admin` with full administrative rights, `spark_writer` with read/write `CATALOG_MANAGE_CONTENT`, and `trino_reader` with least-privilege read access), persisting credentials to the `polaris-client-credentials` Docker volume.

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
| **Polaris Console** | `http://localhost:8183` | 8183 | Catalog & RBAC UI (Realm: `POLARIS`) |
| **MinIO Console** | `http://localhost:9001` | 9001 | S3 Object browser (`minioadmin` / `password`) |

---

## 5. End-to-End Smoke Test

Run the automated smoke test script to verify end-to-end integration:

```bash
./scripts/lakehouse_smoke.sh
```

The script performs the following verifications:
1. Verifies that `polaris` and `minio` endpoints are reachable.
2. Uses Spark SQL (`spark-client`) to write an Iceberg table (`lakehouse.system.stack_smoke`) via Polaris REST catalog.
3. Verifies that data files exist in MinIO under `s3://lakehouse/warehouse/system/stack_smoke`.
4. Executes a Trino query reading from `lakehouse.system.stack_smoke` to ensure end-to-end read-write connectivity.

To query manually via Trino CLI inside container:

```bash
docker compose exec trino trino --execute "SHOW SCHEMAS FROM lakehouse;"
docker compose exec trino trino --execute "SELECT * FROM lakehouse.system.stack_smoke;"
```

---

## 6. Polaris RBAC as Code (`rbac.yml`)

The platform manages Polaris access control declaratively using `infrastructure/polaris/rbac.yml`. Changes made to this YAML file are automatically reconciled by `infrastructure/polaris/sync_polaris_rbac.py` inside `polaris-init`.

### Configuration Structure (`infrastructure/polaris/rbac.yml`)
- **`catalog`**: Defines catalog settings, S3 endpoints, and default warehouse locations.
- **`namespaces`**: Pre-created Iceberg namespaces (`bronze`, `silver`, `gold`, `quarantine`, `system`).
- **`catalog_roles`**: Defines catalog-level roles and their granted privileges (e.g. `CATALOG_MANAGE_CONTENT`, `TABLE_READ_DATA`).
- **`principal_roles`**: Maps principal roles to catalog roles (e.g., binding `spark_writer_role` to `spark_writer_catalog_role`).
- **`principals`**: Defines principals (`spark_writer`, `trino_reader`, `trino_admin`), their role bindings, and target environment variables in `/run/polaris/clients.env`.
- **`purge_unmanaged_principals`**: When `true`, automatically removes any unmanaged principals (excluding `root`).

### Applying RBAC Changes on Demand
Whenever you add, modify, or remove roles, privileges, or principals in `rbac.yml`, apply the changes immediately with:

```bash
docker compose run --rm polaris-init
```

The reconciler:
1. Re-authenticates as Polaris `root`.
2. Verifies and applies changes to catalog, catalog roles, grants, and principal roles.
3. Preserves existing valid credentials in `/run/polaris/clients.env` without rotating unnecessarily.
4. Generates credentials for new principals and updates the credentials file.
5. Purges any unmanaged entities if enabled.

---

## 7. Troubleshooting

### Container Logs

```bash
# Check container status
docker compose --profile core --profile batch --profile bi ps

# Polaris and Database logs
docker compose --profile batch logs --tail=200 postgres polaris-bootstrap polaris polaris-init

# Spark cluster logs
docker compose --profile batch logs --tail=200 spark-master spark-worker

# Trino query engine logs
docker compose logs --tail=200 trino
```

### Common Issues

- **CORS Errors in Polaris Console:** Ensure `POLARIS_CONSOLE_ORIGIN` matches the exact browser URL origin.
- **Authentication Failures in Spark/Trino:** Check that `polaris-init` exited with code 0 and `/run/polaris/clients.env` is mounted from `polaris-client-credentials`.
- **S3 Connectivity Errors:** Ensure container network connectivity to `http://minio:9000`.

---

## 8. Teardown and Environment Reset

To stop services while keeping data intact:

```bash
docker compose --profile core --profile batch --profile bi down
```

To perform a complete factory reset (erasing all MySQL records, MinIO objects, Polaris metadata, and Airflow state):

```bash
docker compose --profile core --profile batch --profile bi --profile lakehouse-tools down -v --remove-orphans
```
