# Batch Pipeline: Access Logs Landing to Bronze (`web_events`)

This document specifies the architectural design, table schema, 15-minute incremental extraction mechanics, idempotency guarantees, Spark processing logic, and Airflow orchestration for ingesting structured HTTP access logs from the MinIO S3 Landing Zone into the Apache Iceberg Bronze layer table (`lakehouse.bronze.web_events`).

---

## 1. Architectural Overview and Data Flow

The Access Log ingestion pipeline runs as a **15-minute scheduled micro-batch ETL job** synchronized with Fluent Bit's log rotation window. To scale to millions of historical files without encountering S3 `ListObjects` performance bottlenecks, the pipeline uses **Time-Window Scoped Ingestion** combined with **Hour-Scoped Metadata Anti-Join**.

```text
MinIO S3 Landing Zone
s3://lakehouse/landing/logs/ingest_date=YYYY-MM-DD/ingest_hour=HH/service=ecommerce-api/*.jsonl.gz
                                │
                                ▼
         Apache Spark 15-Minute Job (ingest_logs_to_bronze.py)
         ├── 1. Scoped Path Discovery: Only list current hour partition (1 to 4 files, <10ms)
         ├── 2. Hour-Scoped Anti-Join: Filter out files already committed to Bronze today
         ├── 3. Parse JSON with explicit OpenTelemetry schema mapping
         ├── 4. Route corrupt / malformed JSON records to Quarantine table
         ├── 5. Attach Lineage Metadata (_run_id, _source_system, _source_file, _ingested_at)
         └── 6. Atomic Commit to Iceberg Bronze table via Polaris REST Catalog
                                │
                 ┌──────────────┴──────────────┐
                 ▼                             ▼
   lakehouse.bronze.web_events    lakehouse.quarantine.bronze_corrupt_logs
   (Valid Nested Iceberg Table)   (Corrupt / Malformed JSON payloads)
                 │
                 ▼
          Trino Query Engine (Port 8084) / Downstream Silver Pipeline
```

---

## 2. Source Contract and Landing Layout

### 2.1. Landing Zone Storage Layout
All access log micro-batches follow Hive-style UTC date/hour directory partitioning:

```text
landing/logs/ingest_date=YYYY-MM-DD/ingest_hour=HH/service=ecommerce-api/<uuid>.jsonl.gz
```

- **Rotation Interval:** 15 minutes (or 128 MiB uncompressed buffer) via Fluent Bit.
- **Format:** Gzip-compressed newline-delimited JSON (`.jsonl.gz`).
- **Contract Schema:** Standardized to OpenTelemetry HTTP server conventions defined in [`docs/contracts/ecommerce-access-v1.schema.json`](../../contracts/ecommerce-access-v1.schema.json).
- **Immutability:** Landing files are strictly immutable once written.

---

## 3. Bronze Table Schema Specification

The `lakehouse.bronze.web_events` table preserves all fields from the source telemetry contract in columnar Iceberg Nested Structs while attaching technical lineage metadata.

### 3.1. Iceberg DDL Specification

