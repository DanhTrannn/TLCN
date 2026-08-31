import shutil
from dataclasses import dataclass
from datetime import datetime

import pytest

pyspark = pytest.importorskip("pyspark", reason="pyspark not installed")
pytestmark = pytest.mark.skipif(
    shutil.which("java") is None,
    reason="Java not found -- Spark tests require a JDK",
)

from pyspark.sql import SparkSession
from pyspark.sql.types import (
    IntegerType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)
from lakehouse.oltp.silver import MergeResult, merge_oltp_table


@pytest.fixture(scope="session")
def spark():
    return SparkSession.builder.master("local[1]").appName("test-silver").getOrCreate()


def _make_bronze_df(spark):
    schema = StructType([
        StructField("customer_id", IntegerType(), False),
        StructField("email_normalized", StringType(), True),
        StructField("full_name", StringType(), True),
        StructField("phone", StringType(), True),
        StructField("role", StringType(), False),
        StructField("status", StringType(), False),
        StructField("created_at", TimestampType(), False),
        StructField("updated_at", TimestampType(), False),
        StructField("_ingested_at_utc", TimestampType(), False),
        StructField("_run_id", StringType(), False),
    ])
    ts = datetime(2026, 1, 1)
    updated_at = datetime(2026, 8, 1)
    ingested = datetime(2026, 8, 15)
    data = [
        (1, "a@test.com", "Alice", "0901", "customer", "active", ts, updated_at, ingested, "run-1"),
        (2, "b@test.com", "Bob", "0902", "customer", "active", ts, updated_at, ingested, "run-1"),
    ]
    return spark.createDataFrame(data, schema)


def test_merge_inserts_new_records(spark, tmp_path):
    bronze_df = _make_bronze_df(spark)
    target = str(tmp_path / "silver_customers")

    @dataclass
    class MockTable:
        name: str
        pk: str
        cursor_field: str
        mutability: str
        silver_table: str
        pseudonymize: tuple = ()

    table = MockTable(
        name="customers", pk="customer_id", cursor_field="updated_at",
        mutability="mutable", silver_table="silver_customers",
        pseudonymize=("email_normalized", "phone", "full_name"),
    )

    result = merge_oltp_table(
        spark=spark, table=table, bronze_df=bronze_df,
        run_id="run-123", target_path=target, _write_format="parquet",
    )

    assert isinstance(result, MergeResult)
    assert result.inserted == 2
    assert result.updated == 0

    df = spark.read.parquet(target)
    assert df.count() == 2
    assert "_silver_ingested_at" in df.columns
    assert "_source_bronze_run_id" in df.columns


def test_merge_upserts_existing_records(spark, tmp_path):
    bronze_df = _make_bronze_df(spark)
    target = str(tmp_path / "silver_customers")

    @dataclass
    class MockTable:
        name: str
        pk: str
        cursor_field: str
        mutability: str
        silver_table: str
        pseudonymize: tuple = ()

    table = MockTable(
        name="customers", pk="customer_id", cursor_field="updated_at",
        mutability="mutable", silver_table="silver_customers",
        pseudonymize=("email_normalized", "phone", "full_name"),
    )

    merge_oltp_table(
        spark=spark, table=table, bronze_df=bronze_df,
        run_id="run-1", target_path=target, _write_format="parquet",
    )

    updated_data = [
        (1, "a_new@test.com", "Alice Updated", "0901", "customer", "active", datetime(2026, 1, 1), datetime(2026, 8, 16), datetime(2026, 8, 16), "run-2"),
    ]
    schema = bronze_df.schema
    updated_df = spark.createDataFrame(updated_data, schema)

    result = merge_oltp_table(
        spark=spark, table=table, bronze_df=updated_df,
        run_id="run-2", target_path=target, _write_format="parquet",
    )

    assert result.inserted == 0
    assert result.updated == 1

    df = spark.read.parquet(target)
    assert df.count() == 2


