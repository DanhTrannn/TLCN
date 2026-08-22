# Local Lakehouse Setup

This runbook covers the local deployment, RBAC bootstrapping, smoke testing, and troubleshooting for the Polaris-Iceberg-Spark-Trino lakehouse stack.

## 1. Component Boundaries

The local stack implements the decoupled architecture defined in the lakehouse plan:

- **MinIO S3:** Stores Landing zone files, Iceberg metadata, and Parquet data files under bucket `lakehouse`.
- **Apache Polaris (v1.6.0):** Acts as the Iceberg REST Catalog, backed by PostgreSQL 16.8 for realm and RBAC metadata.
- **Apache Spark (v3.5.9 + Iceberg v1.10.1):** The exclusive writer engine responsible for ETL and table commits.
- **Trino (v483):** The distributed SQL query engine for read-only serving.
- **Polaris Web Console:** Catalog and RBAC management UI (`:8183`).
- **Apache Superset (v4.1.2):** Business intelligence dashboards connected to Trino.

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

Launch the catalog, compute, and BI layers:

```bash
docker compose --profile batch --profile bi up -d --build
```

To run the complete system including the e-commerce web application:

```bash
docker compose --profile core --profile batch --profile bi up -d --build
```

### Automated Bootstrap Workflow

1. `minio-init` creates the private `lakehouse` bucket if not present.
2. `postgres` provisions isolated databases for `polaris`, `airflow`, and `superset`.
3. `polaris-bootstrap` initializes the JDBC metadata store and default `POLARIS` realm.
4. `polaris-init` creates the `lakehouse` catalog mapped to `s3://lakehouse/warehouse` and registers the namespaces (`bronze`, `silver`, `gold`, `quarantine`, `system`).
5. `polaris-init` provisions `spark_writer` (with `CATALOG_MANAGE_CONTENT`) and `trino_reader` principals, persisting credentials to the `polaris-client-credentials` Docker volume.

---

## 4. Local Service Endpoints

| Service | Local URL | Port | Description |
|---|---|---|---|
| **Storefront** | `http://localhost:3000` | 3000 | Consumer shopping UI |
| **Admin Console** | `http://localhost:3000/admin` | 3000 | Store operations (`admin@web.local` / `Admin@12345`) |
| **Ecommerce API** | `http://localhost:8000/docs` | 8000 | Backend Swagger UI |
| **Airflow UI** | `http://localhost:8080` | 8080 | DAG orchestration UI (`airflow` / `password`) |
| **Spark Master UI** | `http://localhost:8082` | 8082 | Compute cluster status |
| **Trino Web UI** | `http://localhost:8084` | 8084 | Query execution status |
| **Apache Superset** | `http://localhost:8088` | 8088 | BI dashboards (`admin` / `password`) |
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
docker compose --profile bi exec trino trino --execute "SHOW SCHEMAS FROM lakehouse;"
docker compose --profile bi exec trino trino --execute "SELECT * FROM lakehouse.system.stack_smoke;"
```

---

## 6. Troubleshooting

### Container Logs

```bash
# Check container status
docker compose --profile core --profile batch --profile bi ps

# Polaris and Database logs
docker compose --profile batch logs --tail=200 postgres polaris-bootstrap polaris polaris-init

# Spark cluster logs
docker compose --profile batch logs --tail=200 spark-master spark-worker

# Trino and Superset logs
docker compose --profile bi logs --tail=200 trino superset-init superset
```

### Common Issues

- **CORS Errors in Polaris Console:** Ensure `POLARIS_CONSOLE_ORIGIN` matches the exact browser URL origin.
- **Authentication Failures in Spark/Trino:** Check that `polaris-init` exited with code 0 and `/run/polaris/clients.env` is mounted from `polaris-client-credentials`.
- **S3 Connectivity Errors:** Ensure container network connectivity to `http://minio:9000`.

---

## 7. Teardown and Environment Reset

To stop services while keeping data intact:

```bash
docker compose --profile core --profile batch --profile bi down
```

To perform a complete factory reset (erasing all MySQL records, MinIO objects, Polaris metadata, and Airflow state):

```bash
docker compose --profile core --profile batch --profile bi --profile lakehouse-tools down -v --remove-orphans
```
