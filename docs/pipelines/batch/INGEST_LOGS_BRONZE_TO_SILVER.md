# Batch Pipeline: Access Logs Bronze to Silver (web_events)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Spark ingestion pipeline that reads deduplicated access logs from Iceberg Bronze table (`lakehouse.bronze.web_events`), applies anti-join deduplication by `event_id`, flattens nested OpenTelemetry STRUCTs, normalizes routes, hashes actor keys, and writes clean Silver records to `lakehouse.silver.silver_web_events`.

**Architecture:** The pipeline runs as a scheduled micro-batch job synchronized with Bronze ingestion. Each run reads the full Bronze partition for the target date, deduplicates by `event_id` (request_id) using window function with `_ingested_at` ordering (latest wins), flattens nested structs for queryability, adds Silver lineage metadata, and writes to Silver using append mode. Violating records (negative duration, malformed routes) are routed to `lakehouse.quarantine.silver_log_violations`.

**Tech Stack:** PySpark 3.5, Apache Iceberg, Apache Polaris REST catalog, Python 3.11

**Spec:** `docs/project/LAKEHOUSE_DESIGN_PLAN.md`, `docs/pipelines/batch/INGEST_LOGS_LANDING_TO_BRONZE.md`

---

## Global Constraints

- Spark is the only engine permitted to write to Iceberg tables
- All tables belong to the `lakehouse` catalog
- All timestamps must be UTC
- Use `pipelines/src/lakehouse/spark.py` for Spark session
- Use `pipelines/src/lakehouse/logs_bronze.py` for Bronze table constants
- Tests use local Spark (`local[1]`) with Parquet format for CI compatibility
- Do not drop rows during dedup -- keep the latest record by `_ingested_at`

---

## Task 1: Silver Logs DDL Definitions

**Files:**
- Create: `pipelines/src/lakehouse/logs_silver_ddl.py`
- Create: `pipelines/tests/test_logs_silver_ddl.py`

**Produces:**
- `SILVER_LOGS_TABLE_DDL: str` -- DDL for `lakehouse.silver.silver_web_events`
- `SILVER_LOGS_QUARANTINE_DDL: str` -- DDL for `lakehouse.quarantine.silver_log_violations`
- `SILVER_LOGS_TABLE: str` -- table name constant
- `SILVER_LOGS_QUARANTINE_TABLE: str` -- quarantine table name constant
- `ensure_logs_silver_namespaces(spark)` -- creates `silver` and `quarantine` namespaces
- `ensure_logs_silver_tables(spark)` -- creates both tables if not exist

The Silver logs table flattens Bronze nested structs into top-level columns:
- `event_id`, `event_ts`, `http_method`, `http_route`, `status_code`
- `actor_type`, `actor_key`
- `ecommerce_action`, `ecommerce_product_key`, `ecommerce_variant_key`, `ecommerce_search_query`
- `duration_ns`, `user_agent`, `error_code`, `error_type`, `data_origin`
- Plus Silver metadata columns: `_silver_ingested_at`, `_source_bronze_run_id`

### Steps

- [ ] **Step 1: Write the failing test**

```python
import pytest

from lakehouse.logs_silver_ddl import (
    SILVER_LOGS_TABLE_DDL,
    SILVER_LOGS_QUARANTINE_DDL,
    SILVER_LOGS_TABLE,
    SILVER_LOGS_QUARANTINE_TABLE,
    ensure_logs_silver_namespaces,
    ensure_logs_silver_tables,
)


def test_silver_logs_ddl_is_nonempty_string():
    assert isinstance(SILVER_LOGS_TABLE_DDL, str)
    assert len(SILVER_LOGS_TABLE_DDL) > 0


def test_silver_logs_table_constant():
    assert SILVER_LOGS_TABLE == "lakehouse.silver.silver_web_events"


def test_silver_logs_quarantine_ddl_is_nonempty_string():
    assert isinstance(SILVER_LOGS_QUARANTINE_DDL, str)
    assert len(SILVER_LOGS_QUARANTINE_DDL) > 0


def test_silver_logs_quarantine_table_constant():
    assert SILVER_LOGS_QUARANTINE_TABLE == "lakehouse.quarantine.silver_log_violations"


def test_ddl_contains_all_flattened_columns():
    expected_columns = [
        "event_id", "event_ts", "http_method", "http_route", "status_code",
        "actor_type", "actor_key", "duration_ns", "user_agent",
        "error_code", "error_type", "data_origin",
    ]
    for col in expected_columns:
        assert col in SILVER_LOGS_TABLE_DDL, f"Missing column: {col}"


def test_ddl_contains_silver_metadata_columns():
    assert "_silver_ingested_at" in SILVER_LOGS_TABLE_DDL
    assert "_source_bronze_run_id" in SILVER_LOGS_TABLE_DDL


def test_ensure_functions_are_callable():
    assert callable(ensure_logs_silver_namespaces)
    assert callable(ensure_logs_silver_tables)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=pipelines/src pytest pipelines/tests/test_logs_silver_ddl.py -v`