```sql
CREATE NAMESPACE IF NOT EXISTS lakehouse.bronze;

CREATE TABLE IF NOT EXISTS lakehouse.bronze.web_events (
    -- 1. Identity and Timestamps
    event_id            STRING                          COMMENT 'Unique event identifier mapped from request.id (UUIDv7 hex)',
    event_ts            TIMESTAMP                       COMMENT 'Event generation timestamp in UTC',
    observed_timestamp  TIMESTAMP                       COMMENT 'Timestamp when the event was recorded by runtime container',

    -- 2. OpenTelemetry Metadata
    schema              STRUCT<
                            name: STRING,
                            version: STRING
                        >                               COMMENT 'Schema contract identifier and version',
    service             STRUCT<
                            name: STRING,
                            version: STRING,
                            environment: STRING,
                            instance_id: STRING
                        >                               COMMENT 'Service metadata (ecommerce-api)',
    severity_number     INT                             COMMENT 'OpenTelemetry severity code: 9 (INFO), 13 (WARN), 17 (ERROR)',
    severity_text       STRING                          COMMENT 'Severity text level: INFO, WARN, ERROR',
    trace_id            STRING                          COMMENT 'Distributed tracing Trace ID (nullable)',
    span_id             STRING                          COMMENT 'Distributed tracing Span ID (nullable)',

    -- 3. HTTP Server and Request Payload
    event               STRUCT<
                            name: STRING,
                            category: STRING,
                            kind: STRING,
                            outcome: STRING,
                            duration_ns: BIGINT
                        >                               COMMENT 'HTTP request execution duration and outcome',
    http                STRUCT<
                            request_method: STRING,
                            route: STRING,
                            status_code: INT
                        >                               COMMENT 'HTTP protocol attributes (method, parameterized route, status)',
    request             STRUCT<
                            id: STRING
                        >                               COMMENT 'Request identification container',

    -- 4. Actor, Client, and E-Commerce Domain
    actor               STRUCT<
                            type: STRING,               -- anonymous, customer, admin, system
                            key: STRING                 -- Raw actor identifier or customer ID
                        >                               COMMENT 'Actor initiator information',
    client              STRUCT<
                            user_agent: STRING
                        >                               COMMENT 'Client user agent string',
    ecommerce           STRUCT<
                            action: STRING,             -- product_detail, cart_add, checkout_submit, search, ...
                            product_key: STRING,
                            variant_key: STRING,
                            search_query: STRING,
                            search_redacted: BOOLEAN,
                            filters: MAP<STRING, STRING>
                        >                               COMMENT 'E-commerce transactional context and search filters',
    error               STRUCT<
                            code: STRING,
                            type: STRING
                        >                               COMMENT 'Application error code and exception type (if failed)',
    data_origin         STRING                          COMMENT 'Telemetry origin: observed, synthetic',

    -- 5. Technical Lineage Metadata
    _run_id             STRING                          COMMENT 'Airflow/Spark batch execution run ID',
    _source_system      STRING                          COMMENT 'Source system identifier (ecommerce-api-access-log)',
    _source_file        STRING                          COMMENT 'Full S3 URI of the source .jsonl.gz file',
    _ingested_at        TIMESTAMP                       COMMENT 'UTC timestamp when Spark committed record to Bronze'
)
USING iceberg
PARTITIONED BY (days(event_ts))
LOCATION 's3://lakehouse/warehouse/bronze/web_events'
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
);
```

### 3.2. Column Reference Table

| Category | Column | Iceberg Type | Nullable | Description |
|---|---|---|---|---|
| **Identity** | `event_id` | `STRING` | No | Primary request identifier (`request.id`). |
| **Timestamps** | `event_ts` | `TIMESTAMP` | No | Request completion timestamp in UTC. |
| | `observed_timestamp` | `TIMESTAMP` | No | Container logger recording timestamp. |
| **Telemetry** | `schema` | `STRUCT` | No | `{name: string, version: string}`. |
| | `service` | `STRUCT` | No | `{name, version, environment, instance_id}`. |
| | `severity_number` | `INT` | No | OTel severity number (9, 13, 17). |
| | `severity_text` | `STRING` | No | Severity level string (`INFO`, `WARN`, `ERROR`). |
| | `trace_id` | `STRING` | Yes | 32-character hexadecimal trace identifier. |
| | `span_id` | `STRING` | Yes | 16-character hexadecimal span identifier. |
| **HTTP** | `event` | `STRUCT` | No | `{name, category, kind, outcome, duration_ns}`. |
| | `http` | `STRUCT` | No | `{request_method, route, status_code}`. |
| | `request` | `STRUCT` | No | `{id: string}`. |
| **Domain** | `actor` | `STRUCT` | No | `{type: string, key: string}`. |
| | `client` | `STRUCT` | Yes | `{user_agent: string}`. |
| | `ecommerce` | `STRUCT` | No | `{action, product_key, variant_key, search_query, search_redacted, filters}`. |
| | `error` | `STRUCT` | Yes | `{code: string, type: string}`. |
| | `data_origin` | `STRING` | No | `observed` (production) or `synthetic` (backfill). |
| **Lineage** | `_run_id` | `STRING` | No | Batch execution run identifier. |
| | `_source_system` | `STRING` | No | Fixed value: `ecommerce-api-access-log`. |
| | `_source_file` | `STRING` | No | Source `.jsonl.gz` S3 URI. |
| | `_ingested_at` | `TIMESTAMP` | No | Ingestion completion timestamp in UTC. |