def test_merge_preserves_unchanged_columns(spark, tmp_path):
    bronze_df = _make_bronze_df(spark)
    target = str(tmp_path / "silver_customers")

    @dataclass
    class MockTable:
        name: str
        pk: str
        cursor_field: str
        mutability: str
        silver_table: str
        pseudonymize: tuple = ()

    table = MockTable(
        name="customers", pk="customer_id", cursor_field="updated_at",
        mutability="mutable", silver_table="silver_customers",
        pseudonymize=("email_normalized", "phone", "full_name"),
    )

    merge_oltp_table(
        spark=spark, table=table, bronze_df=bronze_df,
        run_id="run-1", target_path=target, _write_format="parquet",
    )

    df_before = spark.read.parquet(target)
    row_before = df_before.filter("customer_id = 2").collect()[0]

    updated_data = [
        (1, "a_new@test.com", "Alice Updated", "0901", "customer", "active", datetime(2026, 1, 1), datetime(2026, 8, 16), datetime(2026, 8, 16), "run-2"),
    ]
    schema = bronze_df.schema
    updated_df = spark.createDataFrame(updated_data, schema)

    merge_oltp_table(
        spark=spark, table=table, bronze_df=updated_df,
        run_id="run-2", target_path=target, _write_format="parquet",
    )

    df_after = spark.read.parquet(target)
    row_after = df_after.filter("customer_id = 2").collect()[0]
    assert row_after["email_normalized_pseudonymized"] == row_before["email_normalized_pseudonymized"]


def test_merge_result_dataclass():
    result = MergeResult(inserted=5, updated=3, quarantined=1)
    assert result.inserted == 5
    assert result.updated == 3
    assert result.quarantined == 1


def test_negative_price_routes_to_quarantine(spark, tmp_path):
    schema = StructType([
        StructField("variant_id", IntegerType(), False),
        StructField("product_id", IntegerType(), False),
        StructField("sku", StringType(), False),
        StructField("size_code", StringType(), True),
        StructField("color_code", StringType(), True),
        StructField("price_vnd", IntegerType(), False),
        StructField("is_active", StringType(), False),
        StructField("created_at", TimestampType(), False),
        StructField("updated_at", TimestampType(), False),
        StructField("_ingested_at_utc", TimestampType(), False),
        StructField("_run_id", StringType(), False),
    ])
    ts = datetime(2026, 1, 1)
    data = [
        (1, 1, "SKU-001", "M", "RED", -1000, "true", ts, datetime(2026, 8, 1), datetime(2026, 8, 15), "run-1"),
        (2, 1, "SKU-002", "L", "BLUE", 50000, "true", ts, datetime(2026, 8, 1), datetime(2026, 8, 15), "run-1"),
    ]
    bronze_df = spark.createDataFrame(data, schema)
    target = str(tmp_path / "silver_product_variants")

    @dataclass
    class MockTable:
        name: str
        pk: str
        cursor_field: str
        mutability: str
        silver_table: str
        pseudonymize: tuple = ()

    table = MockTable(
        name="product_variants", pk="variant_id", cursor_field="updated_at",
        mutability="mutable", silver_table="silver_product_variants",
    )

    result = merge_oltp_table(
        spark=spark, table=table, bronze_df=bronze_df,
        run_id="run-1", target_path=target, _write_format="parquet",
    )

    assert result.quarantined == 1
    assert result.inserted == 1

    df = spark.read.parquet(target)
    assert df.count() == 1
    assert df.filter("variant_id = 2").count() == 1


def test_valid_price_passes(spark, tmp_path):
    schema = StructType([
        StructField("variant_id", IntegerType(), False),
        StructField("product_id", IntegerType(), False),
        StructField("sku", StringType(), False),
        StructField("size_code", StringType(), True),
        StructField("color_code", StringType(), True),
        StructField("price_vnd", IntegerType(), False),
        StructField("is_active", StringType(), False),
        StructField("created_at", TimestampType(), False),
        StructField("updated_at", TimestampType(), False),
        StructField("_ingested_at_utc", TimestampType(), False),
        StructField("_run_id", StringType(), False),
    ])
    data = [
        (1, 1, "SKU-001", "M", "RED", 50000, "true", datetime(2026, 1, 1), datetime(2026, 8, 1), datetime(2026, 8, 15), "run-1"),
    ]
    bronze_df = spark.createDataFrame(data, schema)
    target = str(tmp_path / "silver_product_variants")

    @dataclass
    class MockTable:
        name: str
        pk: str
        cursor_field: str
        mutability: str
        silver_table: str
        pseudonymize: tuple = ()

    table = MockTable(
        name="product_variants", pk="variant_id", cursor_field="updated_at",
        mutability="mutable", silver_table="silver_product_variants",
    )

    result = merge_oltp_table(
        spark=spark, table=table, bronze_df=bronze_df,
        run_id="run-1", target_path=target, _write_format="parquet",
    )

    assert result.quarantined == 0
    assert result.inserted == 1


