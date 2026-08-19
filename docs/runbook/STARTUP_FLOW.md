# Service Startup Sequence

This document describes the initialization sequence and behavior of each service defined in `docker-compose.yml`. All temporary initialization containers are one-shot, idempotent, and safe to execute repeatedly.

## 1. Profile: `core`

| Service | Startup Behavior |
|---|---|
| `mysql` | Boots MySQL 8.4.5 LTS (`utf8mb4_0900_ai_ci`, UTC). Creates the `ecommerce` database and `ecommerce_app` user. |
| `ecommerce-api` | Waits for `mysql` health check → Runs Alembic migrations (`alembic upgrade head`) → Seeds initial product catalog if empty → Bootstraps the default admin user (`admin@web.local`) → Starts Uvicorn ASGI server. |
| `storefront` | Waits for `ecommerce-api` readiness (`/health/ready`) → Starts Next.js standalone web server on port 3000. |

---

## 2. Profile: `batch`

### 2.1. Object Storage, Database & Catalog

| Service | Startup Behavior |
|---|---|
| `minio` | Starts MinIO S3 server (`:9000`) and web console (`:9001`). |
| `minio-init` | One-shot: Configures `mc` alias → Idempotently creates `web-lakehouse` bucket → Disables anonymous public access. |
| `fluent-bit` | Waits for `minio-init` → Tails container stdout logs, buffers to persistent storage, compresses to gzip, and flushes 15-minute micro-batches to `s3://web-lakehouse/landing/logs/`. |
| `postgres` | Boots PostgreSQL 16.8 → Runs `01-create-multiple-databases.sh` to initialize isolated databases for `polaris`, `airflow`, and `superset`. |
| `polaris-bootstrap` | One-shot: Executes `polaris-admin-tool bootstrap` to create the default realm (`POLARIS`) and root client credentials in PostgreSQL. |
| `polaris` | Waits for `postgres`, `polaris-bootstrap`, and `minio-init` → Starts Polaris REST catalog (`:8181`) and management server (`:8182`). |
| `polaris-init` | One-shot: Configures S3 warehouse storage → Creates `spark_writer` and `trino_reader` principals → Exports OAuth credentials to shared volume (`/run/polaris/clients.env`) → Creates namespaces (`bronze`, `silver`, `gold`, `quarantine`, `system`). |
| `polaris-console` | Waits for `polaris-init` → Launches the catalog management web UI on port 8183. |

### 2.2. Apache Spark Compute

| Service | Startup Behavior |
|---|---|
| `spark-master` | Starts Spark standalone cluster master (`:7077`, Web UI: `:8082`). |
| `spark-worker` | Registers worker with `spark-master` (Web UI: `:8083`). |
| `spark-client` | (*Profile `lakehouse-tools`*) One-shot smoke runner injecting Polaris OAuth credentials and executing test table commits. |

### 2.3. Apache Airflow Orchestration

| Service | Startup Behavior |
|---|---|
| `airflow-init` | Waits for `postgres` → Runs `airflow db migrate` → Provisions Airflow admin user → Registers `spark_default` connection. |
| `airflow-webserver` | Starts Airflow web UI on port 8080. |
| `airflow-scheduler` | Starts Airflow scheduler with `LocalExecutor` managing DAG runs. |

---

## 3. Profile: `bi`

| Service | Startup Behavior |
|---|---|
| `trino` | Waits for `polaris-init` credentials → Starts Trino (port 8084) configured with the `lakehouse` Iceberg REST catalog. |
| `superset-init` | Waits for `postgres` and `trino` → Runs `superset db upgrade` → Provisions Superset admin account → Executes `superset init` → Imports Trino datasource configuration (`datasources.yml`). |
| `superset` | Starts Gunicorn web server serving Superset dashboards on port 8088. |

---

## 4. Startup Dependency Graph

```text
mysql ──▶ ecommerce-api ──▶ storefront
minio ──▶ minio-init ──▶ (fluent-bit, polaris)
postgres ──▶ (polaris-bootstrap, airflow-init, superset-init)
polaris-bootstrap ──▶ polaris ──▶ polaris-init ──▶ (polaris-console, trino, spark-client)
spark-master ──▶ spark-worker
airflow-init ──▶ (airflow-webserver, airflow-scheduler)
trino ──▶ superset-init ──▶ superset
```

---

## 5. Persistence and Idempotency Notes

- **Credentials Volume:** Polaris generated client credentials are saved to `polaris-client-credentials` Docker volume and safely reused across container restarts.
- **Idempotent Bootstrapping:** All initialization containers (`minio-init`, `polaris-bootstrap`, `polaris-init`, `airflow-init`, `superset-init`) are designed to be run repeatedly without causing state conflicts or duplicate entities.