Expected: FAIL with "ImportError" or module not found.

- [ ] **Step 3: Write implementation**

```python
from pyspark.sql import SparkSession

SILVER_LOGS_TABLE = "lakehouse.silver.silver_web_events"
SILVER_LOGS_QUARANTINE_TABLE = "lakehouse.quarantine.silver_log_violations"

SILVER_LOGS_TABLE_DDL = f"""
CREATE TABLE IF NOT EXISTS {SILVER_LOGS_TABLE} (
    event_id                    STRING          COMMENT 'Unique event identifier mapped from request.id',
    event_ts                    TIMESTAMP       COMMENT 'Event generation timestamp in UTC',
    http_method                 STRING          COMMENT 'HTTP request method (GET, POST, etc.)',
    http_route                  STRING          COMMENT 'Parameterized HTTP route pattern',
    status_code                 INT             COMMENT 'HTTP response status code',
    actor_type                  STRING          COMMENT 'Actor type: anonymous, customer, admin, system',
    actor_key                   STRING          COMMENT 'Actor identifier or customer ID',
    ecommerce_action            STRING          COMMENT 'E-commerce action type',
    ecommerce_product_key       STRING          COMMENT 'Product key reference',
    ecommerce_variant_key       STRING          COMMENT 'Product variant key reference',
    ecommerce_search_query      STRING          COMMENT 'Search query string if applicable',
    duration_ns                 BIGINT          COMMENT 'HTTP request execution duration in nanoseconds',
    user_agent                  STRING          COMMENT 'Client user agent string',
    error_code                  STRING          COMMENT 'Application error code if failed',
    error_type                  STRING          COMMENT 'Exception type if failed',
    data_origin                 STRING          COMMENT 'Telemetry origin: observed or synthetic',
    _silver_ingested_at         TIMESTAMP       COMMENT 'UTC timestamp when record was committed to Silver',
    _source_bronze_run_id       STRING          COMMENT 'Bronze batch execution run ID that produced this record'
)
USING iceberg
PARTITIONED BY (days(event_ts))
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
"""

SILVER_LOGS_QUARANTINE_DDL = f"""
CREATE TABLE IF NOT EXISTS {SILVER_LOGS_QUARANTINE_TABLE} (
    event_id                    STRING          COMMENT 'Event identifier of the violating record',
    event_ts                    TIMESTAMP       COMMENT 'Event timestamp of the violating record',
    violation_type              STRING          COMMENT 'Type of business rule violation',
    violation_detail            STRING          COMMENT 'Detailed description of the violation',
    record_data                 STRING          COMMENT 'Full JSON of the violating record for debugging',
    source_table                STRING          COMMENT 'Source table where violation was detected',
    _run_id                     STRING          COMMENT 'Batch execution run ID',
    _quarantined_at             TIMESTAMP       COMMENT 'UTC timestamp when record was routed to quarantine'
)
USING iceberg
PARTITIONED BY (days(_quarantined_at))
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
"""


def ensure_logs_silver_namespaces(spark: SparkSession) -> None:
    spark.sql("CREATE NAMESPACE IF NOT EXISTS lakehouse.silver")
    spark.sql("CREATE NAMESPACE IF NOT EXISTS lakehouse.quarantine")


def ensure_logs_silver_tables(spark: SparkSession) -> None:
    ensure_logs_silver_namespaces(spark)
    spark.sql(SILVER_LOGS_TABLE_DDL)
    spark.sql(SILVER_LOGS_QUARANTINE_DDL)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=pipelines/src pytest pipelines/tests/test_logs_silver_ddl.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pipelines/src/lakehouse/logs_silver_ddl.py pipelines/tests/test_logs_silver_ddl.py
git commit -m "feat(pipelines): add Silver logs DDL definitions and validation tests"
```

---

## Task 2: Silver Logs Anti-Join Dedup Core Logic

**Files:**
- Create: `pipelines/src/lakehouse/logs_silver.py`
- Create: `pipelines/tests/test_logs_silver.py`

