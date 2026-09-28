<!-- prettier-ignore -->
<div align="center">

# D&K E-Commerce Data Platform

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Node.js](https://img.shields.io/badge/Node.js->=22-339933?style=flat-square&logo=node.js&logoColor=white)](https://nodejs.org)
[![MySQL](https://img.shields.io/badge/MySQL-8.4-4479A1?style=flat-square&logo=mysql&logoColor=white)](https://mysql.com)
[![Apache Kafka](https://img.shields.io/badge/Apache_Kafka-3.7-231F20?style=flat-square&logo=apachekafka&logoColor=white)](https://kafka.apache.org)
[![Apache Flink](https://img.shields.io/badge/Apache_Flink-1.19-E6526F?style=flat-square&logo=apacheflink&logoColor=white)](https://flink.apache.org)
[![Apache Spark](https://img.shields.io/badge/Apache_Spark-3.5.9-E25A1C?style=flat-square&logo=apachespark&logoColor=white)](https://spark.apache.org)
[![Apache Iceberg](https://img.shields.io/badge/Apache_Iceberg-1.10.1-blue?style=flat-square&logo=apache&logoColor=white)](https://iceberg.apache.org)
[![Apache Polaris](https://img.shields.io/badge/Apache_Polaris-1.6.0-teal?style=flat-square&logo=apache&logoColor=white)](https://polaris.apache.org)
[![Trino](https://img.shields.io/badge/Trino-483-DD00A1?style=flat-square&logo=trino&logoColor=white)](https://trino.io)
[![Apache Superset](https://img.shields.io/badge/Apache_Superset-4.1.2-0CA144?style=flat-square&logo=apache&logoColor=white)](https://superset.apache.org)
[![Apache ECharts](https://img.shields.io/badge/Apache_ECharts-5.5-AA344D?style=flat-square&logo=apacheecharts&logoColor=white)](https://echarts.apache.org)

:star: If you find this project useful, consider giving it a star!

[Overview](#overview) • [Features](#features) • [Quick Start](#quick-start) • [Architecture](#architecture) • [Testing](#testing-and-verification) • [Documentation](#documentation-index)

</div>

The **D&K E-Commerce Data Platform** is an enterprise-grade hybrid lakehouse monorepo combining high-throughput transactional processing, real-time event streaming, and analytical data lakehouse architecture. It operates an operational MySQL 8.4 database with 27 relational tables (26 analytical tables ingested into Lakehouse), a FastAPI e-commerce backend, and a modern Next.js 15 storefront. The data platform combines Apache Kafka + Apache Flink for real-time streaming ingestion alongside Apache Spark for Medallion batch processing (Bronze, Silver, Gold) on Apache Iceberg with Polaris catalog. The analytical layer powers distributed SQL queries via Apache Trino, direct executive and multi-role visual analytics via Apache ECharts in the Admin BI Hub (`/admin/analytics`), and deep exploratory dashboards in Apache Superset.

> [!NOTE]
> The platform implements a **Hybrid Batch & Streaming Architecture**: Kafka & Apache Flink handle real-time clickstream events and streaming ingestion into Iceberg, while Apache Spark orchestrates scheduled batch transformations across Bronze, Silver, and Gold Medallion layers.

## Overview

Building an analytical environment for an operational e-commerce database can place a high load on production systems. This platform provides a robust data lakehouse pattern to offload analytical queries, track historical access patterns, and train machine learning models without impacting operational performance.

The repository includes everything needed to run the data platform locally, including a modern Next.js 15 storefront, a FastAPI backend, a MySQL database with 27 relational business tables (26 analytical tables), a deterministic synthetic data generator, and the complete Medallion lakehouse processing stack.

## Features

- **Inbound Production & MWA Costing:** Internal workshop garment batches, Moving Weighted Average (MWA) inventory costing recalculation, and snapshot COGS at checkout for real-time gross margin tracking.
- **Full Order & Logistics Lifecycle:** End-to-end shipper dispatch, boom COD handling (3-attempt threshold and automatic COD blocking), customer 7-day return/refund management, and customer-confirmed order completion (`delivered -> completed`).
- **7-Role Interactive BI Analytics Hub (`/admin/analytics`):** Tailored operational views for Executive (CEO), Sales, Store Managers (with Row-Level Security), Inventory, Operations & Logistics, Marketing Funnel, and System Admin with reconciliation audits, integrated with Apache ECharts and Apache Trino distributed query engine.
- **Hybrid Streaming & Batch Processing:** Real-time event streaming via Apache Kafka and Apache Flink alongside scheduled Apache Spark Medallion batch ETL.
- **Operational Analytics:** Query historical order, product, inventory, and customer metrics without placing analytical load on the production MySQL database.
- **Access Log Analysis:** Inspect traffic patterns, latency distributions, error rates, and search keywords aggregated into hourly and daily summary tables.
- **Repurchase Modeling:** Generate point-in-time training features and 30-day repurchase labels from validated Gold transaction snapshots.
- **Deterministic Data Generator:** Generate 12 months of realistic Vietnamese e-commerce transactions and matching 30-day access logs using calibrated market distributions.
- **Idempotent Ingestion:** Multi-threaded Spark extractor with composite cursor tracking `(cursor_field, pk)` and cryptographic manifest validation.
- **POS (Point of Sale):** Staff sell at store counter, search products by SKU/name, create completed transactions with store inventory deduction.
- **Multi-City Inventory:** Store-level inventory tracking across 5 cities and 6 stores, with city-based product availability.
- **Role-Based UI:** Strict RBAC panels for Admin (`/admin`), Store Manager (`/store`), and 7 Business Roles (`/admin/analytics`).
- **Structured Checkout:** Address form with 34 Vietnamese provinces (post-1/7/2025 merger), wards, and street fields.

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

To start the real-time streaming pipeline (Kafka + Apache Flink):

```bash
docker compose --profile streaming up -d
```

### 3. Service Access Endpoints

Once the services are running, access the following dashboards and endpoints:

| Service | Port | URL | Default Credentials |
|---|---|---|---|
| **Storefront** | 3000 | `http://localhost:3000` | (Public) |
| **Admin Console** | 3000 | `http://localhost:3000/admin` | `admin@web.local` / `Admin@12345` |
| **BI Analytics Hub (7 Roles)** | 3000 | `http://localhost:3000/admin/analytics` | `admin@web.local` / `Admin@12345` |
| **POS (Point of Sale)** | 3000 | `http://localhost:3000/admin/pos` | `store.manager@dk.local` / `Admin@12345` |
| **Backend API Docs** | 8000 | `http://localhost:8000/docs` | (Public Swagger UI) |
| **LibreDB Studio (SQL IDE)** | 3001 | `http://localhost:3001` | (Web SQL Studio) |
| **MinIO S3 Console** | 9001 | `http://localhost:9001` | `minioadmin` / `password` |
| **Polaris Catalog Console** | 8183 | `http://localhost:8183` | `admin` / `password` (Realm: `POLARIS`) |
| **Airflow Web UI** | 8080 | `http://localhost:8080` | `airflow` / `password` |
| **Spark Master UI** | 8082 | `http://localhost:8082` | (Web UI) |
| **Trino Query Engine** | 8084 | `http://localhost:8084` | `trino` |
| **Flink Dashboard** | 8085 | `http://localhost:8085` | (Web UI) |
| **Apache Superset** | 8088 | `http://localhost:8088` | `admin` / `password` |
| **Kafka Broker** | 9092, 9094 | `localhost:9092` | PLAINTEXT |

---

## Architecture

The system processes data from two operational pipelines: transactional business entities from MySQL (27 tables) and structured clickstream/access logs from FastAPI. It combines real-time streaming ingestion via Kafka + Flink and batch Medallion pipelines via Spark + Iceberg.

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
                      /           │           \
            Short TX /            │            \ Structured Logs
                    ▼             ▼             ▼
               MySQL 8.4     Apache Kafka   Fluent Bit
            (27 OLTP tables)  (Event Bus)   (15m micro-batch gzip)
                    │             │             │
                    │             ▼             │
                    │       Apache Flink        │
                    │    (Streaming Ingest)     │
                    │             │             │
                    └─────────────┼─────────────┘
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
                        /        │       \
                       ▼         ▼        ▼
                LibreDB Studio  Apache   Admin BI Hub (ECharts)
                   (Port 3001)  Superset   (/admin/analytics)
```

### Technology Stack

| Layer | Component | Version | Responsibility |
|---|---|---|---|
| **Presentation** | Next.js / React | 15.5 / 19.1 | Customer storefront, POS, and 7-Role BI Hub |
| **Visual Analytics** | Apache ECharts | 5.5 | Interactive role-based charts and Trino live telemetry |
| **Application** | FastAPI / SQLAlchemy | 0.116 / 2.0 | Transactional business logic (27 tables, 15 modules) |
| **Operational DB** | MySQL | 8.4 LTS | Primary relational database (27 tables, 26 analytical) |
| **Event Streaming** | Apache Kafka | 3.7 | Distributed event streaming backbone |
| **Stream Processing** | Apache Flink | 1.19 | Real-time event consumption and Iceberg streaming ingest |
| **Log Collector** | Fluent Bit | 4.2.3 | Container log tailing, disk buffering, S3 gzip flushing |
| **Object Storage** | MinIO | Latest | S3-compatible Lakehouse storage (`lakehouse` bucket) |
| **Table Catalog** | Apache Polaris | 1.6.0 | REST catalog managing Iceberg namespaces and RBAC |
| **Processing** | Apache Spark | 3.5.9 | Batch ingestion, data quality checks, Iceberg writes |
| **Orchestration** | Apache Airflow | 2.10.5 | DAG scheduling and job orchestration |
| **Query Engine** | Trino | 483 | Distributed SQL query engine reading Iceberg tables |
| **Query UI** | LibreDB Studio | Latest | Web-based SQL IDE for MySQL, PostgreSQL, and Trino |
| **Visualization** | Apache Superset | 4.1.2 | Multi-dimensional BI exploratory dashboards |

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

Run the full test suite across all Python workspace packages and the frontend (361 Python tests total):

```bash
# Backend API tests (200 tests: auth, cart, checkout, pos, inbound, analytics RBAC, logistics, returns)
uv run --locked --package ecommerce-api --extra dev -- pytest services/ecommerce-api/tests

# Data Generator tests (55 tests: distributions, synthetic seed, export validation)
uv run --locked --package data-generator --extra dev -- pytest generator/tests

# Batch Pipeline tests (106 tests: Bronze, Silver, Gold Marts & Financial parity)
uv run pytest pipelines/tests

# Run all Python tests in workspace
PYTHONPATH=pipelines/src:generator/src:services/ecommerce-api uv run pytest

# Frontend type check and production build (27 static & dynamic routes)
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
| **Business Requirements** | [`docs/project/BUSINESS_REQUIREMENTS.md`](docs/project/BUSINESS_REQUIREMENTS.md) | Full e-commerce operations, POS, Lakehouse mapping & extensions |
| **Architecture Layout** | [`docs/architecture/PROJECT_STRUCTURE.md`](docs/architecture/PROJECT_STRUCTURE.md) | Monorepo layout, container isolation, and dependency rules |
| **OLTP Schema** | [`docs/architecture/OLTP_SCHEMA.md`](docs/architecture/OLTP_SCHEMA.md) | Relational tables, foreign keys, transaction boundaries, and invariants |
| **Management Specs** | [`docs/architecture/MANAGEMENT_INFO_TECHNICAL_SPEC.md`](docs/architecture/MANAGEMENT_INFO_TECHNICAL_SPEC.md) | 7-Role BI Hub, Trino query engine, and Superset reporting |
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