def test_full_oltp_pipeline_roundtrip(spark, tmp_path):
    schema = StructType([
        StructField("customer_id", IntegerType(), False),
        StructField("email_normalized", StringType(), True),
        StructField("full_name", StringType(), True),
        StructField("phone", StringType(), True),
        StructField("role", StringType(), False),
        StructField("status", StringType(), False),
        StructField("created_at", TimestampType(), False),
        StructField("updated_at", TimestampType(), False),
        StructField("_ingested_at_utc", TimestampType(), False),
        StructField("_run_id", StringType(), False),
    ])
    ts = datetime(2026, 1, 1)
    data = [
        (1, "alice@test.com", "Alice", "0901", "customer", "active", ts, datetime(2026, 8, 1), datetime(2026, 8, 15), "run-1"),
        (2, "bob@test.com", "Bob", "0902", "customer", "active", ts, datetime(2026, 8, 1), datetime(2026, 8, 15), "run-1"),
    ]
    bronze_df = spark.createDataFrame(data, schema)
    target = str(tmp_path / "silver_customers")

    @dataclass
    class MockTable:
        name: str
        pk: str
        cursor_field: str
        mutability: str
        silver_table: str
        pseudonymize: tuple = ()

    table = MockTable(
        name="customers", pk="customer_id", cursor_field="updated_at",
        mutability="mutable", silver_table="silver_customers",
        pseudonymize=("email_normalized", "phone", "full_name"),
    )

    result1 = merge_oltp_table(
        spark=spark, table=table, bronze_df=bronze_df,
        run_id="run-1", target_path=target, _write_format="parquet",
    )
    assert result1.inserted == 2

    updated_data = [
        (1, "alice_new@test.com", "Alice New", "0901", "customer", "active", ts, datetime(2026, 8, 16), datetime(2026, 8, 16), "run-2"),
    ]
    updated_df = spark.createDataFrame(updated_data, schema)

    result2 = merge_oltp_table(
        spark=spark, table=table, bronze_df=updated_df,
        run_id="run-2", target_path=target, _write_format="parquet",
    )
    assert result2.updated == 1
    assert result2.inserted == 0

    df = spark.read.parquet(target)
    assert df.count() == 2
    alice = df.filter("customer_id = 1").collect()[0]
    assert alice["email_normalized_pseudonymized"] is not None
    assert alice["_source_bronze_run_id"] == "run-2"


def test_quarantine_routes_violations(spark, tmp_path):
    import os
    os.environ["SILVER_PSEUDONYMIZE_SALT"] = "test-salt"
    try:
        schema = StructType([
            StructField("variant_id", IntegerType(), False),
            StructField("product_id", IntegerType(), False),
            StructField("sku", StringType(), False),
            StructField("size_code", StringType(), True),
            StructField("color_code", StringType(), True),
            StructField("price_vnd", IntegerType(), False),
            StructField("is_active", StringType(), False),
            StructField("created_at", TimestampType(), False),
            StructField("updated_at", TimestampType(), False),
            StructField("_ingested_at_utc", TimestampType(), False),
            StructField("_run_id", StringType(), False),
        ])
        ts = datetime(2026, 1, 1)
        data = [
            (1, 1, "SKU-001", "M", "RED", -500, "true", ts, datetime(2026, 8, 1), datetime(2026, 8, 15), "run-1"),
            (2, 1, "SKU-002", "L", "BLUE", 50000, "true", ts, datetime(2026, 8, 1), datetime(2026, 8, 15), "run-1"),
        ]

        bronze_df = spark.createDataFrame(data, schema)
        target = str(tmp_path / "silver_variants")

        @dataclass
        class MockTable:
            name: str
            pk: str
            cursor_field: str
            mutability: str
            silver_table: str
            pseudonymize: tuple = ()

        table = MockTable(
            name="product_variants", pk="variant_id", cursor_field="updated_at",
            mutability="mutable", silver_table="silver_product_variants",
        )

        result = merge_oltp_table(
            spark=spark, table=table, bronze_df=bronze_df,
            run_id="run-1", target_path=target, _write_format="parquet",
        )

        assert result.quarantined == 1
        assert result.inserted == 1
        df = spark.read.parquet(target)
        assert df.count() == 1
        assert df.collect()[0]["variant_id"] == 2
    finally:
        os.environ.pop("SILVER_PSEUDONYMIZE_SALT", None)
