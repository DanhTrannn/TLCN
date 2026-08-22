# Lakehouse Architecture Plan

This document outlines the architecture, storage formats, compute engines, and table designs for the D&K E-Commerce Data Lakehouse.

## 1. Core Architecture Decisions

The platform employs a decoupled storage and compute architecture:

- **Storage:** MinIO object storage (`lakehouse` bucket) holds all Landing files and Iceberg data/metadata files.
- **Table Format:** Apache Iceberg (v1.10.1) is the exclusive table format for Bronze, Silver, and Gold layers.
- **Catalog:** Apache Polaris (v1.6.0) acts as the REST catalog, managing namespaces, tables, and RBAC policies.
- **Processing (Writer):** Apache Spark (v3.5.9) handles all extraction, parsing, transformation, data quality checks, and Iceberg table commits.
- **Serving (Reader):** Trino (v483) serves SQL queries directly from Iceberg tables via Polaris REST catalog.
- **Query UI:** Apache Hue (v4.11.0) provides an interactive SQL editor and data exploration interface for Trino.
- **Visualization:** Apache Superset (v4.1.2) connects to Trino to serve executive and operational dashboards.
- **Orchestration:** Apache Airflow (v2.10.5) manages all pipeline dependencies, schedules, and retries.

> [!IMPORTANT]  
> Spark is the only engine permitted to write to Iceberg tables. Trino and Superset have read-only access. Transactional web APIs must not communicate directly with Spark or Trino.

---

## 2. Namespace and Storage Layout

### 2.1. Polaris Namespaces
The `lakehouse` catalog contains five logical namespaces:
- `lakehouse.bronze`
- `lakehouse.silver`
- `lakehouse.gold`
- `lakehouse.quarantine`
- `lakehouse.system`

### 2.2. Object Storage (MinIO) Layout
Data is physically organized in UTC-based partition paths within the `lakehouse` bucket:
- **Landing Zone:** Immutable raw data `s3://lakehouse/landing/`
  - OLTP: `landing/oltp/<table>/extract_date=YYYY-MM-DD/run_id=<run_id>/...`
  - Access Logs: `landing/logs/ingest_date=YYYY-MM-DD/ingest_hour=HH/service=ecommerce-api/<uuid>.jsonl.gz`
- **Warehouse:** Managed Iceberg tables `s3://lakehouse/warehouse/<namespace>/<table>/`
- **State:** Checkpoints, committed cursors, and run metadata `s3://lakehouse/state/cursor/<table>.json`

---

## 3. Data Processing Flow

### 3.1. Landing Zone
- **OLTP Ingestion:** Airflow triggers a Spark batch job (`extract_oltp.py`) to extract incremental MySQL rows using read-only accounts and composite cursors `(cursor_field, pk)`. Data is written as Parquet files with cryptographic MD5 manifests (`manifest.json`).
- **Access Logs:** The API emits JSON logs to stdout; Fluent Bit flushes 15-minute gzip-compressed micro-batches to the Landing zone.

### 3.2. Bronze Layer
Spark reads Landing files and performs append-only commits to Bronze Iceberg tables using a **Dead-Letter (Guarded)** strategy:
- Preserves the raw source representation exactly as extracted using Spark `PERMISSIVE` read mode.
- Appends three lineage metadata columns to every row: `_run_id` (Airflow DAG Run ID, enables idempotent reruns), `_source_file` (absolute S3 path for auditability), `_ingested_at_utc` (ingest timestamp for incremental Silver processing).
- **Circuit Breaker:** If the fraction of corrupt records in a batch exceeds the error threshold (default 1%), the job raises `RuntimeError` and fails fast. This prevents silent, catastrophic schema changes from propagating.
- **Decentralized Quarantine:** Corrupt records below the threshold are routed to a per-table quarantine namespace (`lakehouse.quarantine.<table_name>_errors`), not a shared sink. This isolates replay scope and prevents cross-domain resource contention.
- Replay of quarantined records is done via ad-hoc jobs that write directly to the Bronze table; the Silver MERGE handles late arrival without ordering issues.

### 3.3. Silver Layer
Spark transforms Bronze data into typed, deduplicated tables.
- **OLTP:** Standardizes timestamps to UTC, deduplicates by source identity, and applies `MERGE` (UPSERT) operations for mutable tables. Validates primary and foreign keys.
- **Logs:** Parses JSON, deduplicates by `request_id`, normalizes routes, and hashes actor keys.
- **Semantic Quarantine:** Routes records violating business constraints to `lakehouse.quarantine.silver_data_quarantine`.

### 3.4. Gold Layer
Spark builds Star Schema models and aggregated Data Marts.
- **Dimensions:** `dim_customer`, `dim_product`, `dim_date`, etc.
- **Facts:** `fact_order`, `fact_payment`, `fact_web_request`, etc.
- **Marts:** `mart_sales_daily`, `mart_hourly_route_metrics`, `mart_daily_product_demand`, `mart_daily_search_keywords`.
- **Publication Gate:** Gold snapshots are only published if source-to-target reconciliation checks (exact row counts, exact revenue totals) pass.

---

## 4. Iceberg Maintenance Strategy

To maintain query performance and manage storage costs, Airflow schedules regular Iceberg maintenance tasks:

- **Metrics-Driven Compaction:** Rewrites small data files into optimal size chunks only when thresholds are breached.
- **Snapshot Expiration:** Expires snapshots older than the required backfill window, ensuring active ML jobs are not disrupted.
- **Orphan Cleanup:** Removes unreferenced data files after a safety window.
- **Logical Invariants:** Compaction and maintenance operations must strictly preserve logical row counts and checksums.

---

## 5. Security and Access Control

- **Service Isolation:** Extractors use read-only MySQL accounts scoped strictly to the 16 allowed analytical tables.
- **Engine Roles:** Spark uses a dedicated `spark_writer` principal (`CATALOG_MANAGE_CONTENT`). Trino uses a read-only `trino_reader` principal (`CATALOG_READ_DATA`).
- **PII Protection:** Passwords, tokens, cookies, and raw IP addresses are stripped before ingestion. Customer PII is pseudonymized before entering Silver and Gold layers.
- **Credential Isolation:** MinIO and Polaris credentials are injected via runtime environment variables and Docker secrets.