---

### 3.3. Bronze Quarantine Table Specification (`lakehouse.quarantine.bronze_corrupt_logs`)

Records with invalid JSON syntax, unparseable lines, or missing mandatory identity boundaries are automatically routed to the quarantine table for root-cause analysis (RCA) and audit isolation without failing the main batch pipeline.

#### Iceberg DDL Specification

```sql
CREATE NAMESPACE IF NOT EXISTS lakehouse.quarantine;

CREATE TABLE IF NOT EXISTS lakehouse.quarantine.bronze_corrupt_logs (
    raw_corrupt_record    STRING                          COMMENT 'Raw unparseable line or malformed JSON text from source file',
    error_message         STRING                          COMMENT 'Error description or parser diagnostic message',
    quarantine_stage      STRING                          COMMENT 'Pipeline phase where anomaly was detected (bronze_landing_ingestion)',
    _run_id               STRING                          COMMENT 'Airflow/Spark batch execution run ID',
    _source_system        STRING                          COMMENT 'Source system identifier (ecommerce-api-access-log)',
    _source_file          STRING                          COMMENT 'Source .jsonl.gz S3 URI containing the corrupt line',
    _quarantined_at       TIMESTAMP                       COMMENT 'UTC timestamp when record was routed to quarantine'
)
USING iceberg
PARTITIONED BY (days(_quarantined_at))
LOCATION 's3://lakehouse/warehouse/quarantine/bronze_corrupt_logs'
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
);
```

#### Quarantine Column Reference Table

| Column | Iceberg Type | Nullable | Description |
|---|---|---|---|
| `raw_corrupt_record` | `STRING` | No | Verbatim raw string payload that failed JSON parsing. |
| `error_message` | `STRING` | No | Diagnostic reason (e.g. `Malformed JSON syntax`, `Schema validation error`). |
| `quarantine_stage` | `STRING` | No | Pipeline isolation stage (`bronze_landing_ingestion`). |
| `_run_id` | `STRING` | No | Batch run execution UUID. |
| `_source_system` | `STRING` | No | Fixed value: `ecommerce-api-access-log`. |
| `_source_file` | `STRING` | No | Full S3 URI of the originating `.jsonl.gz` file. |
| `_quarantined_at` | `TIMESTAMP` | No | UTC timestamp when record was committed to quarantine. |

---

## 4. 15-Minute Incremental & Idempotency Architecture

### 4.1. The High-Scale Listing Challenge
In large-scale production, querying `ListObjects` on an entire Landing Zone with millions of files creates severe I/O latency and network overhead. 

To solve this, the pipeline scopes every run to **a single hour folder** and filters out already-processed files within that hour:

```text
At 10:15 UTC: Folder has [file_10_15]           --> Ingests file_10_15
At 10:30 UTC: Folder has [file_10_15, file_10_30] --> Ingests only file_10_30
At 10:45 UTC: Folder has [file_10_15, file_10_30, file_10_45] --> Ingests only file_10_45
At 11:00 UTC: Folder has [file_10_15, file_10_30, file_10_45, file_11_00] --> Ingests only file_11_00
```

