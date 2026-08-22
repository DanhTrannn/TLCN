# Landing to Bronze Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Spark ingestion pipeline that reads raw files from MinIO Landing zone, applies permissive schema parsing, routes unparseable records to quarantine, and appends valid records to Iceberg Bronze tables with lineage metadata.

**Architecture:** We use a Dead-Letter pattern via Spark's `PERMISSIVE` mode. Records failing to parse are caught in `_corrupt_record`. If the error rate is under a threshold (e.g., 1%), valid records are appended to the main Bronze table and errors to a Quarantine table. If it exceeds the threshold, the job fails fast to prevent cascading data corruption. Metadata (`_run_id`, `_source_file`, `_ingested_at_utc`) is injected to support idempotency and auditing.

**Tech Stack:** PySpark 3.5, Apache Iceberg, MinIO (S3), Python 3.11

**Spec:** `docs/project/LAKEHOUSE_DESIGN_PLAN.md`

## Global Constraints

- Use `pipelines/src/lakehouse/spark.py` to initialize the Spark session for the main job.
- Do not apply strict casting; Bronze is an append-only raw archive.
- Ensure all tables belong to the `lakehouse` catalog (e.g., `lakehouse.bronze.orders`).
- All timestamps must be UTC.

---

### Task 1: Implement Bronze Ingestion Core Logic

**Files:**
- Create: `pipelines/src/lakehouse/bronze.py`
- Create: `pipelines/tests/test_bronze.py`

**Interfaces:**
- Produces: `ingest_to_bronze(spark: SparkSession, run_id: str, source_path: str, format: str, target_table: str, quarantine_table: str, error_threshold: float = 0.01) -> None`

- [ ] **Step 1: Write the failing test**

```python
import pytest
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType

from lakehouse.bronze import ingest_to_bronze

@pytest.fixture(scope="session")
def spark():
    return SparkSession.builder.master("local[1]").appName("test-bronze").getOrCreate()

def test_ingest_to_bronze_ok(spark, tmp_path):
    # Create valid JSONL data
    source_dir = tmp_path / "landing"
    source_dir.mkdir()
    (source_dir / "data.json").write_text('{"id": 1, "name": "A"}\n{"id": 2, "name": "B"}\n')

    target_dir = tmp_path / "target"
    quarantine_dir = tmp_path / "quarantine"

    # We use Parquet for local testing instead of Iceberg for simplicity
    ingest_to_bronze(
        spark=spark,
        run_id="run-123",
        source_path=str(source_dir),
        format="json",
        target_table=str(target_dir),
        quarantine_table=str(quarantine_dir),
        error_threshold=0.01,
        # override write format for local testing
        _write_format="parquet"
    )

    df = spark.read.parquet(str(target_dir))
    assert df.count() == 2
    assert "_run_id" in df.columns
    assert "_source_file" in df.columns
    assert "_ingested_at_utc" in df.columns
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=pipelines/src pytest pipelines/tests/test_bronze.py::test_ingest_to_bronze_ok -v`
Expected: FAIL with "ImportError" or function not found.

- [ ] **Step 3: Write minimal implementation**

```python
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit, input_file_name, current_timestamp

def ingest_to_bronze(
    spark: SparkSession,
    run_id: str,
    source_path: str,
    format: str,
    target_table: str,
    quarantine_table: str,
    error_threshold: float = 0.01,
    _write_format: str = "iceberg"
) -> None:
    # Read permissive mode
    df = (
        spark.read
        .option("mode", "PERMISSIVE")
        .option("columnNameOfCorruptRecord", "_corrupt_record")
        .format(format)
        .load(source_path)
    )

    # Add lineage columns
    df = df.withColumn("_run_id", lit(run_id)) \
           .withColumn("_source_file", input_file_name()) \
           .withColumn("_ingested_at_utc", current_timestamp())

    df.cache()
    total_count = df.count()
    if total_count == 0:
        return

    # Check for errors
    if "_corrupt_record" in df.columns:
        error_df = df.filter(col("_corrupt_record").isNotNull())
        error_count = error_df.count()

        if error_count / total_count >= error_threshold:
            raise RuntimeError(f"Error threshold exceeded: {error_count} errors out of {total_count} records.")

        if error_count > 0:
            if _write_format == "iceberg":
                error_df.write.format("iceberg").mode("append").saveAsTable(quarantine_table)
            else:
                error_df.write.format(_write_format).mode("append").save(quarantine_table)

        valid_df = df.filter(col("_corrupt_record").isNull()).drop("_corrupt_record")
    else:
        valid_df = df

    # Write valid to target
    if _write_format == "iceberg":
        valid_df.write.format("iceberg").mode("append").saveAsTable(target_table)
    else:
        valid_df.write.format(_write_format).mode("append").save(target_table)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=pipelines/src pytest pipelines/tests/test_bronze.py::test_ingest_to_bronze_ok -v`