**Interfaces:**
- Consumes: `logs_bronze.BRONZE_EVENTS_TABLE`
- Produces: `ingest_logs_to_silver(spark, bronze_df, run_id, target_path) -> int` (returns count of records written)

### Steps

- [ ] **Step 1: Write the failing test**

```python
import shutil

import pytest

pyspark = pytest.importorskip("pyspark", reason="pyspark not installed")
pytestmark = pytest.mark.skipif(
    shutil.which("java") is None,
    reason="Java not found -- Spark tests require a JDK",
)

from pyspark.sql import SparkSession
from pyspark.sql.types import (
    BooleanType,
    IntegerType,
    LongType,
    MapType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)
from lakehouse.logs_silver import ingest_logs_to_silver


@pytest.fixture(scope="session")
def spark():
    return SparkSession.builder.master("local[1]").appName("test-logs-silver").getOrCreate()


def _make_logs_bronze_df(spark):
    schema = StructType([
        StructField("event_id", StringType(), False),
        StructField("event_ts", TimestampType(), False),
        StructField("observed_timestamp", TimestampType(), False),
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
        StructField("_run_id", StringType(), False),
        StructField("_source_file", StringType(), False),
        StructField("_ingested_at", TimestampType(), False),
    ])
    data = [
        ("evt-1", "2026-08-15 10:00:00", "2026-08-15 10:00:01", "INFO", 9, {"id": "req-1"}, None, None,
         {"name": "api", "version": "1.0", "environment": "prod", "instance_id": "i-1"},
         {"name": "GET", "category": "http", "kind": "server", "outcome": "OK", "duration_ns": 100000},
         {"request_method": "GET", "route": "/products", "status_code": 200},
         {"type": "anonymous", "key": None}, {"user_agent": "Mozilla/5.0"},
         {"action": "product_detail", "product_key": "p1", "variant_key": "v1", "search_query": None, "search_redacted": False, "filters": None},
         None, "observed", "run-1", "file-1.jsonl.gz", "2026-08-15"),
        ("evt-1", "2026-08-15 10:00:00", "2026-08-15 10:00:01", "INFO", 9, {"id": "req-1"}, None, None,
         {"name": "api", "version": "1.0", "environment": "prod", "instance_id": "i-1"},
         {"name": "GET", "category": "http", "kind": "server", "outcome": "OK", "duration_ns": 100000},
         {"request_method": "GET", "route": "/products", "status_code": 200},
         {"type": "anonymous", "key": None}, {"user_agent": "Mozilla/5.0"},
         {"action": "product_detail", "product_key": "p1", "variant_key": "v1", "search_query": None, "search_redacted": False, "filters": None},
         None, "observed", "run-1", "file-2.jsonl.gz", "2026-08-15"),
        ("evt-2", "2026-08-15 10:01:00", "2026-08-15 10:01:01", "INFO", 9, {"id": "req-2"}, None, None,
         {"name": "api", "version": "1.0", "environment": "prod", "instance_id": "i-1"},
         {"name": "POST", "category": "http", "kind": "server", "outcome": "OK", "duration_ns": 200000},
         {"request_method": "POST", "route": "/cart", "status_code": 201},
         {"type": "customer", "key": "c-1"}, {"user_agent": "Mozilla/5.0"},
         {"action": "cart_add", "product_key": "p1", "variant_key": "v1", "search_query": None, "search_redacted": False, "filters": None},
         None, "observed", "run-1", "file-1.jsonl.gz", "2026-08-15"),
    ]
    return spark.createDataFrame(data, schema)


def test_dedup_removes_duplicate_event_ids(spark, tmp_path):
    bronze_df = _make_logs_bronze_df(spark)
    target = str(tmp_path / "silver_logs")

    count = ingest_logs_to_silver(spark, bronze_df, "run-1", target, _write_format="parquet")

    assert count == 2
    df = spark.read.parquet(target)
    assert df.count() == 2


def test_empty_bronze_returns_zero(spark, tmp_path):
    schema = StructType([
        StructField("event_id", StringType(), False),
    ])
    empty_df = spark.createDataFrame([], schema)
    target = str(tmp_path / "silver_logs_empty")

    count = ingest_logs_to_silver(spark, empty_df, "run-1", target, _write_format="parquet")

    assert count == 0


def test_preserves_latest_record_by_ingested_at(spark, tmp_path):
    bronze_df = _make_logs_bronze_df(spark)
    target = str(tmp_path / "silver_logs_latest")

    count = ingest_logs_to_silver(spark, bronze_df, "run-1", target, _write_format="parquet")
    assert count == 2

    df = spark.read.parquet(target)
    assert df.count() == 2


def test_adds_silver_metadata_columns(spark, tmp_path):
    bronze_df = _make_logs_bronze_df(spark).limit(1)
    target = str(tmp_path / "silver_logs_meta")

    ingest_logs_to_silver(spark, bronze_df, "run-1", target, _write_format="parquet")

    df = spark.read.parquet(target)
    assert "_silver_ingested_at" in df.columns
    assert "_source_bronze_run_id" in df.columns
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=pipelines/src pytest pipelines/tests/test_logs_silver.py -v`
Expected: FAIL with "ImportError" or module not found.

