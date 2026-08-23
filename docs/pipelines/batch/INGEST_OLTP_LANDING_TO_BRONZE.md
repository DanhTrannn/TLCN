# Ingest OLTP Landing to Bronze

This document describes the Spark batch job and Airflow DAG for ingesting OLTP data from the MinIO Landing Zone into Iceberg Bronze tables.

## Overview

After the `ingest_oltp_batch` DAG extracts OLTP data from MySQL to the Landing Zone, this pipeline reads the Parquet files and commits them to the corresponding Bronze Iceberg tables with lineage metadata.

```text
MinIO Landing Zone
s3://lakehouse/landing/oltp/<table>/extract_date=YYYY-MM-DD/run_id=<run_id>/data/*.parquet
        │
        ▼
Spark Batch Job (ingest_oltp_to_bronze)
        │
        ├─ Read Parquet files (PERMISSIVE mode)
        ├─ Add lineage columns (_run_id, _source_file, _ingested_at_utc)
        ├─ Circuit breaker (1% error threshold)
        ├─ Route corrupt records to quarantine
        │
        ▼
Iceberg Bronze Tables
lakehouse.bronze.<table_name>
```

## Airflow DAG

**DAG ID:** `ingest_oltp_landing_to_bronze`

**Schedule:** Daily at 2:00 AM UTC (`0 2 * * *`)

**Tasks:**
1. `begin_run` — Generate unique `run_id` and `extract_date`
2. `ingest_oltp_to_bronze` — Submit Spark job to ingest all 16 OLTP tables

**Trigger:** Manual or scheduled (daily 2 AM UTC)

## Spark Job

**Application:** `/opt/project/pipelines/src/jobs/ingest_oltp_to_bronze.py`

**Arguments:**
| Argument | Required | Description |
|----------|----------|-------------|
| `--run-id` | Yes | Airflow DAG run ID (UUID) |
| `--extract-date` | Yes | Extract date (YYYY-MM-DD) |
| `--tables` | No | Specific tables to ingest (default: all 16) |
| `--bucket` | No | MinIO S3 bucket (default: `lakehouse`) |
| `--error-threshold` | No | Max corrupt record fraction (default: 0.01) |

**Behavior:**
- Iterates over all 16 OLTP tables from `config/default.yml`
- For each table, constructs the Landing path and calls `ingest_to_bronze()`
- Skips tables not found in config with a warning
- Re-raises exceptions on ingestion failure (Airflow detects the error)

## Landing Path Pattern

```text
s3a://{bucket}/landing/oltp/{table}/extract_date={YYYY-MM-DD}/run_id={run_id}/data/*.parquet
```

Example:
```text
s3a://lakehouse/landing/oltp/orders/extract_date=2026-08-23/run_id=abc123/data/*.parquet
```

## Bronze Table Pattern

```text
lakehouse.bronze.{table_name}
```

Example: `lakehouse.bronze.orders`, `lakehouse.bronze.customers`

## Quarantine Table Pattern

```text
lakehouse.quarantine.{table_name}_errors
```

Example: `lakehouse.quarantine.orders_errors`

## Lineage Metadata

Every record in Bronze tables includes three lineage columns:

| Column | Description |
|--------|-------------|
| `_run_id` | Airflow DAG Run ID (UUID) for idempotent reruns |
| `_source_file` | Absolute S3 URI of the source Parquet file |
| `_ingested_at_utc` | UTC timestamp when record was committed to Bronze |

## Error Handling

- **Circuit Breaker:** If corrupt records exceed 1% threshold, the job raises `RuntimeError` and fails fast
- **Quarantine:** Corrupt records below threshold are routed to per-table quarantine tables
- **Idempotent Reruns:** Unique `run_id` per execution prevents duplicate processing

## OLTP Tables (16 total)

| Table | Cursor Field | Mutability |
|-------|--------------|------------|
| `customers` | `updated_at` | mutable |
| `categories` | `updated_at` | mutable |
| `products` | `updated_at` | mutable |
| `product_variants` | `updated_at` | mutable |
| `carts` | `updated_at` | mutable |
| `cart_items` | `updated_at` | mutable |
| `wishlist_items` | `updated_at` | mutable |
| `orders` | `updated_at` | mutable |
| `order_items` | `created_at` | append_only |
| `payments` | `created_at` | append_only |
| `order_status_history` | `created_at` | append_only |
| `inventory` | `updated_at` | mutable |
| `coupons` | `updated_at` | mutable |
| `coupon_redemptions` | `updated_at` | mutable |
| `refunds` | `created_at` | append_only |
| `product_reviews` | `updated_at` | mutable |

## Verification

### Check DAG Status

```bash
# List DAGs
docker compose exec airflow-webserver airflow dags list | grep ingest_oltp_landing_to_bronze

# Check DAG run history
docker compose exec airflow-webserver airflow dags list-runs -d ingest_oltp_landing_to_bronze
```

### Query Bronze Tables

```sql
-- List all Bronze tables
SHOW TABLES FROM lakehouse.bronze;

-- Check row counts
SELECT 'orders' AS tbl, COUNT(*) AS cnt FROM lakehouse.bronze.orders
UNION ALL SELECT 'customers', COUNT(*) FROM lakehouse.bronze.customers;

-- Check lineage metadata
SELECT _run_id, COUNT(*) AS cnt
FROM lakehouse.bronze.orders
GROUP BY _run_id;
```

### Check Quarantine

```sql
SHOW TABLES FROM lakehouse.quarantine;
SELECT COUNT(*) FROM lakehouse.quarantine.orders_errors;
```

## Manual Trigger

```bash
# Via Airflow CLI
docker compose exec airflow-webserver airflow dags trigger ingest_oltp_landing_to_bronze

# Via Airflow UI
# Navigate to http://localhost:8080 → DAGs → ingest_oltp_landing_to_bronze → Trigger DAG
```

## Dependencies

- `ingest_oltp_batch` DAG must have run first (extracts data to Landing)
- Polaris catalog must be initialized
- Spark cluster must be running
- MinIO must be healthy
