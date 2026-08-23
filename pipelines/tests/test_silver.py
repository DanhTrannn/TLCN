import shutil
from dataclasses import dataclass

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
from lakehouse.silver import MergeResult, merge_oltp_table


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
    data = [
        (1, "a@test.com", "Alice", "0901", "customer", "active", "2026-01-01", "2026-08-01", "2026-08-15", "run-1"),
        (2, "b@test.com", "Bob", "0902", "customer", "active", "2026-01-01", "2026-08-01", "2026-08-15", "run-1"),
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
        (1, "a_new@test.com", "Alice Updated", "0901", "customer", "active", "2026-01-01", "2026-08-16", "2026-08-16", "run-2"),
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
        (1, "a_new@test.com", "Alice Updated", "0901", "customer", "active", "2026-01-01", "2026-08-16", "2026-08-16", "run-2"),
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
    data = [
        (1, 1, "SKU-001", "M", "RED", -1000, "true", "2026-01-01", "2026-08-01", "2026-08-15", "run-1"),
        (2, 1, "SKU-002", "L", "BLUE", 50000, "true", "2026-01-01", "2026-08-01", "2026-08-15", "run-1"),
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
        (1, 1, "SKU-001", "M", "RED", 50000, "true", "2026-01-01", "2026-08-01", "2026-08-15", "run-1"),
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
