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
│   │   ├── extract_oltp.py               # Extracts MySQL OLTP tables to MinIO Landing Zone
│   │   ├── ingest_bronze.py              # Ingests Landing OLTP Parquet files into Iceberg Bronze tables
│   │   ├── ingest_logs_to_bronze.py      # Ingests 15-minute micro-batch Access Logs into Iceberg Bronze
│   │   └── jdbc_probe.py                 # Health and connectivity probe for MySQL JDBC
│   └── lakehouse/                        # Core Python library
│       ├── bronze.py                     # OLTP Bronze schema definitions, DDLs, and transformation
│       ├── config.py                     # Pipeline configuration loader and validation
│       ├── cursor.py                     # Composite cursor JSON state serialization and S3 helpers
│       ├── extract.py                    # Multi-threaded MySQL JDBC extraction engine
│       ├── landing.py                    # Landing Zone paths builder and MD5 manifest serialization
│       ├── logs_bronze.py                # OpenTelemetry log schema, DDLs, and partition-pruned anti-join
│       ├── query.py                      # Extraction window SQL predicate generator
│       ├── spark.py                      # SparkSession factory with S3A and Polaris OAuth2 authentication
│       └── validate.py                   # S3 object validation and manifest verification
└── tests/                                # Unit test suite (46 tests total)
    ├── test_bronze.py                    # Tests OLTP Bronze ingestion logic and dead-letter quarantine
    ├── test_config.py                    # Tests configuration parsing and validation
    ├── test_cursor.py                    # Tests cursor state management and S3 state round-trips
    ├── test_landing.py                   # Tests Landing path builders and manifest serialization
    ├── test_logs_bronze.py               # Tests OpenTelemetry log schema and Bronze transformations
    ├── test_query.py                     # Tests extraction window SQL predicate generation
    └── test_validate.py                  # Tests S3 manifest verification logic
```

---

## 2. Ingestion Pipelines

### 2.1. OLTP Incremental Ingestion (`ingest_oltp_batch` DAG)
- **Schedule:** Hourly (`0 * * * *`).
- **Flow:** Extracts 16 allowed operational tables using composite cursors `(cursor_field, pk)`.
- **Landing Format:** Immutable Parquet files with cryptographic `manifest.json`.
- **Documentation:** [`docs/pipelines/batch/INGEST_OLTP_TO_LANDING.md`](../docs/pipelines/batch/INGEST_OLTP_TO_LANDING.md).

### 2.2. Web Access Logs Ingestion (`ingest_logs_15m_to_bronze` DAG)
- **Schedule:** Every 15 minutes (`*/15 * * * *`).
- **Flow:** Discovers new rotated gzip JSON log batches, performs high-performance anti-join via partition pruning, appends records to `lakehouse.bronze.web_events`, and routes corrupt records to `lakehouse.quarantine.bronze_corrupt_logs`.
- **Documentation:** [`docs/pipelines/batch/INGEST_LOGS_LANDING_TO_BRONZE.md`](../docs/pipelines/batch/INGEST_LOGS_LANDING_TO_BRONZE.md).

---

## 3. Running Pipeline Tests

```bash
# Run pipeline unit tests
PYTHONPATH=pipelines/src uv run --locked --package batch-pipeline --extra dev -- pytest pipelines/tests
```
