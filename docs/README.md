# Documentation Index

This directory contains the architecture specifications, data schemas, operations guides, and development workflows for the D&K E-Commerce Data Platform.

## Guides by Category

### Architecture and Specifications

- [`project/SCOPE.md`](project/SCOPE.md): System boundaries, data source allowlists, analytical constraints, and acceptance criteria.
- [`architecture/PROJECT_STRUCTURE.md`](architecture/PROJECT_STRUCTURE.md): Monorepo organization, service boundaries, and dependency rules.
- [`project/LAKEHOUSE_DESIGN_PLAN.md`](project/LAKEHOUSE_DESIGN_PLAN.md): Medallion architecture (Bronze, Silver, Gold), Iceberg table schemas, and data quality gates.
- [`project/WEB_DESIGN_PLAN.md`](project/WEB_DESIGN_PLAN.md): E-commerce storefront and API design specification.
- [`design-system/DESIGN.md`](design-system/DESIGN.md): UI tokens, typography, component guidelines, and Storefront color palette.

### Data Contracts and Schemas

- [`architecture/OLTP_SCHEMA.md`](architecture/OLTP_SCHEMA.md): Complete logical schema for 17 MySQL tables, relational constraints, and invariant rules (migrations 0001–0009).
- [`architecture/ACCESS_LOG_DESIGN.md`](architecture/ACCESS_LOG_DESIGN.md): JSON event schema, Fluent Bit collection pipeline, privacy redactions, and S3 partition layouts.
- [`contracts/ecommerce-access-v1.schema.json`](contracts/ecommerce-access-v1.schema.json): Formal JSON Schema definition for access log records.

### Pipelines and ETL

- [`pipelines/batch/INGEST_OLTP_TO_LANDING.md`](pipelines/batch/INGEST_OLTP_TO_LANDING.md): Spark batch extraction of 16 OLTP tables to MinIO Landing with composite cursors and manifest validation.
- [`pipelines/batch/INGEST_OLTP_LANDING_TO_BRONZE.md`](pipelines/batch/INGEST_OLTP_LANDING_TO_BRONZE.md): Spark ingestion of OLTP data from Landing Zone to Iceberg Bronze tables with lineage metadata.
- [`pipelines/batch/INGEST_LOGS_LANDING_TO_BRONZE.md`](pipelines/batch/INGEST_LOGS_LANDING_TO_BRONZE.md): Spark ingestion of structured access logs from Landing Zone to Iceberg Bronze table (`web_events`).

### Operations and Deployment

- [`runbook/README.md`](runbook/README.md): Index of operational workflows, quick start commands, and validation.
- [`runbook/SETUP.md`](runbook/SETUP.md): Local cluster setup, Polaris RBAC bootstrap, and end-to-end smoke testing.
- [`runbook/STARTUP_FLOW.md`](runbook/STARTUP_FLOW.md): Container startup sequence, database migrations, and health verification.

## Directory Structure

| Directory | Content Type | Focus Area |
|---|---|---|
| [`project/`](project/) | Specification | Scope, Lakehouse Medallion roadmap, and Web Design plans |
| [`architecture/`](architecture/) | Reference | System structure, OLTP schema, and access log contracts |
| [`contracts/`](contracts/) | Schema | JSON Schema definitions for telemetry contracts |
| [`pipelines/`](pipelines/) | Guide | Batch ETL extraction and Airflow DAG implementation guides |
| [`runbook/`](runbook/) | How-To | Deployment, local verification, and disaster recovery runbooks |
| [`design-system/`](design-system/) | Reference | UI tokens, typography, and Storefront component guidelines |