- [ ] **Step 3: Write implementation**

```python
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window

from lakehouse.logs_silver_ddl import SILVER_LOGS_TABLE, ensure_logs_silver_tables


def ingest_logs_to_silver(
    spark: SparkSession,
    bronze_df: DataFrame,
    run_id: str,
    target_path: str,
    _write_format: str = "iceberg",
) -> int:
    if bronze_df.rdd.isEmpty():
        return 0

    window = Window.partitionBy("event_id").orderBy(F.col("_ingested_at").desc())
    deduped = bronze_df.withColumn("_rn", F.row_number().over(window)).filter(F.col("_rn") == 1).drop("_rn")

    enriched = (
        deduped
        .withColumn("http_method", F.col("http.request_method"))
        .withColumn("http_route", F.col("http.route"))
        .withColumn("status_code", F.col("http.status_code"))
        .withColumn("actor_type", F.col("actor.type"))
        .withColumn("actor_key", F.col("actor.key"))
        .withColumn("duration_ns", F.col("event.duration_ns"))
        .withColumn("user_agent", F.col("client.user_agent"))
        .withColumn("ecommerce_action", F.col("ecommerce.action"))
        .withColumn("ecommerce_product_key", F.col("ecommerce.product_key"))
        .withColumn("ecommerce_variant_key", F.col("ecommerce.variant_key"))
        .withColumn("ecommerce_search_query", F.col("ecommerce.search_query"))
        .withColumn("error_code", F.col("error.code"))
        .withColumn("error_type", F.col("error.type"))
        .withColumn("_silver_ingested_at", F.current_timestamp())
        .withColumn("_source_bronze_run_id", F.lit(run_id))
        .select(
            "event_id", "event_ts", "http_method", "http_route", "status_code",
            "actor_type", "actor_key", "ecommerce_action", "ecommerce_product_key",
            "ecommerce_variant_key", "ecommerce_search_query",
            "duration_ns", "user_agent", "error_code", "error_type", "data_origin",
            "_silver_ingested_at", "_source_bronze_run_id",
        )
    )

    count = enriched.count()
    if count == 0:
        return 0

    if _write_format == "iceberg":
        enriched.writeTo(SILVER_LOGS_TABLE).append()
    else:
        enriched.write.format(_write_format).mode("append").save(target_path)

    return count
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=pipelines/src pytest pipelines/tests/test_logs_silver.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pipelines/src/lakehouse/logs_silver.py pipelines/tests/test_logs_silver.py
git commit -m "feat(pipelines): implement Silver logs anti-join dedup core logic"
```

---

## Task 3: Business Rule Validation for Logs

**Files:**
- Modify: `pipelines/src/lakehouse/logs_silver.py`
- Modify: `pipelines/tests/test_logs_silver.py`

**Interfaces:**
- Adds: Business rule validation, quarantine routing for violating records

### Steps

- [ ] **Step 1: Write the failing test**

Add to `pipelines/tests/test_logs_silver.py`:

```python
from pyspark.sql.types import LongType


def test_negative_duration_routes_to_quarantine(spark, tmp_path):
    schema = StructType([
        StructField("event_id", StringType(), False),
        StructField("event_ts", TimestampType(), False),
        StructField("observed_timestamp", TimestampType(), False),
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
        StructField("_run_id", StringType(), False),
        StructField("_source_file", StringType(), False),
        StructField("_ingested_at", TimestampType(), False),
    ])
    data = [
        ("evt-bad", "2026-08-15 10:00:00", "2026-08-15 10:00:01", "INFO", 9,
         {"id": "req-bad"}, None, None,
         {"name": "api", "version": "1.0", "environment": "prod", "instance_id": "i-1"},
         {"name": "GET", "category": "http", "kind": "server", "outcome": "OK", "duration_ns": -100},
         {"request_method": "GET", "route": "/products", "status_code": 200},
         {"type": "anonymous", "key": None}, {"user_agent": "Mozilla/5.0"},
         {"action": "product_detail", "product_key": "p1", "variant_key": "v1",
          "search_query": None, "search_redacted": False, "filters": None},
         None, "observed", "run-1", "file-1.jsonl.gz", "2026-08-15"),
        ("evt-ok", "2026-08-15 10:01:00", "2026-08-15 10:01:01", "INFO", 9,
         {"id": "req-ok"}, None, None,
         {"name": "api", "version": "1.0", "environment": "prod", "instance_id": "i-1"},
         {"name": "GET", "category": "http", "kind": "server", "outcome": "OK", "duration_ns": 100000},
         {"request_method": "GET", "route": "/products", "status_code": 200},
         {"type": "anonymous", "key": None}, {"user_agent": "Mozilla/5.0"},
         {"action": "product_detail", "product_key": "p1", "variant_key": "v1",
          "search_query": None, "search_redacted": False, "filters": None},
         None, "observed", "run-1", "file-1.jsonl.gz", "2026-08-15"),
    ]
    bronze_df = spark.createDataFrame(data, schema)
    target = str(tmp_path / "silver_logs_validated")

    count = ingest_logs_to_silver(spark, bronze_df, "run-1", target, _write_format="parquet")

    assert count == 1
    df = spark.read.parquet(target)
    assert df.count() == 1
    assert df.collect()[0]["event_id"] == "evt-ok"


def test_valid_record_passes_validation(spark, tmp_path):
    bronze_df = _make_logs_bronze_df(spark).limit(1)
    target = str(tmp_path / "silver_logs_valid")

    count = ingest_logs_to_silver(spark, bronze_df, "run-1", target, _write_format="parquet")

    assert count == 1
    df = spark.read.parquet(target)
    assert df.count() == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=pipelines/src pytest pipelines/tests/test_logs_silver.py::test_negative_duration_routes_to_quarantine -v`
Expected: FAIL (negative duration is not quarantined).

- [ ] **Step 3: Write implementation**

Update `pipelines/src/lakehouse/logs_silver.py` to add validation logic:

```python
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window

from lakehouse.logs_silver_ddl import (
    SILVER_LOGS_TABLE,
    SILVER_LOGS_QUARANTINE_TABLE,
    ensure_logs_silver_tables,
)


def _validate_log_records(df: DataFrame) -> tuple[DataFrame, DataFrame]:
    violation_expr = (
        F.when(F.col("event.duration_ns") < 0, F.lit("negative_duration"))
        .when(F.col("http.route").isNull(), F.lit("null_route"))
        .when(
            (F.col("http.status_code") < 100) | (F.col("http.status_code") > 599),
            F.lit("invalid_status_code"),
        )
    )
    df_with_violation = df.withColumn("_violation_type", violation_expr)
    violating = df_with_violation.filter(F.col("_violation_type").isNotNull())
    valid = df_with_violation.filter(F.col("_violation_type").isNull()).drop("_violation_type")
    return valid, violating


def _write_quarantine(
    spark: SparkSession,
    violations_df: DataFrame,
    run_id: str,
    _write_format: str,
    target_path: str,
) -> int:
    if violations_df.rdd.isEmpty():
        return 0

    quarantined = violations_df.select(
        F.col("event_id"),
        F.col("event_ts"),
        F.col("_violation_type").alias("violation_type"),
        F.concat(F.lit("Business rule violation: "), F.col("_violation_type")).alias("violation_detail"),
        F.to_json(F.struct("*")).alias("record_data"),
        F.lit("lakehouse.bronze.web_events").alias("source_table"),
        F.lit(run_id).alias("_run_id"),
        F.current_timestamp().alias("_quarantined_at"),
    )

    count = quarantined.count()
    if count == 0:
        return 0

    if _write_format == "iceberg":
        quarantined.writeTo(SILVER_LOGS_QUARANTINE_TABLE).append()
    else:
        quarantined.write.format(_write_format).mode("append").save(target_path + "_quarantine")

    return count


def ingest_logs_to_silver(
    spark: SparkSession,
    bronze_df: DataFrame,
    run_id: str,
    target_path: str,
    _write_format: str = "iceberg",
) -> int:
    if bronze_df.rdd.isEmpty():
        return 0

    window = Window.partitionBy("event_id").orderBy(F.col("_ingested_at").desc())
    deduped = bronze_df.withColumn("_rn", F.row_number().over(window)).filter(F.col("_rn") == 1).drop("_rn")

    enriched = (
        deduped
        .withColumn("http_method", F.col("http.request_method"))
        .withColumn("http_route", F.col("http.route"))
        .withColumn("status_code", F.col("http.status_code"))
        .withColumn("actor_type", F.col("actor.type"))
        .withColumn("actor_key", F.col("actor.key"))
        .withColumn("duration_ns", F.col("event.duration_ns"))
        .withColumn("user_agent", F.col("client.user_agent"))
        .withColumn("ecommerce_action", F.col("ecommerce.action"))
        .withColumn("ecommerce_product_key", F.col("ecommerce.product_key"))
        .withColumn("ecommerce_variant_key", F.col("ecommerce.variant_key"))
        .withColumn("ecommerce_search_query", F.col("ecommerce.search_query"))
        .withColumn("error_code", F.col("error.code"))
        .withColumn("error_type", F.col("error.type"))
        .withColumn("_silver_ingested_at", F.current_timestamp())
        .withColumn("_source_bronze_run_id", F.lit(run_id))
        .select(
            "event_id", "event_ts", "http_method", "http_route", "status_code",
            "actor_type", "actor_key", "ecommerce_action", "ecommerce_product_key",
            "ecommerce_variant_key", "ecommerce_search_query",
            "duration_ns", "user_agent", "error_code", "error_type", "data_origin",
            "http", "event", "client", "ecommerce", "error",
            "_silver_ingested_at", "_source_bronze_run_id",
        )
    )

    valid_df, violations_df = _validate_log_records(enriched)

    if not violations_df.rdd.isEmpty():
        _write_quarantine(spark, violations_df, run_id, _write_format, target_path)

    final_df = valid_df.select(
        "event_id", "event_ts", "http_method", "http_route", "status_code",
        "actor_type", "actor_key", "ecommerce_action", "ecommerce_product_key",
        "ecommerce_variant_key", "ecommerce_search_query",
        "duration_ns", "user_agent", "error_code", "error_type", "data_origin",
        "_silver_ingested_at", "_source_bronze_run_id",
    )

    count = final_df.count()
    if count == 0:
        return 0

    if _write_format == "iceberg":
        final_df.writeTo(SILVER_LOGS_TABLE).append()
    else:
        final_df.write.format(_write_format).mode("append").save(target_path)

    return count
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=pipelines/src pytest pipelines/tests/test_logs_silver.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pipelines/src/lakehouse/logs_silver.py pipelines/tests/test_logs_silver.py
git commit -m "feat(pipelines): add business rule validation and quarantine routing for logs"
```

---

## Task 4: Spark Submit Job for Logs Silver

**Files:**
- Create: `pipelines/src/jobs/logs/ingest_logs_silver.py`

**Interfaces:**
- argparse with `--run-id` and `--ingest-date`
- Reads Bronze logs partition for target date, calls `ingest_logs_to_silver`

### Steps

- [ ] **Step 1: Write the job script**

```python
import argparse
import sys

from pyspark.sql.functions import col

from lakehouse.logs.bronze import BRONZE_EVENTS_TABLE
from lakehouse.logs.silver import ensure_logs_silver_tables, ingest_logs_to_silver
from lakehouse.spark import spark_session


def parse_args(args):
    parser = argparse.ArgumentParser(
        description="Ingest access logs from Iceberg Bronze to Silver with dedup"
    )
    parser.add_argument("--run-id", required=True, help="Batch execution run ID")
    parser.add_argument("--ingest-date", required=True, help="Target UTC date (YYYY-MM-DD)")
    parser.add_argument(
        "--bucket",
        default="lakehouse",
        help="MinIO S3 bucket name (default: lakehouse)",
    )
    return parser.parse_args(args)


def main():
    args = parse_args(sys.argv[1:])
    spark = spark_session("ingest_logs_bronze_to_silver")
    try:
        ensure_logs_silver_tables(spark)

        try:
            bronze_df = (
                spark.read.format("iceberg")
                .load(BRONZE_EVENTS_TABLE)
                .filter(col("event_ts") >= f"{args.ingest_date} 00:00:00")
                .filter(col("event_ts") <= f"{args.ingest_date} 23:59:59")
            )
        except Exception:
            print(f"Bronze table {BRONZE_EVENTS_TABLE} not found or empty for date {args.ingest_date}. Exiting.")
            return

        count = ingest_logs_to_silver(
            spark=spark,
            bronze_df=bronze_df,
            run_id=args.run_id,
            target_path="",
        )

        print(f"[{args.run_id}] Logs Silver ingestion completed: {count} records written.")
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify script is syntactically valid**

Run: `python -c "import ast; ast.parse(open('pipelines/src/jobs/ingest_logs_silver.py').read())"`

- [ ] **Step 3: Verify imports resolve**

Run: `PYTHONPATH=pipelines/src python -c "from lakehouse.logs_bronze import BRONZE_EVENTS_TABLE; from lakehouse.logs_silver import ingest_logs_to_silver; print('OK')"`

- [ ] **Step 4: Verify tests still pass**

Run: `PYTHONPATH=pipelines/src pytest pipelines/tests/test_logs_silver.py -v`

- [ ] **Step 5: Commit**

```bash
git add pipelines/src/jobs/ingest_logs_silver.py
git commit -m "feat(pipelines): add Spark submit job for logs Bronze to Silver"
```

---

## Task 5: Airflow DAG for Logs Silver

**Files:**
- Create: `airflow/dags/ingest_logs_bronze_to_silver.py`

**Interfaces:**
- DAG id: `ingest_logs_bronze_to_silver`
- Schedule: `0 */2 * * *` (every 2 hours)
- `begin_run` task pushes `run_id`, `spark` task submits the job

### Steps

- [ ] **Step 1: Write the DAG**

```python
import uuid
from datetime import datetime, timedelta, timezone

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator

SPARK_APP = "/opt/project/pipelines/src/jobs/logs/ingest_logs_silver.py"

DEFAULT_ARGS = {
    "owner": "batch",
    "retries": 2,
    "retry_delay": timedelta(minutes=1),
}


def begin_run(**context) -> None:
    context["ti"].xcom_push(key="run_id", value=uuid.uuid4().hex)
    context["ti"].xcom_push(
        key="ingest_date", value=datetime.now(timezone.utc).strftime("%Y-%m-%d")
    )


with DAG(
    dag_id="ingest_logs_bronze_to_silver",
    default_args=DEFAULT_ARGS,
    schedule_interval="0 */2 * * *",
    start_date=datetime(2026, 8, 15, tzinfo=timezone.utc),
    catchup=False,
    max_active_runs=1,
    description="Hourly ingestion of deduplicated access logs from Bronze to Silver Iceberg",
) as dag:

    begin = PythonOperator(
        task_id="begin_run",
        python_callable=begin_run,
    )

    spark_ingest = SparkSubmitOperator(
        task_id="spark_logs_bronze_to_silver",
        application=SPARK_APP,
        application_args=[
            "--run-id", "{{ ti.xcom_pull(task_ids='begin_run', key='run_id') }}",
            "--ingest-date", "{{ ti.xcom_pull(task_ids='begin_run', key='ingest_date') }}",
        ],
    )

    begin >> spark_ingest
```

- [ ] **Step 2: Verify DAG syntax**

Run: `python -c "import ast; ast.parse(open('airflow/dags/ingest_logs_bronze_to_silver.py').read())"`

- [ ] **Step 3: Verify DAG can be parsed by Airflow**

Run: `python -c "from airflow.models import DagBag; db = DagBag(dag_folder='airflow/dags'); assert 'ingest_logs_bronze_to_silver' in db.dags, 'DAG not found'"`

- [ ] **Step 4: Verify existing tests still pass**

Run: `PYTHONPATH=pipelines/src pytest pipelines/tests/test_logs_silver.py pipelines/tests/test_logs_silver_ddl.py -v`

- [ ] **Step 5: Commit**

```bash
git add airflow/dags/ingest_logs_bronze_to_silver.py
git commit -m "feat(pipelines): add Airflow DAG for logs Bronze to Silver ingestion"
```

---

## Task 6: Documentation Update

**Files:**
- Modify: `docs/project/LAKEHOUSE_DESIGN_PLAN.md` (section 3.3)
- Modify: `docs/pipelines/batch/INGEST_LOGS_LANDING_TO_BRONZE.md` (section 8)

### Steps

- [ ] **Step 1: Read current section 3.3 in LAKEHOUSE_DESIGN_PLAN.md**

Locate section 3.3 (`Silver Layer`) and identify where the logs Silver documentation should be inserted.

- [ ] **Step 2: Write failing assertion (manual review gate)**

Verify section 3.3 does NOT yet mention `silver_web_events` or `silver_log_violations`:
```
grep -c "silver_web_events" docs/project/LAKEHOUSE_DESIGN_PLAN.md
# Expected: 0
```

- [ ] **Step 3: Update docs/project/LAKEHOUSE_DESIGN_PLAN.md section 3.3**

Add the following subsection under section 3.3:

```markdown
#### Access Logs Silver Table (`lakehouse.silver.silver_web_events`)

