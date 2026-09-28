# Documentation Index

This directory contains the architecture specifications, data schemas, operations guides, and development workflows for the D&K E-Commerce Data Platform.

## Guides by Category

### Architecture and Specifications

- [`project/SCOPE.md`](project/SCOPE.md): System boundaries, data source allowlists, analytical constraints, and acceptance criteria.
- [`architecture/PROJECT_STRUCTURE.md`](architecture/PROJECT_STRUCTURE.md): Monorepo organization, service boundaries, and dependency rules.
- [`architecture/MANAGEMENT_INFO_TECHNICAL_SPEC.md`](architecture/MANAGEMENT_INFO_TECHNICAL_SPEC.md): 7-Role Management Information System (MIS) specification, Trino distributed SQL engine, and Apache ECharts BI Hub.
- [`project/LAKEHOUSE_DESIGN_PLAN.md`](project/LAKEHOUSE_DESIGN_PLAN.md): Medallion architecture (Bronze, Silver, Gold), Iceberg table schemas, and data quality gates.
- [`project/WEB_DESIGN_PLAN.md`](project/WEB_DESIGN_PLAN.md): E-commerce storefront and API design specification.

### Data Contracts and Schemas

- [`architecture/OLTP_SCHEMA.md`](architecture/OLTP_SCHEMA.md): Complete OLTP schema reference — 27 MySQL tables with column-level definitions, check constraints, indexes, transaction catalogue (TX-01–TX-12), in-house logistics, 7-day returns, inventory ledger, MWA costing, lock ordering, race handling, and reconciliation rules.
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
| Apache Kafka | Done | Distributed event bus for streaming logs and domain events |
| Apache Flink | Done | 1.19 Streaming engine ingesting Kafka events into Iceberg |
| Trino (query engine) | Done | v483, distributed queries via Polaris and direct telemetry for BI Hub |
| Airflow (orchestration) | Done | v2.10.5, LocalExecutor |
| MySQL (OLTP source) | Done | 27 tables, synthetic data via generator & demo scenarios seed |
| LibreDB Studio (SQL IDE) | Done | Connected to MySQL, PostgreSQL, Trino |
| E-Commerce API + Storefront | Done | FastAPI (200 tests) + Next.js (27 routes) |

### Lakehouse Pipelines

| DAG / Pipeline | Status | Tables | Notes |
|---|---|---|---|
| `lakehouse_oltp_pipeline` | Done | 26 tables | Unified End-to-End OLTP DAG: Landing → Bronze → Silver → Gold |
| `kafka_to_lakehouse_pure_streaming` | Done | Real-time | Streaming logs into Landing, Bronze, Silver, Gold |
| `lakehouse_streaming_maintenance` | Done | 4 layers | Streaming logs healthcheck, Iceberg maintenance & Gold Marts rollup |

### Validation

| Check | Status | Result |
|---|---|---|
| OLTP extraction (MySQL → Landing) | Pass | 26 tables, Parquet + MD5 manifests |
| Landing → Bronze ingestion | Pass | 26 tables, 0 skipped, 0 quarantine |
| Bronze table counts (Trino) | Pass | Matches source |
| Polaris catalog + RBAC | Pass | Spark write, Trino read-only |
| Access logs → Bronze | Pass | `web_events` table (streaming + batch) |
| OLTP Bronze → Silver | Pass | 26 tables, MERGE, PII pseudonymization, quarantine |
| OLTP Silver → Gold | Pass | 6 dims, 5 facts, 4 marts built and verified via Trino (with COGS & margins) |
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