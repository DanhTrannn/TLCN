import shutil
from datetime import datetime

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
from lakehouse.logs_silver import ingest_logs_to_silver, ensure_logs_silver_tables


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
        StructField("schema", StructType([
            StructField("name", StringType(), True),
            StructField("version", StringType(), True),
        ]), True),
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
    ts1 = datetime(2026, 8, 15, 10, 0, 0)
    ts2 = datetime(2026, 8, 15, 10, 0, 1)
    ingested = datetime(2026, 8, 15)
    data = [
        ("evt-1", ts1, ts2, "INFO", 9, {"name": "otlp", "version": "1.0"}, {"id": "req-1"}, None, None,
         {"name": "api", "version": "1.0", "environment": "prod", "instance_id": "i-1"},
         {"name": "GET", "category": "http", "kind": "server", "outcome": "OK", "duration_ns": 100000},
         {"request_method": "GET", "route": "/products", "status_code": 200},
         {"type": "anonymous", "key": None}, {"user_agent": "Mozilla/5.0"},
         {"action": "product_detail", "product_key": "p1", "variant_key": "v1", "search_query": None, "search_redacted": False, "filters": None},
         None, "observed", "run-1", "file-1.jsonl.gz", ingested),
        ("evt-1", ts1, ts2, "INFO", 9, {"name": "otlp", "version": "1.0"}, {"id": "req-1"}, None, None,
         {"name": "api", "version": "1.0", "environment": "prod", "instance_id": "i-1"},
         {"name": "GET", "category": "http", "kind": "server", "outcome": "OK", "duration_ns": 100000},
         {"request_method": "GET", "route": "/products", "status_code": 200},
         {"type": "anonymous", "key": None}, {"user_agent": "Mozilla/5.0"},
         {"action": "product_detail", "product_key": "p1", "variant_key": "v1", "search_query": None, "search_redacted": False, "filters": None},
         None, "observed", "run-1", "file-2.jsonl.gz", ingested),
    ]
    return spark.createDataFrame(data, schema)


def test_dedup_removes_duplicate_event_ids(spark, tmp_path):
    bronze_df = _make_logs_bronze_df(spark)
    target = str(tmp_path / "silver_logs")

    count = ingest_logs_to_silver(spark, bronze_df, "run-1", target, _write_format="parquet")

    assert count == 1
    df = spark.read.parquet(target)
    assert df.count() == 1


def test_empty_bronze_returns_zero(spark, tmp_path):
    schema = StructType([
        StructField("event_id", StringType(), False),
    ])
    empty_df = spark.createDataFrame([], schema)
    target = str(tmp_path / "silver_logs_empty")

    count = ingest_logs_to_silver(spark, empty_df, "run-1", target, _write_format="parquet")

    assert count == 0


def test_adds_metadata_columns(spark, tmp_path):
    bronze_df = _make_logs_bronze_df(spark).limit(1)
    target = str(tmp_path / "silver_logs_meta")

    ingest_logs_to_silver(spark, bronze_df, "run-1", target, _write_format="parquet")

    df = spark.read.parquet(target)
    assert "_silver_ingested_at" in df.columns
    assert "_source_bronze_run_id" in df.columns
