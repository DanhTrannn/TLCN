# Lakehouse Batch Pipelines

The `batch-pipeline` package encapsulates Apache Spark batch processing jobs, Iceberg Medallion table definitions, incremental MySQL extraction logic, and Airflow DAG integration helpers for the D&K Data Lakehouse.

---

## 1. Directory Structure

```text
pipelines/
├── config/
│   └── default.yml                       # Lakehouse table specifications, cursor mappings, and mutability
├── src/
│   ├── jobs/                             # Data pipeline execution jobs (Streaming & Batch)
│   │   ├── logs/                         # Access Logs streaming & analytical jobs
│   │   │   ├── kafka_to_lakehouse.py     # Pure Streaming: Kafka -> Medallion (Landing, Bronze, Silver, Gold)
│   │   │   └── build_logs_gold.py        # Builds Gold Data Marts from real-time fact_web_events
│   │   ├── maintenance/                  # Lakehouse Iceberg maintenance
│   │   │   └── iceberg_table_maintenance.py # Compaction (rewrite_data_files), snapshot expiration, orphan cleanup
│   │   └── oltp/                         # MySQL OLTP ingestion jobs
│   │       ├── extract_oltp.py           # Extracts MySQL OLTP tables to MinIO Landing Zone
│   │       ├── ingest_bronze.py          # Ingests Landing OLTP Parquet files into Iceberg Bronze tables
│   │       ├── ingest_oltp_to_bronze.py  # Auto-discovers Landing run_id and ingests to Bronze
│   │       └── ingest_oltp_silver.py     # Ingests OLTP Bronze to Silver via MERGE
│   └── lakehouse/                        # Core Python library
│       ├── flink.py                      # Flink environment & Polaris REST catalog factory
│       ├── spark.py                      # SparkSession factory with S3A and Polaris OAuth2 authentication
│       ├── config.py                     # Pipeline configuration loader and validation
│       ├── landing.py                    # Landing Zone paths builder and MD5 manifest serialization
│       ├── validate.py                   # S3 object validation and manifest verification
│       ├── logs/                         # Access Logs domain logic
│       │   ├── bronze.py                 # OpenTelemetry log schema and Bronze DDLs
│       │   ├── silver.py                 # Logs Silver: struct flattening, schema DDLs
│       │   └── gold.py                   # Logs Gold: Fact web events & Marts (hourly route metrics, daily product demand)
│       └── oltp/                         # MySQL OLTP domain logic
│           ├── extract.py                # Multi-threaded MySQL JDBC extraction engine
│           ├── bronze.py                 # OLTP Bronze schema definitions, DDLs, and transformation
│           ├── silver.py                 # OLTP Silver: MERGE core, dedup, PII, quarantine
│           ├── silver_ddl.py             # Silver table DDL definitions (16 OLTP + quarantine)
│           ├── cursor.py                 # Composite cursor JSON state serialization and S3 helpers
│           └── query.py                  # Extraction window SQL predicate generator
└── tests/                                # Unit test suite
    ├── test_bronze.py                    # Tests OLTP Bronze ingestion logic and dead-letter quarantine
    ├── test_config.py                    # Tests configuration parsing and validation
    ├── test_cursor.py                    # Tests cursor state management and S3 state round-trips
    ├── test_ingest_oltp_to_bronze.py     # Tests Landing path builders and auto-discovery
    ├── test_landing.py                   # Tests Landing path builders and manifest serialization
    ├── test_logs_bronze.py               # Tests OpenTelemetry log schema and Bronze transformations
    ├── test_logs_silver.py               # Tests Logs Silver dedup and struct flattening
    ├── test_logs_gold.py                 # Tests Logs Gold Fact and Data Mart transformations
    ├── test_query.py                     # Tests extraction window SQL predicate generation
    ├── test_silver.py                    # Tests OLTP Silver MERGE, PII, quarantine, integration
    └── test_validate.py                  # Tests S3 manifest verification logic
```

---

## 2. Ingestion Pipelines

