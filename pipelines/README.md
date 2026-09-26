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
- **Extraction to Landing (`ingest_oltp_batch`):** Hourly incremental extraction of 16 tables via composite cursors.
- **Landing to Bronze (`ingest_oltp_landing_to_bronze`):** Daily 2 AM auto-discovery of Landing files and ingestion into Iceberg Bronze tables.
- **Bronze to Silver (`ingest_oltp_silver`):** Daily 2 AM deduplication, PII pseudonymization, business rule validation, quarantine routing, and ACID MERGE into Silver tables.
- **Documentation:** [`docs/pipelines/batch/INGEST_OLTP_TO_LANDING.md`](../docs/pipelines/batch/INGEST_OLTP_TO_LANDING.md) & [`docs/pipelines/batch/INGEST_OLTP_BRONZE_TO_SILVER.md`](../docs/pipelines/batch/INGEST_OLTP_BRONZE_TO_SILVER.md).

---

## 3. Pipeline Status

### Completed

| DAG / Job | Schedule | Source → Target | Architecture | Notes |
|---|---|---|---|---|
| `kafka_to_lakehouse_pure_streaming` | Continuous (10s checkpoints) | Kafka → Landing, Bronze, Silver, Gold | **Pure Streaming (PyFlink)** | StatementSet, Pendulum VN timezone, Merge-on-Read |
| `lakehouse_streaming_maintenance` | 2 hours | Iceberg Tables & Gold Marts | **Maintenance DAG** | Flink Healthcheck, Compaction, Expiry, Marts Rollup |
| `ingest_oltp_batch` | Hourly | MySQL → Landing | Modular DAG | Composite cursors, MD5 manifests |
| `ingest_oltp_landing_to_bronze` | Daily 2 AM | Landing → Bronze | Modular DAG | Auto-discover `run_id` from Landing |
| `ingest_oltp_silver` | Daily 2 AM | Bronze → Silver | Modular DAG | MERGE, PII pseudonymization, quarantine |

### Pending

| Pipeline | Schedule | Source → Target | Notes |
|---|---|---|---|
| Silver → Gold Tasks | - | Silver → Gold | Star schema (`dim_*`, `fact_*`), analytical marts |

### Validation Results

```
OLTP extraction (MySQL → Landing):        Pass  (16 tables, Parquet + manifests)
Landing → Bronze ingestion:               Pass  (16 tables, 0 skipped, 0 quarantine)
Bronze table counts (Trino):              Pass  (e.g. orders: 12,000, customers: 2,008)
Access logs → Bronze:                     Pass  (web_events table)
OLTP Bronze → Silver:                     Pass  (16 tables, MERGE, PII, quarantine)
Logs Bronze → Silver:                     Pass  (web_events, anti-join dedup)
```

---

## 4. Running Pipeline Tests

```bash
# Run pipeline unit tests
PYTHONPATH=pipelines/src uv run --locked --package batch-pipeline --extra dev -- pytest pipelines/tests
```