### 4.2. Partition Pruning + Column Pruning Anti-Join Optimization
1. **Target Directory Scoping:** Airflow supplies `ingest_date` (e.g. `2026-08-22`) and `ingest_hour` (e.g. `10`). Spark scans strictly `landing/logs/ingest_date=2026-08-22/ingest_hour=10/service=ecommerce-api/*.jsonl.gz` ($O(1)$ file count, $\le 4$ files).
2. **Metadata Anti-Join via Partition & Column Pruning:**
   Spark queries the Bronze Iceberg table to retrieve the set of already-ingested Landing files for the target window:
   ```sql
   SELECT DISTINCT _source_file 
   FROM lakehouse.bronze.web_events 
   WHERE event_ts >= TIMESTAMP '2026-08-22 00:00:00'
     AND event_ts <= TIMESTAMP '2026-08-22 23:59:59';
   ```
   * **Partition Pruning:** Iceberg's `PARTITIONED BY (days(event_ts))` skips all historical day partitions on S3 and reads only the metadata and data files for the target date.
   * **Column Pruning:** Parquet columnar format reads exclusively the single dictionary-encoded `_source_file` column, bypassing all nested structs (`http`, `ecommerce`, `event`, etc.).
   * **Execution Latency:** Execution completes in **~50–100 milliseconds**.

3. **Difference Filter:** Spark filters the input DataFrame:
   $$\text{New Files} = \{ f \in \text{Hour Landing Files} \mid f \notin \text{Committed Files} \}$$
4. **Zero-Cost No-Op:** If no new files exist (e.g., all 4 files were already ingested or traffic is idle), the job terminates immediately without performing costly commits.
5. **Replay Mode (`--replay-date YYYY-MM-DD`):** If a historical date is re-run, Spark switches from `.append()` to `.overwrite(col("event_ts").cast("date") == lit(replay_date))` for atomic partition replacement.

---

## 5. Spark Implementation

### 5.1. OpenTelemetry Schema Definition
```python
from pyspark.sql.types import (
    BooleanType, IntegerType, LongType, MapType,
    StringType, StructField, StructType, TimestampType
)

OTEL_LOG_SCHEMA = StructType([
    StructField("schema", StructType([
        StructField("name", StringType(), False),
        StructField("version", StringType(), False),
    ]), False),
    StructField("timestamp", StringType(), False),
    StructField("observed_timestamp", StringType(), False),
    StructField("severity_text", StringType(), False),
    StructField("severity_number", IntegerType(), False),
    StructField("request", StructType([
        StructField("id", StringType(), False),
    ]), False),
    StructField("trace_id", StringType(), True),
    StructField("span_id", StringType(), True),
    StructField("service", StructType([
        StructField("name", StringType(), False),
        StructField("version", StringType(), False),
        StructField("environment", StringType(), False),
        StructField("instance_id", StringType(), False),
    ]), False),
    StructField("event", StructType([
        StructField("name", StringType(), False),
        StructField("category", StringType(), False),
        StructField("kind", StringType(), False),
        StructField("outcome", StringType(), False),
        StructField("duration_ns", LongType(), False),
    ]), False),
    StructField("http", StructType([
        StructField("request_method", StringType(), False),
        StructField("route", StringType(), False),
        StructField("status_code", IntegerType(), False),
    ]), False),
    StructField("actor", StructType([
        StructField("type", StringType(), False),
        StructField("key", StringType(), True),
    ]), False),
    StructField("client", StructType([
        StructField("user_agent", StringType(), True),
    ]), True),
    StructField("ecommerce", StructType([
        StructField("action", StringType(), False),
        StructField("product_key", StringType(), True),
        StructField("variant_key", StringType(), True),
        StructField("search_query", StringType(), True),
        StructField("search_redacted", BooleanType(), True),
        StructField("filters", MapType(StringType(), StringType()), True),
    ]), False),
    StructField("error", StructType([
        StructField("code", StringType(), True),
        StructField("type", StringType(), True),
    ]), True),
    StructField("data_origin", StringType(), False),
    StructField("_corrupt_record", StringType(), True),
])
```

