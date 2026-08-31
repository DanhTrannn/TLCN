# Lakehouse Batch Pipelines

The `batch-pipeline` package encapsulates Apache Spark batch processing jobs, Iceberg Medallion table definitions, incremental MySQL extraction logic, and Airflow DAG integration helpers for the D&K Data Lakehouse.

---

## 1. Directory Structure

```text
pipelines/
├── config/
│   └── default.yml                       # Lakehouse table specifications, cursor mappings, and mutability
├── src/
│   ├── jobs/                             # Standalone Spark batch jobs submitted via Airflow
│   │   ├── logs/                         # Access Logs ingestion & analytical jobs
│   │   │   ├── ingest_logs_to_bronze.py  # Ingests micro-batch Access Logs into Iceberg Bronze
│   │   │   ├── ingest_logs_silver.py     # Ingests Logs Bronze to Silver with anti-join dedup
│   │   │   └── build_logs_gold.py        # Builds Gold Fact and Data Marts from Silver logs
│   │   └── oltp/                         # MySQL OLTP ingestion jobs
│   │       ├── extract_oltp.py           # Extracts MySQL OLTP tables to MinIO Landing Zone
│   │       ├── ingest_bronze.py          # Ingests Landing OLTP Parquet files into Iceberg Bronze tables
│   │       ├── ingest_oltp_to_bronze.py  # Auto-discovers Landing run_id and ingests to Bronze
│   │       └── ingest_oltp_silver.py     # Ingests OLTP Bronze to Silver via MERGE
│   └── lakehouse/                        # Core Python library
│       ├── config.py                     # Pipeline configuration loader and validation
│       ├── landing.py                    # Landing Zone paths builder and MD5 manifest serialization
│       ├── spark.py                      # SparkSession factory with S3A and Polaris OAuth2 authentication
│       ├── validate.py                   # S3 object validation and manifest verification
│       ├── logs/                         # Access Logs domain logic
│       │   ├── bronze.py                 # OpenTelemetry log schema, DDLs, and partition-pruned anti-join
│       │   ├── silver.py                 # Logs Silver: anti-join dedup, struct flattening, metadata
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

### 2.1. Unified Master Access Logs Pipeline (`lakehouse_logs_pipeline` DAG)
- **Schedule:** Every 2 hours (`0 */2 * * *`).
- **Architecture:** Unified End-to-End DAG with 4 visual `TaskGroup` layers:
  1. `staging_layer`: `check_minio_landing` → `discover_landing_logs` (probes Landing S3 bucket and discovers log batches).
  2. `bronze_layer`: `ingest_logs_to_bronze` (parses OpenTelemetry JSON, anti-join via partition pruning, appends to `web_events`).
  3. `silver_layer`: `ingest_logs_to_silver` (window deduplication by `event_id`, flattens nested structs, appends to `silver_logs`).
  4. `gold_layer`: `build_logs_gold` (builds `fact_web_events`, `mart_hourly_route_metrics`, and `mart_daily_product_demand`).
- **Documentation:** [`docs/pipelines/batch/INGEST_LOGS_LANDING_TO_BRONZE.md`](../docs/pipelines/batch/INGEST_LOGS_LANDING_TO_BRONZE.md).

### 2.2. OLTP Ingestion Pipelines
- **Extraction to Landing (`ingest_oltp_batch`):** Hourly incremental extraction of 16 tables via composite cursors.
- **Landing to Bronze (`ingest_oltp_landing_to_bronze`):** Daily 2 AM auto-discovery of Landing files and ingestion into Iceberg Bronze tables.
- **Bronze to Silver (`ingest_oltp_silver`):** Daily 2 AM deduplication, PII pseudonymization, business rule validation, quarantine routing, and ACID MERGE into Silver tables.
- **Documentation:** [`docs/pipelines/batch/INGEST_OLTP_TO_LANDING.md`](../docs/pipelines/batch/INGEST_OLTP_TO_LANDING.md) & [`docs/pipelines/batch/INGEST_OLTP_BRONZE_TO_SILVER.md`](../docs/pipelines/batch/INGEST_OLTP_BRONZE_TO_SILVER.md).

---

## 3. Pipeline Status

### Completed

| DAG | Schedule | Source → Target | Architecture | Notes |
|---|---|---|---|---|
| `lakehouse_logs_pipeline` | 2 hours | MinIO Landing → Bronze → Silver → Gold | **Master Unified DAG** | 4 TaskGroups (`staging`, `bronze`, `silver`, `gold`) |
| `ingest_oltp_batch` | Hourly | MySQL → Landing | Modular DAG | Composite cursors, MD5 manifests |
| `ingest_oltp_landing_to_bronze` | Daily 2 AM | Landing → Bronze | Modular DAG | Auto-discover `run_id` from Landing |
| `ingest_oltp_silver` | Daily 2 AM | Bronze → Silver | Modular DAG | MERGE, PII pseudonymization, quarantine |

### Pending

| DAG | Schedule | Source → Target | Notes |
|---|---|---|---|
| Silver → Gold Tasks | - | Silver → Gold | Star schema (`dim_*`, `fact_*`), analytical marts |
| Iceberg maintenance | - | - | Compaction, snapshot expiration, orphan cleanup |

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
