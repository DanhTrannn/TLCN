<!-- prettier-ignore -->
<div align="center">

# D&K E-Commerce Data Platform

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Node.js](https://img.shields.io/badge/Node.js-22-339933?style=flat-square&logo=node.js&logoColor=white)](https://nodejs.org)
[![MySQL](https://img.shields.io/badge/MySQL-8.4-4479A1?style=flat-square&logo=mysql&logoColor=white)](https://mysql.com)
[![Apache Kafka](https://img.shields.io/badge/Apache_Kafka-3.8-231F20?style=flat-square&logo=apachekafka&logoColor=white)](https://kafka.apache.org)
[![Apache Flink](https://img.shields.io/badge/Apache_Flink-1.19-E6526F?style=flat-square&logo=apacheflink&logoColor=white)](https://flink.apache.org)
[![Apache Spark](https://img.shields.io/badge/Apache_Spark-3.5.9-E25A1C?style=flat-square&logo=apachespark&logoColor=white)](https://spark.apache.org)
[![Apache Iceberg](https://img.shields.io/badge/Apache_Iceberg-1.10.1-blue?style=flat-square&logo=apache&logoColor=white)](https://iceberg.apache.org)
[![Apache Polaris](https://img.shields.io/badge/Apache_Polaris-1.6.0-teal?style=flat-square&logo=apache&logoColor=white)](https://polaris.apache.org)
[![Trino](https://img.shields.io/badge/Trino-483-DD00A1?style=flat-square&logo=trino&logoColor=white)](https://trino.io)
[![Apache ECharts](https://img.shields.io/badge/Apache_ECharts-6.1-AA344D?style=flat-square&logo=apacheecharts&logoColor=white)](https://echarts.apache.org)
[![CI](https://img.shields.io/badge/CI-GitHub_Actions-2088FF?style=flat-square&logo=githubactions&logoColor=white)](.github/workflows/ci.yml)

:star: If you find this project useful, consider giving it a star!

[Overview](#overview) • [Features](#features) • [Quick Start](#quick-start) • [Architecture](#architecture) • [Development](#development-commands) • [Documentation](#documentation-index)

</div>

The **D&K E-Commerce Data Platform** is a local Data Engineering project combining an e-commerce source application, batch data processing, MySQL change capture, and access-log streaming. MySQL contains 28 OLTP tables; 27 are configured for analytical ingestion. Data is stored in Apache Iceberg on MinIO, cataloged by Polaris, and queried through Trino. A Next.js/FastAPI application provides Storefront, POS, administration, and ECharts dashboards.

> [!NOTE]
> The platform has three data paths: **OLTP batch**, **MySQL binlog CDC**, and **access-log streaming**. CDC currently writes an append-only Bronze event log; OLTP Silver/Gold tables are built by Spark batch jobs.

## Overview

The project covers data collection, incremental extraction, Medallion transformations, data quality, reconciliation, and SQL analytics. The website and POS provide transactional source data; the generator supplies configurable synthetic datasets and simulated API traffic.

Historical analytics use Trino over Iceberg. Current store, inventory, and logistics indicators use MySQL through FastAPI. Responses identify their data source and any fallback. Machine learning training and scoring remain outside the implemented scope.

## Features

- **Hybrid Ingestion:** Spark batch extraction, Debezium MySQL CDC, and Kafka/Flink access-log processing.
- **Incremental Batch:** Composite cursors `(cursor_field, pk)`, lookback windows, high watermarks, Parquet files, and manifests.
- **Medallion Processing:** Bronze source history, Silver typing/deduplication/MERGE and PII pseudonymization, and Gold dimensions/facts/marts.
- **Data Quality and Reconciliation:** Source-to-Silver reconciliation and post-Gold checks, with audit results in `lakehouse.system.data_quality_results`.
- **Open Lakehouse Storage:** MinIO object storage, Iceberg tables/snapshots, Polaris catalog, and scheduled maintenance.
- **Role-Based Analytics:** Seven dashboard views with API-level role and store filtering, Trino historical queries, and explicitly marked OLTP fallback.
- **Access-Log Analytics:** Request volume, duration percentiles, error rates, product interactions, and event-based marketing funnels.
- **Synthetic Data Generation:** Version 0.7 generates deterministic SQL history and historical access logs from YAML configurations; live API traffic can feed the Kafka stream.
- **Operational Source Application:** Storefront, cart/checkout, POS, store inventory, in-house delivery, COD failure tracking, returns/refunds, and product reviews.
- **Inventory Costing:** Inbound receipts, Moving Weighted Average costs, and order-item cost snapshots for analytical COGS calculations.

## Quick Start

### Prerequisites

- [Docker Engine](https://docs.docker.com/engine/install/) with Docker Compose v2 and BuildKit support.
- [Python 3.11](https://www.python.org/downloads/) and [uv](https://docs.astral.sh/uv/) for host-side data generation and Python development.
- [Node.js 22.x](https://nodejs.org/) and npm 10+ for host-side frontend development.

### Quick Start (One Command)

The launcher creates `.env` from `.env.example` if needed, starts the `core`, `batch`, and `streaming` profiles, waits for service readiness, and initializes missing Gold schemas:

```bash
make up
# or
./scripts/start_all.sh
```

Use `./scripts/start_all.sh --build` when rebuilding images. On a new MySQL volume, `database/schema.sql` creates all 28 source tables. The API initializes the catalog/admin; transactional history and populated Gold results require ingestion and a pipeline run. Existing volumes keep their schema and data; see the [database guide](database/README.md).

To stop the platform:

```bash
make down
# or
./scripts/stop_all.sh
```

---

### Step-by-Step Startup (Alternative)

#### 1. Prepare the Environment

```bash
cp .env.example .env
```

The example sets `COMPOSE_PROFILES=core,batch,streaming`. Profiles supplied with `--profile` add to the environment selection; they do not restrict it to a single profile.

#### 2. Start and Inspect the Services

```bash
docker compose --profile core --profile batch --profile streaming up -d --build

docker compose --profile core --profile batch --profile streaming ps
curl -fsS http://localhost:8000/health/ready
```

This path starts Compose services directly. See the [setup guide](docs/runbook/SETUP.md) for initialization dependencies, catalog operation, and troubleshooting.

#### 3. Service Access Endpoints

Ports and credentials below follow the default configuration; environment overrides may change them.

| Service | Port | URL | Credentials / Notes |
|---|---|---|---|
| **Storefront** | 3000 | `http://localhost:3000` | Public browsing |
| **Admin Console** | 3000 | `http://localhost:3000/admin` | Bootstrap admin from `API_BOOTSTRAP_ADMIN_*` |
| **BI Analytics Hub** | 3000 | `http://localhost:3000/admin/analytics` | Staff role or admin |
| **POS** | 3000 | `http://localhost:3000/store/pos` | Store manager / admin UI; store scope checked by API |
| **Backend API Docs** | 8000 | `http://localhost:8000/docs` | Swagger UI |
| **LibreDB Studio** | 3001 | `http://localhost:3001` | `LIBREDB_ADMIN_EMAIL` / `LIBREDB_ADMIN_PASSWORD` |
| **MinIO Console** | 9001 | `http://localhost:9001` | `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD` |
| **Polaris Console** | 8183 | `http://localhost:8183` | `POLARIS_ROOT_CLIENT_ID` / `POLARIS_ROOT_CLIENT_SECRET`; realm `POLARIS` |
| **Airflow UI** | 8080 | `http://localhost:8080` | `AIRFLOW_ADMIN_USER` / `AIRFLOW_ADMIN_PASSWORD` |
| **Spark Master UI** | 8082 | `http://localhost:8082` | Cluster status |
| **Trino** | 8084 | `http://localhost:8084` | Query engine / Web UI |
| **Flink Dashboard** | 8085 | `http://localhost:8085` | Job status |
| **Kafka** | 9092, 9094 | `localhost:9094` | External listener; Docker clients use `kafka:9092` |
| **Debezium Connect** | 8086 | `http://127.0.0.1:8086` | Connector lifecycle/status |
| **Trino Admin (optional)** | 8087 | `http://localhost:8087` | Separate `trino-admin` profile |

Additional staff accounts and store assignments are managed through the application.

### Service Identities

Storage workloads use seven scoped MinIO identities and four Polaris principals: `spark_writer`, `flink_writer`, `trino_reader`, and `trino_admin`. Each consumer mounts its own credential file. MinIO initialization uses the root identity to provision accounts; regular workloads use their assigned identities. Details are in the [setup guide](docs/runbook/SETUP.md).

---

## Architecture

`customer_credentials` is excluded from both the 27-table batch configuration and CDC capture. The three ingestion paths have different processing and serving boundaries:

```text
                    Customer / Staff / Admin
                              |
                       Next.js Storefront
                              |
                           FastAPI
                              |
                       MySQL (28 tables)

OLTP batch:
  MySQL -> Spark -> Landing Parquet -> Bronze -> Silver -> Gold

MySQL CDC:
  MySQL binlog -> Debezium -> Kafka -> Flink -> Bronze CDC events

Access logs:
  FastAPI middleware -> Kafka -> Flink -> Iceberg log tables
                                        (Landing / Bronze / Silver / Gold)

Storage / catalog:
  Iceberg data and metadata files on MinIO + Polaris REST catalog

Serving:
  Iceberg -> Trino -> FastAPI analytics -> Admin BI Hub / ECharts
  MySQL -----------> FastAPI operational metrics
  Trino -----------> LibreDB Studio
```

See the [system architecture](docs/architecture/SYSTEM_ARCHITECTURE_VISUAL.md) and [editable draw.io diagram](docs/diagram/08-system-architecture.drawio) for component boundaries.

### Technology Stack

| Layer | Component | Version / Image Tag | Responsibility |
|---|---|---|---|
| **Presentation** | Next.js / React | 15.5.21 / 19.1.8 | Storefront, POS, administration, BI Hub |
| **Visualization** | Apache ECharts | 6.1.0 | Dashboard charts |
| **Application** | FastAPI / SQLAlchemy | 0.116.1 / 2.0.41 | Transactions, auth/RBAC, logging, analytics API |
| **Operational DB** | MySQL | 8.4.5 | 28 OLTP tables; 27 analytical source tables |
| **Change Capture** | Debezium | 3.0.8 | Initial snapshot and row-binlog capture |
| **Event Streaming** | Apache Kafka | 3.8.0 | CDC and access-log topics |
| **Stream Processing** | Apache Flink | 1.19 | Access-log tables and Bronze CDC ingestion |
| **Object Storage** | MinIO | `latest-dev` | Landing, Iceberg files, and processing state |
| **Table Format** | Apache Iceberg | 1.10.1 | Tables, snapshots, and commits |
| **Catalog** | Apache Polaris | 1.6.0 | REST catalog and access control |
| **Batch Processing** | Apache Spark | 3.5.9 | Extraction, transformations, gates, maintenance |
| **Orchestration** | Apache Airflow | 2.10.5 | Batch and maintenance DAGs |
| **Metadata DB** | PostgreSQL | 16.8 | Polaris and Airflow metadata |
| **Query Engine** | Trino | 483 | SQL over Iceberg |
| **SQL UI** | LibreDB Studio | `latest` | Database/query interface |

The OLTP Gold model defines **6 dimensions, 5 facts, and 4 marts**. The log model defines **1 fact and 3 marts**. Row counts depend on the loaded dataset and completed pipeline runs.

The OLTP batch DAG is scheduled daily at 02:00 Asia/Ho_Chi_Minh; OLTP maintenance runs at 03:00 and streaming maintenance every two hours. Flink runs continuously with a configured 10-second checkpoint interval. That interval is not a measured end-to-end latency guarantee.

Source–Silver reconciliation runs before Gold processing; a second gate checks Gold counts, monetary parity, keys, references, lineage, and PII tokens. Failures mark the task/DAG unsuccessful and results are recorded in `lakehouse.system.data_quality_results`. These runtime gates remain part of data processing.

Batch cursors advance after Bronze; Gold tables commit independently. CDC does not yet apply changes into typed Silver/Gold, and the payments created_at cursor can miss older COD status updates. Maintenance targets an explicit subset of tables. Current transaction, permission, security and recovery limits are documented in [scope](docs/project/SCOPE.md) and [setup](docs/runbook/SETUP.md).

---

## Data Generation and Simulation

Data generation is configurable through `generator/configs/`. For example, `small.yml` specifies 500 customers, 60 products, 240 variants, 3,000 orders, and 12 months of history. Dates are anchored by `anchor_time` in the configuration.

### Real-Time Traffic Simulation

Import the matching SQL dataset first, then run virtual users against the API to produce live access-log events:

```bash
uv run --locked --package data-generator -- python scripts/simulate_web_traffic.py \
  --config generator/configs/small.yml \
  --duration 60 \
  --concurrency 5 \
  --error-rate 0.05
```

### Historical Data Backfill

#### Automated Backfill

The helper generates data in a temporary directory, imports/uploads it, and removes temporary files:

```bash
# Import OLTP history and upload raw historical access logs
./scripts/backfill_data.sh

# Select one source
./scripts/backfill_data.sh --mode oltp
./scripts/backfill_data.sh --mode logs
```

#### Manual Step-by-Step Backfill

```bash
# 1. Export and import OLTP history
uv run --locked --package data-generator -- generator export-sql \
  --config generator/configs/small.yml \
  --output data/generator/small.sql
./scripts/import_generated_sql.sh data/generator/small.sql

# 2. Export historical log files and upload them to raw Landing
uv run --locked --package data-generator -- generator export-logs \
  --config generator/configs/small.yml \
  --output-directory data/generator/access-logs \
  --expected-requests 60000
./scripts/upload_generated_logs.sh data/generator/access-logs
```

Uploaded JSONL files remain raw Landing assets: the current Flink job reads Kafka, so uploading files does not automatically process them into Gold. Live API traffic feeds the streaming path. Generated data is synthetic; it is not evidence of real customer behavior or production performance.

### Run the OLTP Batch Pipeline

DAGs start paused by default. After importing source data:

```bash
docker compose exec -T airflow-scheduler airflow dags unpause lakehouse_oltp_pipeline
docker compose exec -T airflow-scheduler airflow dags trigger lakehouse_oltp_pipeline
```

Importing the same SQL dataset twice is rejected by unique keys. See the [generator guide](generator/README.md) for configuration and account mapping.

---

### Operational Signals and Analytical Metrics

The BI Hub combines historical Trino queries with current MySQL indicators. API responses expose `data_source`, `is_degraded`, and `degraded_reason` so the UI can identify OLTP fallback or incomplete data.

| Role | Implemented Indicators | Primary Source | Interpretation |
|---|---|---|---|
| **Executive** | Order totals, revenue, COGS, profit, AOV, COD in transit | Gold + MySQL enrichment | Gold and OLTP fallback have different revenue rules |
| **Sales** | Store/channel contributions, top products, category shares | Gold facts and sales mart | Order counts across categories are not additive |
| **Store** | Today's revenue/orders, low stock, stockout SKUs | MySQL, restricted by store | Today's boundary uses Asia/Ho_Chi_Minh |
| **Inventory** | On-hand units/value, inbound batches, depletion signals | MySQL | Current inventory state |
| **Operations** | Pending orders, waiting time, failed shipments, COD failure by region, returns | MySQL | Field names and detection formulas are documented separately |
| **Marketing** | 30-day event funnel, coupon usage, recent negative reviews | Gold events + MySQL | Funnel counts events, not unique people or linked sessions |
| **System** | Gold freshness, order-count and monetary variance | Gold compared with MySQL | UI freshness thresholds differ from the daily batch schedule |

Refreshing a dashboard does not refresh batch Gold. Definitions, windows, denominators, and current limitations are detailed in the [Metrics Catalog](docs/architecture/METRICS_CATALOG.md).

System reconciliation renders one chart per metric so order counts and VND use independent scales. Fallback values are not shown as measured Gold comparisons.

---

## Development Commands

```bash
# Validate all active Compose profiles with the example environment
docker compose --env-file .env.example --profile core --profile batch --profile streaming --profile lakehouse-tools config --quiet

# Python static checks
uv lock --check
python3 -m compileall -q airflow/dags/
uvx ruff check .

# Frontend static checks and production build
npm --prefix apps/storefront ci
npm --prefix apps/storefront run lint
make typecheck
npm --prefix apps/storefront run build
```

### Continuous Integration

The [GitHub Actions workflow](.github/workflows/ci.yml) runs on pushes to `dev`, `main`, or `master`, pull requests, and manual dispatch. Pushes and pull requests that only change `docs/**`, `**.md`, `.gitignore`, or `LICENSE` are skipped.

| Job | Checks |
|---|---|
| **Repository validation** | Validate Compose with `.env.example` and the four profiles shown above; compile Airflow DAG Python files; run Ruff |
| **Storefront** | Install dependencies with `npm ci`; run lint, TypeScript typecheck, and the Next.js production build |

CI uses `--env-file .env.example` because `.env` is not committed and Compose requires the service-account credentials. `uv lock --check` is an additional local check in the commands above.

---

## Documentation Index

| Topic | Document | Purpose |
|---|---|---|
| **Documentation Map** | [docs/README.md](docs/README.md) | Current implementation references and retained thesis documents |
| **System Scope** | [SCOPE.md](docs/project/SCOPE.md) | DE goals, data boundaries, and implementation limits |
| **System Architecture** | [SYSTEM_ARCHITECTURE_VISUAL.md](docs/architecture/SYSTEM_ARCHITECTURE_VISUAL.md) | Components, batch/CDC/log flows, serving, and deployment |
| **Repository Layout** | [PROJECT_STRUCTURE.md](docs/architecture/PROJECT_STRUCTURE.md) | Source directories and pipeline entry points |
| **Lakehouse Model** | [LAKEHOUSE_DESIGN_PLAN.md](docs/project/LAKEHOUSE_DESIGN_PLAN.md) | Storage layout and dimension/fact/mart grains |
| **Metric Definitions** | [METRICS_CATALOG.md](docs/architecture/METRICS_CATALOG.md) | Formulas, sources, windows, and interpretation limits |
| **OLTP Schema** | [OLTP_SCHEMA.md](docs/architecture/OLTP_SCHEMA.md) | 28 source tables, relationships, and invariants |
| **Physical SQL Schema** | [database/schema.sql](database/schema.sql) | MySQL table definitions for empty-database initialization |
| **CDC** | [CDC_DASHBOARD_DATA_SPEC.md](docs/architecture/CDC_DASHBOARD_DATA_SPEC.md) | Capture contract, replay metadata, and recovery |
| **Access Logs** | [ACCESS_LOG_DESIGN.md](docs/architecture/ACCESS_LOG_DESIGN.md) | Event contract, privacy rules, and streaming/raw-file boundaries |
| **Data Generator** | [generator/README.md](generator/README.md) | Synthetic SQL/log generation and live traffic |
| **Diagrams** | [docs/diagram/README.md](docs/diagram/README.md) | Chapter 3 draw.io sources, SVG figures, and offline HTML viewer |
| **Business Analysis (B)** | [BUSINESS_DOMAIN.md](docs/architecture/BUSINESS_DOMAIN.md) | Implemented role views, business questions, sources, and KPI limits |
| **Business Requirements (C)** | [BUSINESS_REQUIREMENTS.md](docs/project/BUSINESS_REQUIREMENTS.md) | Retail, POS, inventory, delivery, and returns |
| **Object-Oriented Analysis (A)** | [OOSAD_ANALYSIS.md](docs/design-analysis/OOSAD_ANALYSIS.md) | Actors, Use Cases, Activity, and Sequence analysis |
| **Web Design (D)** | [WEB_DESIGN_PLAN.md](docs/project/WEB_DESIGN_PLAN.md) | Source application design |
| **Local Setup** | [SETUP.md](docs/runbook/SETUP.md) | Startup dependencies, identities, data operations, catalog inspection, and troubleshooting |
