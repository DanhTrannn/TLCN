<!-- prettier-ignore -->
<div align="center">

# D&K E-Commerce Data Platform

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Node.js](https://img.shields.io/badge/Node.js->=22-339933?style=flat-square&logo=node.js&logoColor=white)](https://nodejs.org)
[![MySQL](https://img.shields.io/badge/MySQL-8.4-4479A1?style=flat-square&logo=mysql&logoColor=white)](https://mysql.com)
[![Apache Spark](https://img.shields.io/badge/Apache_Spark-3.5.9-E25A1C?style=flat-square&logo=apachespark&logoColor=white)](https://spark.apache.org)
[![Apache Iceberg](https://img.shields.io/badge/Apache_Iceberg-1.10.1-blue?style=flat-square&logo=apache&logoColor=white)](https://iceberg.apache.org)
[![Apache Polaris](https://img.shields.io/badge/Apache_Polaris-1.6.0-teal?style=flat-square&logo=apache&logoColor=white)](https://polaris.apache.org)
[![Apache Airflow](https://img.shields.io/badge/Apache_Airflow-2.10.5-017CEE?style=flat-square&logo=apacheairflow&logoColor=white)](https://airflow.apache.org)
[![Trino](https://img.shields.io/badge/Trino-483-DD00A1?style=flat-square&logo=trino&logoColor=white)](https://trino.io)
[![Apache Superset](https://img.shields.io/badge/Apache_Superset-4.1.2-0CA144?style=flat-square&logo=apache&logoColor=white)](https://superset.apache.org)

:star: If you find this project useful, consider giving it a star!

[Overview](#overview) • [Features](#features) • [Quick Start](#quick-start) • [Architecture](#architecture) • [Testing](#testing-and-verification) • [Documentation](#documentation-index)

</div>

The **D&K E-Commerce Data Platform** is a batch data lakehouse monorepo. It extracts transactional records from MySQL 8.4 and ingests structured web access logs from an e-commerce FastAPI backend. The platform cleans, normalizes, and models this data across Medallion layers (Bronze, Silver, Gold) using Apache Iceberg, Apache Spark, and Apache Polaris catalog. The output serves analytical queries via Trino, business intelligence dashboards in Apache Superset, and feature engineering pipelines for customer repurchase prediction.

> [!NOTE]
> The system batches access logs in 15-minute intervals and runs scheduled batch ETL jobs for OLTP data. It does not provide sub-minute streaming latency or Kafka/Flink event streaming.

## Overview

Building an analytical environment for an operational e-commerce database can place a high load on production systems. This platform provides a robust data lakehouse pattern to offload analytical queries, track historical access patterns, and train machine learning models without impacting operational performance.

The repository includes everything needed to run the data platform locally, including a modern Next.js 15 storefront, a FastAPI backend, a MySQL database with 17 relational tables, a deterministic synthetic data generator, and the complete Medallion lakehouse processing stack.

## Features

- **Operational Analytics:** Query historical order, product, inventory, and customer metrics without placing analytical load on the production MySQL database.
- **Access Log Analysis:** Inspect traffic patterns, latency distributions, error rates, and search keywords aggregated into hourly and daily summary tables.
- **Repurchase Modeling:** Generate point-in-time training features and 30-day repurchase labels from validated Gold transaction snapshots.
- **Deterministic Data Generator:** Generate 12 months of realistic Vietnamese e-commerce transactions and matching 30-day access logs using calibrated market distributions.
- **Idempotent Ingestion:** Multi-threaded Spark extractor with composite cursor tracking `(cursor_field, pk)` and cryptographic manifest validation.

## Quick Start

### Prerequisites

You need the following tools to run this platform locally:

- [Docker Engine](https://docs.docker.com/engine/install/) 24+ and Docker Compose v2.20+
- [Python 3.11](https://www.python.org/downloads/) with [`uv`](https://docs.astral.sh/uv/) package manager
- [Node.js](https://nodejs.org/) 22+ (for host storefront development)

### 1. Start Core Services

Clone the repository and launch the core operational stack (MySQL, FastAPI Backend, Next.js Storefront, MinIO S3, and Fluent Bit):

```bash
cp .env.example .env
docker compose --profile core up -d --build
```

Verify service readiness:

```bash
docker compose --profile core ps
curl -fsS http://localhost:8000/health/ready
```

### 2. Start Data Platform Services

Launch the Lakehouse processing and query services (Polaris Catalog, Spark Master/Worker, Airflow Scheduler/Webserver, Trino, and Apache Superset):

```bash
docker compose --profile batch --profile bi up -d
```

### 3. Service Access Endpoints

Once the services are running, access the following dashboards and endpoints:

| Service | Port | URL | Default Credentials |
|---|---|---|---|
| **Storefront** | 3000 | `http://localhost:3000` | (Public) |
| **Admin Console** | 3000 | `http://localhost:3000/admin` | `admin@web.local` / `Admin@12345` |
| **Backend API Docs** | 8000 | `http://localhost:8000/docs` | (Public Swagger UI) |
| **MinIO S3 Console** | 9001 | `http://localhost:9001` | `minioadmin` / `password` |
| **Polaris Catalog Console** | 8183 | `http://localhost:8183` | `admin` / `password` (Realm: `POLARIS`) |
| **Airflow Web UI** | 8080 | `http://localhost:8080` | `airflow` / `password` |
| **Spark Master UI** | 8082 | `http://localhost:8082` | (Web UI) |
| **Trino Query Engine** | 8084 | `http://localhost:8084` | `trino` |
| **Apache Superset** | 8088 | `http://localhost:8088` | `admin` / `password` |

---

## Architecture

The system processes data from two main sources: transactional data from MySQL and structured access logs from FastAPI. It leverages an object storage landing zone and an Apache Spark ETL pipeline to load data into Apache Iceberg tables.

```text
               Customer / Admin Traffic
                          │
                          ▼
            Next.js Storefront (Port 3000)
                          │
                     HTTP / JSON
                          │
                          ▼
             FastAPI API (Port 8000)
            /                       \
   Short Transactions          Structured Logs (stdout)
          /                           \
         ▼                             ▼
    MySQL 8.4                     Fluent Bit
  (16 OLTP tables)            (15m micro-batch gzip)
         │                             │
         └──────────────┬──────────────┘
                        ▼
               MinIO S3 Landing Zone
           s3://lakehouse/landing/
                        │
                  Apache Spark
           (Medallion ETL Pipeline)
                        │
            Apache Iceberg + Polaris
           (Bronze → Silver → Gold)
                        │
                  Trino SQL Engine
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
    Apache Hue     Apache Superset  ML Repurchase
    (Query UI)     (BI Dashboards)   Prediction
```

### Technology Stack

| Layer | Component | Version | Responsibility |
|---|---|---|---|
| **Presentation** | Next.js / React | 15.5 / 19.1 | Customer storefront and store operations console |
| **Application** | FastAPI / SQLAlchemy | 0.116 / 2.0 | Transactional business logic and structured access logging |
| **Operational DB** | MySQL | 8.4 LTS | Primary relational database (17 tables, 16 analytical) |
| **Log Collector** | Fluent Bit | 4.2.3 | Container log tailing, disk buffering, S3 gzip flushing |
| **Object Storage** | MinIO | Latest | S3-compatible Lakehouse storage (`lakehouse` bucket) |
| **Table Catalog** | Apache Polaris | 1.6.0 | REST catalog managing Iceberg namespaces and RBAC |
| **Processing** | Apache Spark | 3.5.9 | Batch ingestion, data quality checks, Iceberg writes |
| **Orchestration** | Apache Airflow | 2.10.5 | DAG scheduling and job orchestration |
| **Query Engine** | Trino | 483 | Distributed SQL query engine reading Iceberg tables |
| **Query UI** | Apache Hue | 4.11.0 | Interactive SQL editor and data exploration interface for Trino |
| **Visualization** | Apache Superset | 4.1.2 | Executive and operational BI dashboards |

---

## Data Generation and Simulation

The repository provides two traffic generation mechanisms: real-time simulation against live services and deterministic historical backfill.

### Real-Time Traffic Simulation

Run concurrent virtual users executing browsing, search, cart, checkout, and review actions against the live API:

```bash
uv run --package data-generator -- python scripts/simulate_web_traffic.py \
  --duration 60 \
  --concurrency 5 \
  --error-rate 0.05
```

### Historical Data Backfill

Generate and ingest 12 months of deterministic OLTP transactions and 30 days of matching access logs.

#### Automated Backfill (Recommended — auto-cleanup with no temporary files left on host):

```bash
# Backfill both OLTP MySQL transactions and MinIO Access Logs
./scripts/backfill_data.sh

# Or backfill individually
./scripts/backfill_data.sh --mode oltp  # MySQL database only
./scripts/backfill_data.sh --mode logs  # MinIO Landing Zone only
```

#### Manual Step-by-Step Backfill:

```bash
# 1. Export SQL transaction history & import into MySQL
uv run --locked --package data-generator -- generator export-sql \
  --config generator/configs/small.yml \
  --output data/generator/small.sql
./scripts/import_generated_sql.sh data/generator/small.sql

# 2. Export operational access logs & upload to MinIO S3 Landing Zone
uv run --locked --package data-generator -- generator export-logs \
  --config generator/configs/small.yml \
  --output-directory data/generator/access-logs \
  --expected-requests 60000
./scripts/upload_generated_logs.sh data/generator/access-logs
```

---

## Testing and Verification

Run the full test suite across all Python workspace packages and the frontend (171 Python tests total):

```bash
# Backend API tests (63 tests)
uv run --locked --package ecommerce-api --extra dev -- pytest services/ecommerce-api/tests

# Data Generator tests (54 tests)
uv run --locked --package data-generator --extra dev -- pytest generator/tests

# Batch Pipeline tests (54 tests: Bronze, Silver & Gold)
PYTHONPATH=pipelines/src uv run --locked --package batch-pipeline --extra dev -- pytest pipelines/tests

# Run all Python tests in workspace
PYTHONPATH=pipelines/src:generator/src:services/ecommerce-api uv run pytest

# Frontend type check and production build
npm --prefix apps/storefront run typecheck
npm --prefix apps/storefront run build

# Lakehouse cluster smoke test
./scripts/lakehouse_smoke.sh
```

---

## Documentation Index

Explore the detailed architecture and planning documents:

| Topic | Document | Purpose |
|---|---|---|
| **System Scope** | [`docs/project/SCOPE.md`](docs/project/SCOPE.md) | Technical requirements, data boundaries, and acceptance criteria |
| **Architecture Layout** | [`docs/architecture/PROJECT_STRUCTURE.md`](docs/architecture/PROJECT_STRUCTURE.md) | Monorepo layout, container isolation, and dependency rules |
| **OLTP Schema** | [`docs/architecture/OLTP_SCHEMA.md`](docs/architecture/OLTP_SCHEMA.md) | Relational tables, foreign keys, transaction boundaries, and invariants |
| **Access Logs** | [`docs/architecture/ACCESS_LOG_DESIGN.md`](docs/architecture/ACCESS_LOG_DESIGN.md) | Event schema contract, privacy rules, Fluent Bit buffering, S3 layout |
| **Lakehouse Plan** | [`docs/project/LAKEHOUSE_DESIGN_PLAN.md`](docs/project/LAKEHOUSE_DESIGN_PLAN.md) | Medallion architecture (Bronze/Silver/Gold), Iceberg schemas, and DQ rules |
| **Web Design Plan** | [`docs/project/WEB_DESIGN_PLAN.md`](docs/project/WEB_DESIGN_PLAN.md) | E-commerce application structure, endpoints, and transaction models |
| **Design System** | [`docs/design-system/DESIGN.md`](docs/design-system/DESIGN.md) | UI tokens, typography, component guidelines, and color palette |
| **Batch Ingestion (OLTP)** | [`docs/pipelines/batch/INGEST_OLTP_TO_LANDING.md`](docs/pipelines/batch/INGEST_OLTP_TO_LANDING.md) | Spark OLTP extraction to MinIO Landing and manifest validation |
| **Bronze Ingestion (OLTP)** | [`docs/pipelines/batch/INGEST_OLTP_LANDING_TO_BRONZE.md`](docs/pipelines/batch/INGEST_OLTP_LANDING_TO_BRONZE.md) | Spark ingestion of OLTP data from Landing to Iceberg Bronze tables |
| **Bronze Ingestion (Logs)** | [`docs/pipelines/batch/INGEST_LOGS_LANDING_TO_BRONZE.md`](docs/pipelines/batch/INGEST_LOGS_LANDING_TO_BRONZE.md) | Spark ingestion of Access Logs from Landing to Iceberg Bronze table (`web_events`) |
| **Silver Ingestion (OLTP)** | [`docs/pipelines/batch/INGEST_OLTP_BRONZE_TO_SILVER.md`](docs/pipelines/batch/INGEST_OLTP_BRONZE_TO_SILVER.md) | Spark ingestion of OLTP data from Bronze to Silver with MERGE |
| **Silver Ingestion (Logs)** | [`docs/pipelines/batch/INGEST_LOGS_BRONZE_TO_SILVER.md`](docs/pipelines/batch/INGEST_LOGS_BRONZE_TO_SILVER.md) | Spark ingestion of Access Logs from Bronze to Silver (`silver_logs`) |
| **Gold Ingestion (Logs)** | [`docs/pipelines/batch/BUILD_LOGS_GOLD.md`](docs/pipelines/batch/BUILD_LOGS_GOLD.md) | Spark transformation of Silver logs to Gold Fact and Data Marts |
| **Local Runbook** | [`docs/runbook/SETUP.md`](docs/runbook/SETUP.md) | Step-by-step Lakehouse startup, RBAC setup, and smoke testing |
| **Startup Sequence** | [`docs/runbook/STARTUP_FLOW.md`](docs/runbook/STARTUP_FLOW.md) | Service bootstrap sequence, migrations, and health checks |
| **Runbook Index** | [`docs/runbook/README.md`](docs/runbook/README.md) | Central index for operational tasks, commands, and validation |