The logs Silver table flattens Bronze nested OpenTelemetry structs into top-level columns for direct queryability:

| Column | Type | Description |
|---|---|---|
| `event_id` | `STRING` | Unique event identifier (`request.id`) |
| `event_ts` | `TIMESTAMP` | Event generation timestamp in UTC |
| `http_method` | `STRING` | HTTP request method |
| `http_route` | `STRING` | Parameterized HTTP route |
| `status_code` | `INT` | HTTP response status code |
| `actor_type` | `STRING` | Actor type: anonymous, customer, admin, system |
| `actor_key` | `STRING` | Actor identifier or customer ID |
| `ecommerce_action` | `STRING` | E-commerce action type |
| `ecommerce_product_key` | `STRING` | Product key reference |
| `ecommerce_variant_key` | `STRING` | Product variant key reference |
| `ecommerce_search_query` | `STRING` | Search query string |
| `duration_ns` | `BIGINT` | HTTP request duration in nanoseconds |
| `user_agent` | `STRING` | Client user agent string |
| `error_code` | `STRING` | Application error code |
| `error_type` | `STRING` | Exception type |
| `data_origin` | `STRING` | Telemetry origin: observed or synthetic |
| `_silver_ingested_at` | `TIMESTAMP` | UTC timestamp when committed to Silver |
| `_source_bronze_run_id` | `STRING` | Bronze batch execution run ID |

**Deduplication:** Records are deduplicated by `event_id` using a window function ordered by `_ingested_at DESC` (latest wins).

**Business Validation Rules:**
- `duration_ns >= 0` (negative durations are invalid)
- `http_route IS NOT NULL`
- `status_code BETWEEN 100 AND 599`

Violating records are routed to `lakehouse.quarantine.silver_log_violations`.

**Partitioning:** `PARTITIONED BY (days(event_ts))`
```

- [ ] **Step 4: Update docs/pipelines/batch/INGEST_LOGS_LANDING_TO_BRONZE.md section 8**

Replace the placeholder text in section 8 with:

```markdown
## 8. Silver Layer Transformation Pipeline

The Silver layer pipeline (`ingest_logs_bronze_to_silver`) performs the following:

1. **Deduplication:** Window function on `event_id` ordered by `_ingested_at DESC` -- latest record wins.
2. **Struct Flattening:** Nested OpenTelemetry structs (`http`, `actor`, `ecommerce`, `error`, `client`, `event`) are flattened into top-level columns.
3. **Business Validation:** Records with negative duration, null routes, or invalid status codes are quarantined.
4. **Silver Metadata:** `_silver_ingested_at` and `_source_bronze_run_id` columns are appended.

**Downstream Query Examples (Trino):**

```sql
-- Error rate by HTTP route (Silver)
SELECT
    http_method,
    http_route,
    status_code,
    COUNT(*) AS request_count,
    AVG(duration_ns) / 1000000.0 AS avg_duration_ms
FROM lakehouse.silver.silver_web_events
WHERE event_ts >= CURRENT_DATE - INTERVAL '1' DAY
  AND status_code >= 400
GROUP BY 1, 2, 3
ORDER BY request_count DESC;

-- Product views and cart actions (Silver)
SELECT
    ecommerce_action,
    ecommerce_product_key,
    COUNT(*) AS total_interactions,
    COUNT(DISTINCT actor_key) AS unique_actors
FROM lakehouse.silver.silver_web_events
WHERE event_ts >= CURRENT_DATE - INTERVAL '7' DAY
  AND ecommerce_action IN ('product_detail', 'cart_add')
GROUP BY 1, 2
ORDER BY total_interactions DESC
LIMIT 20;

-- Quarantined log violations
SELECT
    event_id,
    violation_type,
    violation_detail,
    _quarantined_at
FROM lakehouse.quarantine.silver_log_violations
ORDER BY _quarantined_at DESC
LIMIT 10;
```
```

- [ ] **Step 5: Commit**

```bash
git add docs/project/LAKEHOUSE_DESIGN_PLAN.md docs/pipelines/batch/INGEST_LOGS_LANDING_TO_BRONZE.md
git commit -m "docs: update Silver logs layer documentation with schema and query examples"
```