### 5.2. Core Spark Job: `pipelines/src/jobs/ingest_logs_to_bronze.py`
```python
import argparse
import sys
from pyspark.sql.functions import col, current_timestamp, input_file_name, lit, to_timestamp
from lakehouse.spark import spark_session


def main():
    parser = argparse.ArgumentParser(description="15-minute micro-batch Access Log ingestion to Bronze")
    parser.add_argument("--run-id", required=True, help="Batch execution run ID")
    parser.add_argument("--ingest-date", required=True, help="Target UTC date (YYYY-MM-DD)")
    parser.add_argument("--ingest-hour", required=True, help="Target UTC hour (HH)")
    parser.add_argument("--replay-date", required=False, help="Replay entire date using partition overwrite")
    args = parser.parse_args()

    spark = spark_session("ingest_logs_15m_to_bronze")

    # 1. Resolve Target Landing Path
    if args.replay_date:
        landing_path = f"s3a://lakehouse/landing/logs/ingest_date={args.replay_date}/*/*/*.jsonl.gz"
    else:
        landing_path = (
            f"s3a://lakehouse/landing/logs/"
            f"ingest_date={args.ingest_date}/ingest_hour={args.ingest_hour}/service=ecommerce-api/*.jsonl.gz"
        )

    # 2. Retrieve Committed Files from Bronze for Target Window
    try:
        query_date = args.replay_date or args.ingest_date
        committed_files_df = (
            spark.read.table("lakehouse.bronze.web_events")
            .filter(col("event_ts") >= f"{query_date} 00:00:00")
            .filter(col("event_ts") <= f"{query_date} 23:59:59")
            .select("_source_file")
            .distinct()
        )
        committed_files = set(r[0] for r in committed_files_df.collect())
    except Exception:
        committed_files = set()  # Initial run when table is newly created

    # 3. Read Landing Files with OTel Schema
    try:
        raw_df = spark.read.schema(OTEL_LOG_SCHEMA).json(landing_path)
    except Exception:
        print(f"No Landing files found at {landing_path}. Exiting safely.")
        sys.exit(0)

    # 4. Anti-Join to isolate new files (only during regular incremental ingestion)
    if not args.replay_date and committed_files:
        unprocessed_df = raw_df.filter(~input_file_name().isin(list(committed_files)))
    else:
        unprocessed_df = raw_df

    if unprocessed_df.rdd.isEmpty():
        print(f"All files in {landing_path} are already ingested. Zero-cost No-Op.")
        sys.exit(0)

    # 5. Quarantine Handling
    corrupt_df = unprocessed_df.filter(col("_corrupt_record").isNotNull())
    valid_df = unprocessed_df.filter(col("_corrupt_record").isNull())

    # 6. Lineage Metadata Enrichment
    enriched_df = (
        valid_df
        .withColumn("event_id", col("request.id"))
        .withColumn("event_ts", to_timestamp(col("timestamp")))
        .withColumn("observed_timestamp", to_timestamp(col("observed_timestamp")))
        .withColumn("_run_id", lit(args.run_id))
        .withColumn("_source_system", lit("ecommerce-api-access-log"))
        .withColumn("_source_file", input_file_name())
        .withColumn("_ingested_at", current_timestamp())
        .drop("_corrupt_record", "timestamp")
    )

    # 7. Commit to Iceberg Bronze Table
    if args.replay_date:
        enriched_df.writeTo("lakehouse.bronze.web_events") \
            .overwrite(col("event_ts").cast("date") == lit(args.replay_date))
        print(f"Atomically overwrote partition date={args.replay_date} in lakehouse.bronze.web_events.")
    else:
        enriched_df.writeTo("lakehouse.bronze.web_events").append()
        print(f"Appended 15-minute micro-batch to lakehouse.bronze.web_events.")

    # 8. Commit Corrupt Records to Quarantine (if any)
    if not corrupt_df.rdd.isEmpty():
        corrupt_enriched = (
            corrupt_df
            .select(
                col("_corrupt_record").alias("raw_corrupt_record"),
                lit("Malformed JSON or schema validation failure").alias("error_message"),
                lit("bronze_landing_ingestion").alias("quarantine_stage"),
                lit(args.run_id).alias("_run_id"),
                lit("ecommerce-api-access-log").alias("_source_system"),
                input_file_name().alias("_source_file"),
                current_timestamp().alias("_quarantined_at"),
            )
        )
        corrupt_enriched.writeTo("lakehouse.quarantine.bronze_corrupt_logs").append()
        print("Routed corrupt records to lakehouse.quarantine.bronze_corrupt_logs.")

    spark.stop()


if __name__ == "__main__":
    main()
```