### 2.1. Pure Streaming Medallion Logs Pipeline & Maintenance
- **Streaming Ingestion (PyFlink):** Continuous real-time ingestion from Kafka `ecommerce.access_logs` directly into all 4 layers (`landing.access_logs`, `bronze.web_events`, `silver.silver_logs`, `gold.fact_web_events`) via Flink `StatementSet` every 10-second checkpoint with Merge-on-Read write mode.
- **Maintenance & Data Marts DAG (`lakehouse_streaming_maintenance`):**
  - **Schedule:** Every 2 hours (`0 */2 * * *`).
  - **Tasks:**
    1. `stream_monitoring`: Healthcheck Flink JobManager REST API verifying continuous `RUNNING` stream status.
    2. `iceberg_maintenance`: Spark-based Iceberg compaction (`rewrite_data_files`, `rewrite_manifests`), snapshot expiration (`expire_snapshots`), and orphan file purge (`remove_orphan_files`).
    3. `gold_marts`: Periodic rollup of `mart_hourly_route_metrics` and `mart_daily_product_demand` from real-time `fact_web_events`.

### 2.2. OLTP Ingestion Pipelines
- **Unified OLTP Pipeline (`lakehouse_oltp_pipeline`):** End-to-end daily batch ingestion of 26 OLTP tables across all Medallion layers:
  1. **Landing Zone:** Incremental extraction via composite cursors `(cursor_field, pk)` with MD5 cryptographic manifests.
  2. **Bronze Layer:** Append-only ingestion into Iceberg Bronze tables.
  3. **Silver Layer:** Deduplication, PII pseudonymization (SHA-256), business rule validation, quarantine routing, and ACID MERGE into Silver tables.
  4. **Gold Layer:** Star Schema Dimensions, Facts, and Data Marts with financial COGS and KPI rollups.
- **Documentation:** [`docs/pipelines/batch/INGEST_OLTP_TO_LANDING.md`](../docs/pipelines/batch/INGEST_OLTP_TO_LANDING.md) & [`docs/pipelines/batch/INGEST_OLTP_BRONZE_TO_SILVER.md`](../docs/pipelines/batch/INGEST_OLTP_BRONZE_TO_SILVER.md).

---

## 3. Pipeline Status

### Completed

| DAG / Job | Schedule | Source → Target | Architecture | Notes |
|---|---|---|---|---|
| `lakehouse_oltp_pipeline` | Daily 2 AM | MySQL → Landing → Bronze → Silver → Gold | **Unified Batch DAG** | Composite cursors (26 tables), MD5 manifests, PII, MERGE, COGS Marts |
| `kafka_to_lakehouse_pure_streaming` | Continuous (10s checkpoints) | Kafka → Landing, Bronze, Silver, Gold | **Pure Streaming (PyFlink)** | StatementSet, Pendulum VN timezone, Merge-on-Read |
| `lakehouse_streaming_maintenance` | 2 hours | Iceberg Tables & Gold Marts | **Maintenance DAG** | Flink Healthcheck, Compaction, Expiry, Marts Rollup |
| `build_oltp_gold` | Daily 2 AM | Silver → Gold (`dim_*`, `fact_*`, `mart_*`) | **Gold Batch Transformation** | Star schema, financial COGS parity, gross profit rollups |

### Validation Results

```text
OLTP extraction (MySQL → Landing):        Pass  (26 analytical tables, Parquet + manifests)
Landing → Bronze ingestion:               Pass  (26 tables, 0 skipped, 0 quarantine)
Bronze table counts (Trino):              Pass  (verified via Trino & Polaris catalog)
Access logs → Bronze:                     Pass  (web_events table)
OLTP Bronze → Silver:                     Pass  (26 tables, MERGE, PII, quarantine)
Logs Bronze → Silver:                     Pass  (web_events, anti-join dedup)
Silver → Gold Marts:                      Pass  (sales marts, inventory health, COGS)
```

---

## 4. Running Pipeline Tests

Run the pipeline unit and financial parity test suite (106 tests):

```bash
uv run pytest pipelines/tests
```