Expected: PASS

- [ ] **Step 5: Write threshold test & implement**

Write test `test_ingest_to_bronze_threshold_exceeded` that creates corrupted JSON (`{"id": 1, ...` without closing brace) causing it to hit the `_corrupt_record` and raise `RuntimeError`. Run it and ensure it passes.

- [ ] **Step 6: Commit**

```bash
git add pipelines/src/lakehouse/bronze.py pipelines/tests/test_bronze.py
git commit -m "feat(pipelines): implement permissive bronze ingestion logic with quarantine"
```

---

### Task 2: Implement Spark Job Script

**Files:**
- Create: `pipelines/src/jobs/ingest_bronze.py`

**Interfaces:**
- Consumes: `lakehouse.bronze.ingest_to_bronze`, `lakehouse.spark.spark_session`

- [ ] **Step 1: Write the job script**

```python
import argparse
import sys
from lakehouse.spark import spark_session
from lakehouse.bronze import ingest_to_bronze

def parse_args(args):
    parser = argparse.ArgumentParser(description="Ingest Landing data to Bronze")
    parser.add_argument("--job-name", required=True, help="Spark application name")
    parser.add_argument("--run-id", required=True, help="Airflow DAG run ID or unique identifier")
    parser.add_argument("--source-path", required=True, help="S3 path to the landing directory")
    parser.add_argument("--format", required=True, choices=["parquet", "json"], help="Source data format")
    parser.add_argument("--target-table", required=True, help="Iceberg target table (e.g., lakehouse.bronze.orders)")
    parser.add_argument("--quarantine-table", required=True, help="Iceberg quarantine table")
    parser.add_argument("--error-threshold", type=float, default=0.01, help="Fraction of allowed corrupt records")
    return parser.parse_args(args)

def main():
    args = parse_args(sys.argv[1:])
    spark = spark_session(args.job_name)
    try:
        ingest_to_bronze(
            spark=spark,
            run_id=args.run_id,
            source_path=args.source_path,
            format=args.format,
            target_table=args.target_table,
            quarantine_table=args.quarantine_table,
            error_threshold=args.error_threshold
        )
    finally:
        spark.stop()

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Commit**

```bash
git add pipelines/src/jobs/ingest_bronze.py
git commit -m "feat(pipelines): add spark submit job for bronze ingestion"
```

---

### Task 3: Update Architecture Documentation

**Files:**
- Modify: `docs/project/LAKEHOUSE_DESIGN_PLAN.md`

- [ ] **Step 1: Update Bronze layer documentation**

Update the `3.2. Bronze Layer` section in `docs/project/LAKEHOUSE_DESIGN_PLAN.md` to explicitly document the `Dead-Letter` strategy, the 1% error threshold (Circuit Breaker), and the decentralized quarantine routing (`lakehouse.quarantine.<table_name>_errors`). Also ensure the required metadata columns (`_run_id`, `_source_file`, `_ingested_at_utc`) are listed.

- [ ] **Step 2: Commit**

```bash
git add docs/project/LAKEHOUSE_DESIGN_PLAN.md
git commit -m "docs: document bronze ingestion dead-letter strategy and metadata columns"
```