---

## 6. Airflow Orchestration DAG (`airflow/dags/ingest_logs_15m.py`)

```python
import uuid
from datetime import datetime, timedelta, timezone

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator

DEFAULT_ARGS = {
    "owner": "batch",
    "retries": 2,
    "retry_delay": timedelta(minutes=1),
}

with DAG(
    dag_id="ingest_logs_15m_to_bronze",
    default_args=DEFAULT_ARGS,
    schedule_interval="*/15 * * * *",  # Triggers every 15 minutes (00, 15, 30, 45)
    start_date=datetime(2026, 8, 15, tzinfo=timezone.utc),
    catchup=False,
    max_active_runs=1,
    description="15-minute micro-batch ingestion of access logs from Landing to Bronze Iceberg",
) as dag:

    def _begin_run(**context):
        context["ti"].xcom_push(key="run_id", value=uuid.uuid4().hex)

    begin = PythonOperator(
        task_id="begin_run",
        python_callable=_begin_run,
    )

    spark_ingest = SparkSubmitOperator(
        task_id="spark_microbatch_to_bronze",
        application="/opt/project/pipelines/src/jobs/ingest_logs_to_bronze.py",
        application_args=[
            "--run-id", "{{ ti.xcom_pull(task_ids='begin_run', key='run_id') }}",
            "--ingest-date", "{{ data_interval_start.strftime('%Y-%m-%d') }}",
            "--ingest-hour", "{{ data_interval_start.strftime('%H') }}",
        ],
    )

    begin >> spark_ingest
```

---

## 7. Trino Query Patterns on Bronze Nested Structs

Because fields are stored as Iceberg Structs, Trino queries achieve sub-second execution via Parquet sub-column pruning:

### Query 1: Error Rate by HTTP Route
```sql
SELECT 
    http.request_method,
    http.route,
    http.status_code,
    COUNT(*) AS request_count,
    AVG(event.duration_ns) / 1000000.0 AS avg_duration_ms
FROM lakehouse.bronze.web_events
WHERE event_ts >= CURRENT_DATE - INTERVAL '1' DAY
  AND http.status_code >= 400
GROUP BY 1, 2, 3
ORDER BY request_count DESC;
```

### Query 2: Product Views and Cart Actions
```sql
SELECT 
    ecommerce.action,
    ecommerce.product_key,
    COUNT(*) AS total_interactions,
    COUNT(DISTINCT actor.key) AS unique_actors
FROM lakehouse.bronze.web_events
WHERE event_ts >= CURRENT_DATE - INTERVAL '7' DAY
  AND ecommerce.action IN ('product_detail', 'cart_add')
GROUP BY 1, 2
ORDER BY total_interactions DESC
LIMIT 20;
```

### Query 3: Inspect Corrupt Logs in Quarantine
```sql
SELECT 
    _quarantined_at,
    _source_file,
    error_message,
    raw_corrupt_record
FROM lakehouse.quarantine.bronze_corrupt_logs
ORDER BY _quarantined_at DESC
LIMIT 10;
```

---

## 8. Downstream Silver Transformation Scope

Once ingested into Bronze, the Silver layer pipeline will perform:
1. **Deduplication:** Exact deduplication by `event_id` (`request.id`).
2. **PII Pseudonymization:** Cryptographic hashing of `actor.key` (`sha256(actor.key + salt)`).
3. **User Agent Enrichment:** Parsing `client.user_agent` into browser family, OS, and device category.
4. **Business Validation:** Routing records with negative duration or malformed routes to `lakehouse.quarantine.silver_data_quarantine`.
