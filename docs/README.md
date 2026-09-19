# Documentation Index

This directory contains the architecture specifications, data schemas, operations guides, and development workflows for the D&K E-Commerce Data Platform.

## Guides by Category

### Architecture and Specifications

- [`project/SCOPE.md`](project/SCOPE.md): System boundaries, data source allowlists, analytical constraints, and acceptance criteria.
- [`architecture/PROJECT_STRUCTURE.md`](architecture/PROJECT_STRUCTURE.md): Monorepo organization, service boundaries, and dependency rules.
- [`project/LAKEHOUSE_DESIGN_PLAN.md`](project/LAKEHOUSE_DESIGN_PLAN.md): Medallion architecture (Bronze, Silver, Gold), Iceberg table schemas, and data quality gates.
- [`project/WEB_DESIGN_PLAN.md`](project/WEB_DESIGN_PLAN.md): E-commerce storefront and API design specification.

### Data Contracts and Schemas

- [`architecture/OLTP_SCHEMA.md`](architecture/OLTP_SCHEMA.md): Complete OLTP schema reference — 25 MySQL tables with column-level definitions, check constraints, indexes, transaction catalogue (TX-01–TX-12), in-house logistics, 7-day returns, inventory ledger, lock ordering, race handling, and reconciliation rules.
- [`architecture/ACCESS_LOG_DESIGN.md`](architecture/ACCESS_LOG_DESIGN.md): JSON event schema, Fluent Bit collection pipeline, privacy redactions, and S3 partition layouts.
- [`contracts/ecommerce-access-v1.schema.json`](contracts/ecommerce-access-v1.schema.json): Formal JSON Schema definition for access log records.

### Operations and Deployment

- [`runbook/README.md`](runbook/README.md): Index of operational workflows, quick start commands, and validation.
- [`runbook/SETUP.md`](runbook/SETUP.md): Local cluster setup, Polaris RBAC bootstrap, and end-to-end smoke testing.
- [`runbook/STARTUP_FLOW.md`](runbook/STARTUP_FLOW.md): Container startup sequence, database migrations, and health verification.

## Progress

### Infrastructure

| Component | Status | Notes |
|---|---|---|
| MinIO (S3 storage) | Done | `lakehouse` bucket, Landing + Warehouse paths |
| Polaris (Iceberg REST catalog) | Done | RBAC: `spark_writer`, `trino_reader`, `trino_admin` |
| Spark (compute) | Done | 3.5.9 + Iceberg 1.10.1, standalone cluster |
| Trino (query engine) | Done | v483, read-only via Polaris |
| Airflow (orchestration) | Done | v2.10.5, LocalExecutor |
| MySQL (OLTP source) | Done | 25 tables, synthetic data via generator |
| LibreDB Studio (SQL IDE) | Done | Connected to MySQL, PostgreSQL, Trino |
| Superset (dashboards) | Done | Connected to Trino |
| E-Commerce API + Storefront | Done | FastAPI + Next.js |

### Batch Pipelines

| DAG | Status | Tables | Notes |
|---|---|---|---|
| `lakehouse_logs_pipeline` | Done | 4 layers | Master Logs DAG: Landing → Bronze → Silver → Gold |
| `ingest_oltp_batch` | Done | 24/24 | MySQL → Landing (Parquet + manifests) |
| `ingest_oltp_landing_to_bronze` | Done | 24/24 | Landing → Bronze (auto-discover run_id) |
| `ingest_oltp_bronze_to_silver` | Done | 24/24 | Bronze → Silver (MERGE, PII, quarantine) |
| `build_oltp_gold` | Done | 6 dims, 5 facts, 4 marts | Star schema (`dim_*`, `fact_*`), sales, logistics, returns, inventory marts |
| Iceberg maintenance | Pending | - | Compaction, snapshot expiration, orphan cleanup |

### Validation

| Check | Status | Result |
|---|---|---|
| OLTP extraction (MySQL → Landing) | Pass | 24 tables, Parquet + MD5 manifests |
| Landing → Bronze ingestion | Pass | 24 tables, 0 skipped, 0 quarantine |
| Bronze table counts (Trino) | Pass | Matches source |
| Polaris catalog + RBAC | Pass | Spark write, Trino read-only |
| Access logs → Bronze | Pass | `web_events` table (1,193+ events) |
| OLTP Bronze → Silver | Pass | 24 tables, MERGE, PII pseudonymization, quarantine |
| OLTP Silver → Gold | Pass | 6 dims, 5 facts, 4 marts built and verified via Trino |
| Logs Bronze → Silver | Pass | `silver_logs` window dedup, struct flattening |
| Logs Silver → Gold | Pass | `fact_web_events`, `mart_hourly_route_metrics`, `mart_daily_product_demand` |


---

## Directory Structure

| Directory | Content Type | Focus Area |
|---|---|---|
| [`project/`](project/) | Specification | Scope, Lakehouse Medallion roadmap, and Web Design plans |
| [`architecture/`](architecture/) | Reference | System structure, OLTP schema, and access log contracts |
| [`contracts/`](contracts/) | Schema | JSON Schema definitions for telemetry contracts |
| [`runbook/`](runbook/) | How-To | Deployment, local verification, and disaster recovery runbooks |