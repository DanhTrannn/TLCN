# Operational Runbooks

This directory contains operational runbooks and development workflows for the D&K E-Commerce Data Platform.

## Runbook Guides

- [`SETUP.md`](SETUP.md): Step-by-step Lakehouse deployment, Polaris REST Catalog RBAC bootstrapping, smoke testing, and troubleshooting for the Iceberg-Spark-Trino stack.
- [`STARTUP_FLOW.md`](STARTUP_FLOW.md): Detailed initialization sequence, Docker Compose profiles, one-shot init containers, database migrations, and health checks.

---

## 1. Quick Start (Base Commands)

Launch services using Docker Compose profiles:

```bash
# 1. Prepare environment configuration
cp .env.example .env

# 2. Start Default Storage, Catalog & Query UI (MySQL, Postgres, MinIO, Polaris, Trino, Hue)
docker compose up -d --build

# 3. Start Batch Processing & Log Collector (Fluent Bit, Spark Cluster, Airflow)
docker compose --profile batch up -d --build

# 4. Start BI Dashboards (Apache Superset)
docker compose --profile bi up -d --build

# 5. Start Storefront & FastAPI Web Application (Optional)
docker compose --profile core up -d --build
```

---

## 2. Web Application and Endpoints

After starting the `core` profile, access the applications at:

- **Storefront:** `http://localhost:3000`
- **Admin Console:** `http://localhost:3000/admin` (Default: `admin@web.local` / `Admin@12345`)
- **API Documentation:** `http://localhost:8000/docs` (Interactive Swagger UI)
- **API Readiness Check:** `http://localhost:8000/health/ready`

### Data Platform & Analytics Endpoints

- **Hue (SQL Query Editor for Trino):** `http://localhost:8888` (Create any username/password on first login)
- **Apache Superset (BI Dashboards):** `http://localhost:8088` (Default: `admin` / `password`)
- **Apache Airflow (Orchestration):** `http://localhost:8080` (Default: `airflow` / `airflow`)
- **Apache Polaris Web Console:** `http://localhost:8183`
- **MinIO Object Storage Console:** `http://localhost:9001` (Default: `minioadmin` / `password`)
- **Spark Master UI:** `http://localhost:8082`

*Note: Database migrations and default admin seeding occur automatically during backend startup.*

---

## 3. Data Generation and Backfill

### Automated Backfill (Zero-Footprint on Host)

To backfill data using temporary directories with automatic cleanup:

```bash
# Backfill both OLTP MySQL dataset and MinIO Access Logs
./scripts/backfill_data.sh

# Or backfill individually
./scripts/backfill_data.sh --mode oltp  # MySQL database only
./scripts/backfill_data.sh --mode logs  # MinIO Landing Zone only
```

### Manual Step-by-Step Backfill

#### Generate Synthetic OLTP Transactions

```bash
uv run --locked --package data-generator -- generator export-sql \
  --config generator/configs/small.yml \
  --output data/generator/small.sql

./scripts/import_generated_sql.sh data/generator/small.sql
```

#### Generate Historical Access Logs

```bash
uv run --locked --package data-generator -- generator export-logs \
  --config generator/configs/small.yml \
  --output-directory data/generator/access-logs \
  --expected-requests 60000

./scripts/upload_generated_logs.sh data/generator/access-logs
```

### Live Access Logging

To stream live HTTP access logs from running API containers into MinIO Landing:

```bash
docker compose --profile core --profile batch up -d
docker compose --profile batch logs -f fluent-bit
```

---

## 4. Local Validation and CI Commands

Run tests and type checks across all components before submitting changes:

```bash
# Check uv lockfile and Docker Compose syntax
uv lock --check
docker compose --profile core --profile batch --profile bi --profile lakehouse-tools config --quiet

# Run Python Test Suite (163 tests total)
uv run --locked --package ecommerce-api --extra dev -- pytest services/ecommerce-api/tests
uv run --locked --package data-generator --extra dev -- pytest generator/tests
PYTHONPATH=pipelines/src uv run --locked --package batch-pipeline --extra dev -- pytest pipelines/tests

# Run all Python tests in single runner
PYTHONPATH=pipelines/src:generator/src:services/ecommerce-api uv run pytest

# Frontend Typecheck and Production Build
npm --prefix apps/storefront run typecheck
npm --prefix apps/storefront run build

# Lakehouse Smoke Test
./scripts/lakehouse_smoke.sh
```
