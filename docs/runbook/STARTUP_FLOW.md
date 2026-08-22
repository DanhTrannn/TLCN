# Service Startup Sequence & Profile Layout

This document describes the initialization sequence and behavior of each service defined in `docker-compose.yml`. All temporary initialization containers are one-shot, idempotent, and safe to execute repeatedly.

---

## 1. Default Services (`docker compose up -d`)

Running `docker compose up -d` without flags brings up the core **Storage, Metadata, Catalog, and Query Foundation**:

### 1.1. Databases & Object Storage

| Service | Startup Behavior |
|---|---|
| `mysql` | Boots MySQL 8.4.5 LTS (`utf8mb4_0900_ai_ci`, UTC). Creates the `ecommerce` database and `ecommerce_app` user. |
| `postgres` | Boots PostgreSQL 16.8 → Runs `01-create-multiple-databases.sh` to initialize isolated metadata databases for `polaris`, `airflow`, and `superset`. |
| `minio` | Starts MinIO S3 server (`:9000`) and web console (`:9001`). |
| `minio-init` | One-shot: Configures `mc` alias → Idempotently creates `lakehouse` bucket → Disables anonymous public access. |

### 1.2. Apache Polaris REST Catalog

| Service | Startup Behavior |
|---|---|
| `polaris-bootstrap` | One-shot: Executes `polaris-admin-tool bootstrap` to create the default realm (`POLARIS`) and root client credentials in PostgreSQL. |
| `polaris` | Waits for `postgres`, `polaris-bootstrap`, and `minio-init` → Starts Polaris REST catalog (`:8181`) and management server (`:8182`). |
| `polaris-init` | One-shot: Configures S3 warehouse storage → Creates `spark_writer` and `trino_reader` principals → Exports OAuth credentials to shared volume (`/run/polaris/clients.env`) → Creates namespaces (`bronze`, `silver`, `gold`, `quarantine`, `system`). |
| `polaris-console` | Waits for `polaris-init` → Launches the catalog management web UI on port 8183. |

### 1.3. Query Engine & SQL Editor

| Service | Startup Behavior |
|---|---|
| `trino` | Waits for `polaris-init` credentials → Starts Trino (port 8084) configured with the `lakehouse` Iceberg REST catalog. |
| `hue` | Waits for `trino` health check → Launches Apache Hue SQL Query Editor & Data Browser on port 8888. |

---

## 2. Profile: `batch` (`docker compose --profile batch up -d`)

Brings up log collection, Spark cluster, and Airflow orchestration:

### 2.1. Log Collector & Streaming Buffer
| Service | Startup Behavior |
|---|---|
| `fluent-bit` | Waits for `minio-init` → Tails container stdout logs, buffers to persistent storage, compresses to gzip, and flushes 15-minute micro-batches to `s3://lakehouse/landing/logs/`. |

### 2.2. Apache Spark Compute Cluster
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

## 3. Profile: `bi` (`docker compose --profile bi up -d`)

Brings up Apache Superset visualization dashboards:

| Service | Startup Behavior |
|---|---|
| `superset-init` | Waits for `postgres` and `trino` → Runs `superset db upgrade` → Provisions Superset admin account → Executes `superset init` → Imports Trino datasource configuration (`datasources.yml`). |
| `superset` | Starts Gunicorn web server serving Superset dashboards on port 8088. |

---

## 4. Profile: `core` (`docker compose --profile core up -d`)

Brings up the transactional e-commerce application:

| Service | Startup Behavior |
|---|---|
| `ecommerce-api` | Waits for `mysql` health check → Runs Alembic migrations (`alembic upgrade head`) → Seeds initial product catalog if empty → Bootstraps default admin user (`admin@web.local`) → Starts FastAPI server on port 8000. |
| `storefront` | Waits for `ecommerce-api` readiness (`/health/ready`) → Starts Next.js standalone web server on port 3000. |

---

## 5. Startup Dependency Graph

```text
minio ──▶ minio-init ──▶ polaris
postgres ──▶ polaris-bootstrap ──▶ polaris ──▶ polaris-init ──▶ (polaris-console, trino)
trino ──▶ hue
mysql (independent)

[When --profile batch is enabled]
minio-init ──▶ fluent-bit
spark-master ──▶ spark-worker
postgres ──▶ airflow-init ──▶ (airflow-webserver, airflow-scheduler)

[When --profile bi is enabled]
(postgres, trino) ──▶ superset-init ──▶ superset

[When --profile core is enabled]
mysql ──▶ ecommerce-api ──▶ storefront
```