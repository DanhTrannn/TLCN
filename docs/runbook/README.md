# Operational Runbooks

This directory contains operational runbooks and development workflows for the D&K E-Commerce Data Platform.

## Runbook Guides

- [`SETUP.md`](SETUP.md): Step-by-step Lakehouse deployment, Polaris REST Catalog RBAC bootstrapping, catalog inspection, and troubleshooting for the Iceberg-Spark-Trino stack.
- [`STARTUP_FLOW.md`](STARTUP_FLOW.md): Detailed initialization sequence, Docker Compose profiles, one-shot init containers, database migrations, and health checks.
- [`CI.md`](CI.md): GitHub Actions CI workflow, static code analysis, frontend build, and local development commands.

---

## 1. Quick Start (Base Commands)

Launch the profiles configured in `.env` (the example enables core, batch and streaming):

```bash
# 1. Prepare environment configuration
cp .env.example .env

# 2. Start the platform and wait for readiness
./scripts/start_all.sh --build

# 3. Inspect service state
make ps
```

---

## 2. Web Application and Endpoints

After starting the `core` profile, access the applications at:

- **Storefront:** `http://localhost:3000`
- **Admin Console:** `http://localhost:3000/admin` (Default: `admin@web.local` / `Admin@12345`)
- **API Documentation:** `http://localhost:8000/docs` (Interactive Swagger UI)
- **API Readiness Check:** `http://localhost:8000/health/ready`

### Data Platform & Analytics Endpoints

- **LibreDB Studio (SQL IDE):** `http://localhost:3001`
- **Apache Airflow (Orchestration):** `http://localhost:8080` (Default: `airflow` / `password`; configurable in `.env`)
- **Apache Polaris Web Console:** `http://localhost:8183` (`root` / value of `POLARIS_ROOT_CLIENT_SECRET` in `.env`, Realm: `POLARIS`)
- **MinIO Object Storage Console:** `http://localhost:9001` (`minio-root` / value of `MINIO_ROOT_PASSWORD` in `.env`)
- **Spark Master UI:** `http://localhost:8082`
- **Trino Admin Engine (optional, profile `trino-admin`):** `http://localhost:8087` — not part of the default startup

### Service Identities

Every storage consumer runs with its own least-privilege identity; no workload uses the MinIO root account or a shared credential file. MinIO bootstraps seven service users (`lakehouse-polaris`, `lakehouse-spark`, `lakehouse-flink`, `lakehouse-airflow`, `lakehouse-trino`, `lakehouse-trino-admin`, `lakehouse-uploader`), and Polaris provisions four principals (`spark_writer`, `flink_writer`, `trino_reader`, `trino_admin`), each writing credentials to its own private `clients.env` volume — see [`SETUP.md`](SETUP.md) for the full identity matrix.

*Note: Database migrations and default admin seeding occur automatically during backend startup.*

---

## 3. Data Generation and Backfill

### Automated Backfill (Zero-Footprint on Host)

To backfill data using temporary directories with automatic cleanup:

```bash
# Load the OLTP dataset and upload raw historical logs to MinIO
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

Uploaded JSONL files remain raw Landing assets. The current Flink job reads Kafka; these files are not automatically transformed into Gold. Use live API traffic to feed the streaming pipeline.

### Live Access Logging

To stream live HTTP access logs into Iceberg in real-time:

```bash
docker compose --profile core --profile streaming up -d
docker compose --profile streaming logs -f flink-jobmanager
```

### MySQL Change Data Capture

The `streaming` profile enables MySQL row binlog, provisions a dedicated
replication account, registers Debezium, and submits the Flink CDC sink:

```bash
docker compose --profile core --profile batch --profile streaming up -d --build
curl -fsS http://127.0.0.1:8086/connectors/mysql-ecommerce-cdc/status
```

See [`../architecture/CDC_DASHBOARD_DATA_SPEC.md`](../architecture/CDC_DASHBOARD_DATA_SPEC.md)
for event semantics and recovery rules.

---

## 4. Local Development Commands

```bash
# Dependency lockfile, Compose configuration and Python syntax
uv lock --check
docker compose --env-file .env.example --profile core --profile batch --profile streaming --profile lakehouse-tools config --quiet
python3 -m compileall -q airflow/dags/
uvx ruff check .

# Frontend static checks and production build
npm --prefix apps/storefront run lint
make typecheck
npm --prefix apps/storefront run build
```
