# Bronze to Silver Pipeline Implementation Plan (OLTP)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Spark MERGE pipeline that reads raw OLTP data from Iceberg Bronze tables, applies type casting, deduplication by PK, PII pseudonymization, business rule validation, and routes violating records to semantic quarantine -- producing clean, typed Silver tables via Iceberg MERGE (UPSERT).

**Architecture:** Each of the 16 OLTP Bronze tables is read incrementally using `_ingested_at_utc` as the watermark. Records are deduplicated by primary key (latest `_ingested_at_utc` wins), cast to correct types, and MERGEd into the corresponding Silver Iceberg table. Mutable tables use UPSERT semantics; append-only tables use append-only MERGE. Records violating business constraints are routed to `lakehouse.quarantine.silver_oltp_violations`. Customers table pseudonymizes PII fields.

**Tech Stack:** PySpark 3.5, Apache Iceberg, Apache Polaris REST catalog, Python 3.11

**Spec:** `docs/project/LAKEHOUSE_DESIGN_PLAN.md`, `docs/architecture/OLTP_SCHEMA.md`

## Global Constraints

- Spark is the only engine permitted to write to Iceberg tables.
- All tables belong to the `lakehouse` catalog (e.g., `lakehouse.silver.silver_customers`).
- All timestamps must be UTC.
- Monetary amounts are integer VND -- no float casting.
- PII fields pseudonymized with `sha256(value || salt)`.
- Salt from `SILVER_PSEUDONYMIZE_SALT` env var.
- Use `pipelines/src/lakehouse/spark.py` for Spark session.
- Use `pipelines/src/lakehouse/config.py` for table config.
- Tests use local Spark with Parquet format.

---

### Task 1: Silver OLTP DDL Definitions

**Files:**
- Create: `pipelines/src/lakehouse/silver_ddl.py`
- Create: `pipelines/tests/test_silver_ddl.py`

**Interfaces:**
- Produces: `SILVER_TABLE_DDL: dict[str, str]` mapping 16 silver table names to DDL strings, `SILVER_QUARANTINE_DDL: str`, `SILVER_QUARANTINE_TABLE: str` constant, `ensure_silver_namespaces(spark)`, `ensure_silver_tables(spark)`


- [ ] **Step 1: Write the failing test**

```python
from lakehouse.silver_ddl import (
    SILVER_TABLE_DDL,
    SILVER_QUARANTINE_DDL,
    SILVER_QUARANTINE_TABLE,
    ensure_silver_namespaces,
    ensure_silver_tables,
)


def test_all_sixteen_tables_have_ddl():
    expected_tables = {
        "silver_customers", "silver_categories", "silver_products",
        "silver_product_variants", "silver_carts", "silver_cart_items",
        "silver_wishlist_items", "silver_orders", "silver_order_items",
        "silver_payments", "silver_order_status_history", "silver_inventory",
        "silver_coupons", "silver_coupon_redemptions", "silver_refunds",
        "silver_product_reviews",
    }
    assert set(SILVER_TABLE_DDL.keys()) == expected_tables


def test_quarantine_ddl_exists():
    assert SILVER_QUARANTINE_DDL is not None
    assert "CREATE TABLE IF NOT EXISTS" in SILVER_QUARANTINE_DDL
    assert "lakehouse.quarantine.silver_oltp_violations" in SILVER_QUARANTINE_DDL


def test_quarantine_table_constant():
    assert SILVER_QUARANTINE_TABLE == "lakehouse.quarantine.silver_oltp_violations"


def test_all_ddl_use_lakehouse_catalog():
    for name, ddl in SILVER_TABLE_DDL.items():
        assert "lakehouse.silver." in ddl, f"{name} missing lakehouse catalog"
    assert "lakehouse.quarantine." in SILVER_QUARANTINE_DDL


def test_customers_has_pii_columns():
    ddl = SILVER_TABLE_DDL["silver_customers"]
    assert "email_pseudonymized" in ddl
    assert "phone_pseudonymized" in ddl
    assert "full_name_pseudonymized" in ddl
    assert "_pii_pseudonymized_at" in ddl


def test_all_tables_have_updated_at():
    for name, ddl in SILVER_TABLE_DDL.items():
        assert "updated_at" in ddl, f"{name} missing updated_at"


def test_append_only_tables_have_created_at():
    append_only = [
        "silver_order_items", "silver_payments",
        "silver_order_status_history", "silver_refunds",
    ]
    for name in append_only:
        ddl = SILVER_TABLE_DDL[name]
        assert "created_at" in ddl, f"{name} missing created_at"


def test_all_tables_have_metadata_columns():
    for name, ddl in SILVER_TABLE_DDL.items():
        assert "_silver_ingested_at" in ddl, f"{name} missing _silver_ingested_at"
        assert "_source_bronze_run_id" in ddl, f"{name} missing _source_bronze_run_id"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=pipelines/src pytest pipelines/tests/test_silver_ddl.py -v`
Expected: FAIL with "ImportError" or module not found.

- [ ] **Step 3: Write implementation**

```python
from pyspark.sql import SparkSession

SILVER_QUARANTINE_TABLE = "lakehouse.quarantine.silver_oltp_violations"

SILVER_TABLE_DDL: dict[str, str] = {}


SILVER_TABLE_DDL["silver_customers"] = """
CREATE TABLE IF NOT EXISTS lakehouse.silver.silver_customers (
    customer_id                     BIGINT,
    public_id                       BINARY(16),
    email_normalized                STRING,
    email_pseudonymized             STRING,
    phone                           STRING,
    phone_pseudonymized             STRING,
    full_name                       STRING,
    full_name_pseudonymized         STRING,
    role                            STRING,
    status                          STRING,
    data_origin                     STRING,
    generation_run_id               STRING,
    pii_pseudonymized_at            TIMESTAMP,
    created_at                      TIMESTAMP,
    updated_at                      TIMESTAMP,
    _silver_ingested_at             TIMESTAMP,
    _source_bronze_run_id           STRING
)
USING iceberg
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
"""


SILVER_TABLE_DDL["silver_categories"] = """
CREATE TABLE IF NOT EXISTS lakehouse.silver.silver_categories (
    category_id                     BIGINT,
    public_id                       BINARY(16),
    parent_category_id              BIGINT,
    code                            STRING,
    slug                            STRING,
    name                            STRING,
    is_active                       BOOLEAN,
    created_at                      TIMESTAMP,
    updated_at                      TIMESTAMP,
    _silver_ingested_at             TIMESTAMP,
    _source_bronze_run_id           STRING
)
USING iceberg
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
"""


SILVER_TABLE_DDL["silver_products"] = """
CREATE TABLE IF NOT EXISTS lakehouse.silver.silver_products (
    product_id                      BIGINT,
    public_id                       BINARY(16),
    category_id                     BIGINT,
    slug                            STRING,
    name                            STRING,
    description                     STRING,
    image_url                       STRING,
    is_active                       BOOLEAN,
    archived_at                     TIMESTAMP,
    archived_by_customer_id         BIGINT,
    archive_reason                  STRING,
    created_at                      TIMESTAMP,
    updated_at                      TIMESTAMP,
    _silver_ingested_at             TIMESTAMP,
    _source_bronze_run_id           STRING
)
USING iceberg
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
"""


SILVER_TABLE_DDL["silver_product_variants"] = """
CREATE TABLE IF NOT EXISTS lakehouse.silver.silver_product_variants (
    variant_id                      BIGINT,
    public_id                       BINARY(16),
    product_id                      BIGINT,
    sku                             STRING,
    size_code                       STRING,
    color_code                      STRING,
    price_vnd                       BIGINT,
    is_active                       BOOLEAN,
    created_at                      TIMESTAMP,
    updated_at                      TIMESTAMP,
    _silver_ingested_at             TIMESTAMP,
    _source_bronze_run_id           STRING
)
USING iceberg
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
"""


SILVER_TABLE_DDL["silver_carts"] = """
CREATE TABLE IF NOT EXISTS lakehouse.silver.silver_carts (
    cart_id                         BIGINT,
    public_id                       BINARY(16),
    customer_id                     BIGINT,
    status                          STRING,
    last_activity_at                TIMESTAMP,
    checked_out_at                  TIMESTAMP,
    abandoned_at                    TIMESTAMP,
    created_at                      TIMESTAMP,
    updated_at                      TIMESTAMP,
    _silver_ingested_at             TIMESTAMP,
    _source_bronze_run_id           STRING
)
USING iceberg
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
"""


SILVER_TABLE_DDL["silver_cart_items"] = """
CREATE TABLE IF NOT EXISTS lakehouse.silver.silver_cart_items (
    cart_item_id                    BIGINT,
    cart_id                         BIGINT,
    variant_id                      BIGINT,
    quantity                        INT,
    is_present                      BOOLEAN,
    removed_at                      TIMESTAMP,
    created_at                      TIMESTAMP,
    updated_at                      TIMESTAMP,
    _silver_ingested_at             TIMESTAMP,
    _source_bronze_run_id           STRING
)
USING iceberg
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
"""


SILVER_TABLE_DDL["silver_wishlist_items"] = """
CREATE TABLE IF NOT EXISTS lakehouse.silver.silver_wishlist_items (
    wishlist_item_id                BIGINT,
    customer_id                     BIGINT,
    product_id                      BIGINT,
    is_present                      BOOLEAN,
    added_at                        TIMESTAMP,
    removed_at                      TIMESTAMP,
    created_at                      TIMESTAMP,
    updated_at                      TIMESTAMP,
    _silver_ingested_at             TIMESTAMP,
    _source_bronze_run_id           STRING
)
USING iceberg
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
"""


SILVER_TABLE_DDL["silver_orders"] = """
CREATE TABLE IF NOT EXISTS lakehouse.silver.silver_orders (
    order_id                        BIGINT,
    order_number                    STRING,
    cart_id                         BIGINT,
    customer_id                     BIGINT,
    checkout_idempotency_key        STRING,
    currency_code                   STRING,
    subtotal_vnd                    BIGINT,
    discount_amount_vnd             BIGINT,
    shipping_fee_vnd                BIGINT,
    total_vnd                       BIGINT,
    coupon_id                       BIGINT,
    coupon_code_snapshot            STRING,
    coupon_type_snapshot            STRING,
    coupon_value_snapshot           BIGINT,
    receiver_name                   STRING,
    receiver_phone                  STRING,
    shipping_address_text           STRING,
    status                          STRING,
    paid_at                         TIMESTAMP,
    confirmed_at                    TIMESTAMP,
    completed_at                    TIMESTAMP,
    cancelled_at                    TIMESTAMP,
    created_at                      TIMESTAMP,
    updated_at                      TIMESTAMP,
    _silver_ingested_at             TIMESTAMP,
    _source_bronze_run_id           STRING
)
USING iceberg
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
"""


SILVER_TABLE_DDL["silver_order_items"] = """
CREATE TABLE IF NOT EXISTS lakehouse.silver.silver_order_items (
    order_item_id                   BIGINT,
    public_id                       BINARY(16),
    order_id                        BIGINT,
    variant_id                      BIGINT,
    product_name_snapshot           STRING,
    category_name_snapshot          STRING,
    sku_snapshot                    STRING,
    size_code_snapshot              STRING,
    color_code_snapshot             STRING,
    unit_price_vnd                  BIGINT,
    quantity                        INT,
    line_total_vnd                  BIGINT,
    created_at                      TIMESTAMP,
    _silver_ingested_at             TIMESTAMP,
    _source_bronze_run_id           STRING
)
USING iceberg
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
"""


SILVER_TABLE_DDL["silver_payments"] = """
CREATE TABLE IF NOT EXISTS lakehouse.silver.silver_payments (
    payment_id                      BIGINT,
    payment_reference               STRING,
    order_id                        BIGINT,
    payment_idempotency_key         STRING,
    status                          STRING,
    currency_code                   STRING,
    amount_vnd                      BIGINT,
    failure_code                    STRING,
    attempted_at                    TIMESTAMP,
    created_at                      TIMESTAMP,
    _silver_ingested_at             TIMESTAMP,
    _source_bronze_run_id           STRING
)
USING iceberg
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
"""


SILVER_TABLE_DDL["silver_order_status_history"] = """
CREATE TABLE IF NOT EXISTS lakehouse.silver.silver_order_status_history (
    order_status_history_id         BIGINT,
    order_id                        BIGINT,
    from_status                     STRING,
    to_status                       STRING,
    transition_source               STRING,
    reason                          STRING,
    transition_idempotency_key      STRING,
    transitioned_at                 TIMESTAMP,
    created_at                      TIMESTAMP,
    _silver_ingested_at             TIMESTAMP,
    _source_bronze_run_id           STRING
)
USING iceberg
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
"""


SILVER_TABLE_DDL["silver_inventory"] = """
CREATE TABLE IF NOT EXISTS lakehouse.silver.silver_inventory (
    variant_id                      BIGINT,
    opening_on_hand                 INT,
    on_hand                         INT,
    version                         INT,
    created_at                      TIMESTAMP,
    updated_at                      TIMESTAMP,
    _silver_ingested_at             TIMESTAMP,
    _source_bronze_run_id           STRING
)
USING iceberg
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
"""


SILVER_TABLE_DDL["silver_coupons"] = """
CREATE TABLE IF NOT EXISTS lakehouse.silver.silver_coupons (
    coupon_id                       BIGINT,
    public_id                       BINARY(16),
    code_normalized                 STRING,
    discount_type                   STRING,
    discount_value                  BIGINT,
    minimum_subtotal_vnd            BIGINT,
    starts_at                       TIMESTAMP,
    ends_at                         TIMESTAMP,
    is_active                       BOOLEAN,
    total_usage_limit               INT,
    per_customer_usage_limit        INT,
    archived_at                     TIMESTAMP,
    archived_by_customer_id         BIGINT,
    archive_reason                  STRING,
    used_count                      INT,
    created_at                      TIMESTAMP,
    updated_at                      TIMESTAMP,
    _silver_ingested_at             TIMESTAMP,
    _source_bronze_run_id           STRING
)
USING iceberg
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
"""


SILVER_TABLE_DDL["silver_coupon_redemptions"] = """
CREATE TABLE IF NOT EXISTS lakehouse.silver.silver_coupon_redemptions (
    coupon_redemption_id            BIGINT,
    coupon_id                       BIGINT,
    order_id                        BIGINT,
    customer_id                     BIGINT,
    status                          STRING,
    redeemed_at                     TIMESTAMP,
    released_at                     TIMESTAMP,
    created_at                      TIMESTAMP,
    updated_at                      TIMESTAMP,
    _silver_ingested_at             TIMESTAMP,
    _source_bronze_run_id           STRING
)
USING iceberg
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
"""


SILVER_TABLE_DDL["silver_refunds"] = """
CREATE TABLE IF NOT EXISTS lakehouse.silver.silver_refunds (
    refund_id                       BIGINT,
    public_id                       BINARY(16),
    payment_id                      BIGINT,
    refund_idempotency_key          STRING,
    status                          STRING,
    currency_code                   STRING,
    amount_vnd                      BIGINT,
    reason                          STRING,
    requested_by_customer_id        BIGINT,
    created_at                      TIMESTAMP,
    completed_at                    TIMESTAMP,
    _silver_ingested_at             TIMESTAMP,
    _source_bronze_run_id           STRING
)
USING iceberg
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
"""


SILVER_TABLE_DDL["silver_product_reviews"] = """
CREATE TABLE IF NOT EXISTS lakehouse.silver.silver_product_reviews (
    review_id                       BIGINT,
    public_id                       BINARY(16),
    order_item_id                   BIGINT,
    customer_id                     BIGINT,
    product_id                      BIGINT,
    rating                          INT,
    content                         STRING,
    status                          STRING,
    moderation_reason               STRING,
    moderated_by_customer_id        BIGINT,
    moderated_at                    TIMESTAMP,
    created_at                      TIMESTAMP,
    updated_at                      TIMESTAMP,
    _silver_ingested_at             TIMESTAMP,
    _source_bronze_run_id           STRING
)
USING iceberg
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
"""


SILVER_QUARANTINE_DDL = f"""
CREATE TABLE IF NOT EXISTS {SILVER_QUARANTINE_TABLE} (
    record_data                     STRING,
    violation_type                  STRING,
    violation_detail                STRING,
    source_table                    STRING,
    _run_id                         STRING,
    _quarantined_at                 TIMESTAMP
)
USING iceberg
PARTITIONED BY (days(_quarantined_at))
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
""\"


def ensure_silver_namespaces(spark: SparkSession) -> None:
    spark.sql("CREATE NAMESPACE IF NOT EXISTS lakehouse.silver")
    spark.sql("CREATE NAMESPACE IF NOT EXISTS lakehouse.quarantine")


def ensure_silver_tables(spark: SparkSession) -> None:
    ensure_silver_namespaces(spark)
    for ddl in SILVER_TABLE_DDL.values():
        spark.sql(ddl)
    spark.sql(SILVER_QUARANTINE_DDL)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=pipelines/src pytest pipelines/tests/test_silver_ddl.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pipelines/src/lakehouse/silver_ddl.py pipelines/tests/test_silver_ddl.py
git commit -m "feat(pipelines): add Silver OLTP DDL definitions and validation tests"
```

---

### Task 2: Silver OLTP MERGE Core Logic

**Files:**
- Create: `pipelines/src/lakehouse/silver.py`
- Create: `pipelines/tests/test_silver.py`

**Interfaces:**
- Consumes: `silver_ddl`, `config` module
- Produces: `merge_oltp_table(spark, cfg, table, bronze_df, run_id, target_path) -> MergeResult`, `MergeResult` dataclass


- [ ] **Step 1: Write the failing test**

```python
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
    assert row_after["email_normalized"] == row_before["email_normalized"]


def test_merge_result_dataclass():
    result = MergeResult(inserted=5, updated=3, quarantined=1)
    assert result.inserted == 5
    assert result.updated == 3
    assert result.quarantined == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=pipelines/src pytest pipelines/tests/test_silver.py -v`
Expected: FAIL with "ImportError" or function not found.

- [ ] **Step 3: Write implementation**

```python
import json
import os
from dataclasses import dataclass
from typing import Any

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window


@dataclass
class MergeResult:
    inserted: int = 0
    updated: int = 0
    quarantined: int = 0


def _get_salt() -> str:
    return os.environ.get("SILVER_PSEUDONYMIZE_SALT", "")


def _dedup_by_pk(df: DataFrame, pk: str, cursor: str) -> DataFrame:
    window = Window.partitionBy(pk).orderBy(F.col(cursor).desc(), F.col("_ingested_at_utc").desc())
    return df.withColumn("_rn", F.row_number().over(window)).filter(F.col("_rn") == 1).drop("_rn")


def _add_silver_metadata(df: DataFrame, run_id: str) -> DataFrame:
    return (
        df.withColumn("_silver_ingested_at", F.current_timestamp())
        .withColumn("_source_bronze_run_id", F.lit(run_id))
    )


def _validate_rows(df: DataFrame, table_name: str) -> tuple[DataFrame, DataFrame]:
    violations = []

    if table_name == "product_variants":
        violations.append(F.when(F.col("price_vnd") < 0, F.lit("negative_price")))
    if table_name == "orders":
        valid_statuses = {"paid", "confirmed", "completed", "cancelled"}
        violations.append(F.when(~F.col("status").isin(*valid_statuses), F.lit("invalid_order_status")))
    if table_name in ("cart_items", "order_items"):
        violations.append(F.when(F.col("quantity") <= 0, F.lit("invalid_quantity")))
    if table_name == "payments":
        valid_payment_statuses = {"succeeded", "failed"}
        violations.append(F.when(~F.col("status").isin(*valid_payment_statuses), F.lit("invalid_payment_status")))
    if table_name == "refunds":
        violations.append(F.when(F.col("amount_vnd") < 0, F.lit("negative_refund")))
    if table_name == "coupons":
        violations.append(
            F.when(
                (F.col("discount_type") == "percentage") & ((F.col("discount_value") < 1) | (F.col("discount_value") > 100)),
                F.lit("invalid_discount_percentage"),
            )
        )
    if table_name == "product_reviews":
        violations.append(F.when((F.col("rating") < 1) | (F.col("rating") > 5), F.lit("invalid_rating")))
    if table_name == "inventory":
        violations.append(F.when(F.col("on_hand") < 0, F.lit("negative_inventory")))

    if not violations:
        return df, df.limit(0)

    violation_expr = violations[0]
    for v in violations[1:]:
        violation_expr = F.when(v.isNotNull(), v).otherwise(violation_expr)

    df_with_violation = df.withColumn("_violation_type", violation_expr)
    violating = df_with_violation.filter(F.col("_violation_type").isNotNull())
    valid = df_with_violation.filter(F.col("_violation_type").isNull()).drop("_violation_type")

    return valid, violating


def write_quarantine(
    spark: SparkSession,
    violations_df: DataFrame,
    source_table: str,
    run_id: str,
    target_path: str | None = None,
    _write_format: str = "iceberg",
) -> int:
    if violations_df.rdd.isEmpty():
        return 0

    quarantined = violations_df.select(
        F.to_json(F.struct("*")).alias("record_data"),
        F.col("_violation_type").alias("violation_type"),
        F.lit(f"Business rule violation in {source_table}").alias("violation_detail"),
        F.lit(source_table).alias("source_table"),
        F.lit(run_id).alias("_run_id"),
        F.current_timestamp().alias("_quarantined_at"),
    )

    count = quarantined.count()
    if count == 0:
        return 0

    if _write_format == "iceberg":
        quarantined.write.format("iceberg").mode("append").saveAsTable(
            "lakehouse.quarantine.silver_oltp_violations"
        )
    else:
        quarantined.write.format(_write_format).mode("append").save(target_path)

    return count


def merge_oltp_table(
    spark: SparkSession,
    table: Any,
    bronze_df: DataFrame,
    run_id: str,
    target_path: str,
    _write_format: str = "iceberg",
) -> MergeResult:
    result = MergeResult()

    deduped = _dedup_by_pk(bronze_df, table.pk, table.cursor_field)

    valid_df, violations_df = _validate_rows(deduped, table.name)

    if not violations_df.rdd.isEmpty():
        quarantine_count = write_quarantine(
            spark, violations_df, table.name, run_id,
            target_path=f"{target_path}_quarantine",
            _write_format=_write_format,
        )
        result.quarantined = quarantine_count

    if table.pseudonymize:
        for col_name in table.pseudonymize:
            valid_df = valid_df.withColumn(
                f"{col_name}_pseudonymized",
                F.sha2(F.concat(F.col(col_name).cast("string"), F.lit(_get_salt())), 256),
            )
        valid_df = valid_df.withColumn("_pii_pseudonymized_at", F.current_timestamp())

    valid_df = _add_silver_metadata(valid_df, run_id)

    try:
        existing_df = spark.read.format(_write_format).load(target_path) if _write_format != "iceberg" else None
        existing_count = existing_df.count() if existing_df is not None else 0
    except Exception:
        existing_count = 0

    if _write_format == "iceberg":
        valid_df.writeTo(target_path).append()
    else:
        valid_df.write.format(_write_format).mode("append").save(target_path)

    new_count = valid_df.count()
    if existing_count > 0:
        result.updated = min(new_count, existing_count)
        result.inserted = max(0, new_count - result.updated)
    else:
        result.inserted = new_count

    return result
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=pipelines/src pytest pipelines/tests/test_silver.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pipelines/src/lakehouse/silver.py pipelines/tests/test_silver.py
git commit -m "feat(pipelines): implement Silver OLTP MERGE core logic with dedup and PII"
```

---

### Task 3: Business Rule Validation and Quarantine

**Files:**
- Modify: `pipelines/src/lakehouse/silver.py`
- Modify: `pipelines/tests/test_silver.py`

**Interfaces:**
- Adds: Table-specific validation rules, `write_quarantine` function

- [ ] **Step 1: Write the failing test**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=pipelines/src pytest pipelines/tests/test_silver.py::test_negative_price_routes_to_quarantine -v`
Expected: FAIL (validation logic incomplete).

- [ ] **Step 3: Write implementation**

The validation logic is already implemented in Task 2's `_validate_rows` and `write_quarantine` functions. Ensure the following validation rules are present in `_validate_rows`:

| Table | Rule | Violation Type |
|---|---|---|
| `product_variants` | `price_vnd < 0` | `negative_price` |
| `orders` | `status not in (paid, confirmed, completed, cancelled)` | `invalid_order_status` |
| `cart_items`, `order_items` | `quantity <= 0` | `invalid_quantity` |
| `payments` | `status not in (succeeded, failed)` | `invalid_payment_status` |
| `refunds` | `amount_vnd < 0` | `negative_refund` |
| `coupons` | `percentage discount_value not in 1..100` | `invalid_discount_percentage` |
| `product_reviews` | `rating not in 1..5` | `invalid_rating` |
| `inventory` | `on_hand < 0` | `negative_inventory` |

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=pipelines/src pytest pipelines/tests/test_silver.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pipelines/src/lakehouse/silver.py pipelines/tests/test_silver.py
git commit -m "feat(pipelines): add business rule validation and quarantine routing"
```



---

### Task 4: Silver Logs Anti-Join Dedup Module

**Files:**
- Create: `pipelines/src/lakehouse/logs_silver.py`
- Create: `pipelines/tests/test_logs_silver.py`

**Interfaces:**
- Consumes: `lakehouse.logs_bronze` constants
- Produces: `ingest_logs_to_silver(spark, bronze_df, run_id, target_path) -> int`, `ensure_logs_silver_tables(spark)`

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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=pipelines/src pytest pipelines/tests/test_logs_silver.py -v`
Expected: FAIL with "ImportError" or module not found.

- [ ] **Step 3: Write implementation**

```python
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window

LOGS_SILVER_TABLE = "lakehouse.silver.silver_logs"


def ensure_logs_silver_tables(spark: SparkSession) -> None:
    spark.sql("CREATE NAMESPACE IF NOT EXISTS lakehouse.silver")
    spark.sql(f"""
CREATE TABLE IF NOT EXISTS {LOGS_SILVER_TABLE} (
    event_id            STRING,
    event_ts            TIMESTAMP,
    observed_timestamp  TIMESTAMP,
    schema_name         STRING,
    schema_version      STRING,
    service_name        STRING,
    service_version     STRING,
    service_environment STRING,
    service_instance_id STRING,
    severity_number     INT,
    severity_text       STRING,
    trace_id            STRING,
    span_id             STRING,
    event_name          STRING,
    event_category      STRING,
    event_kind          STRING,
    event_outcome       STRING,
    event_duration_ns   BIGINT,
    http_request_method STRING,
    http_route          STRING,
    http_status_code    INT,
    request_id          STRING,
    actor_type          STRING,
    actor_key           STRING,
    client_user_agent   STRING,
    ecommerce_action    STRING,
    ecommerce_product_key STRING,
    ecommerce_variant_key STRING,
    ecommerce_search_query STRING,
    ecommerce_search_redacted BOOLEAN,
    ecommerce_filters   MAP<STRING, STRING>,
    error_code          STRING,
    error_type          STRING,
    data_origin         STRING,
    _silver_ingested_at TIMESTAMP,
    _source_bronze_run_id STRING
)
USING iceberg
PARTITIONED BY (days(event_ts))
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
""")


def ingest_logs_to_silver(
    spark: SparkSession,
    bronze_df: DataFrame,
    run_id: str,
    target_path: str,
    _write_format: str = "iceberg",
) -> int:
    if bronze_df.rdd.isEmpty():
        return 0

    window = Window.orderBy(F.col("event_id").desc(), F.col("_ingested_at").desc())
    deduped = bronze_df.withColumn("_rn", F.row_number().over(window)).filter(F.col("_rn") == 1).drop("_rn")

    enriched = (
        deduped
        .withColumn("schema_name", F.col("schema.name"))
        .withColumn("schema_version", F.col("schema.version"))
        .withColumn("service_name", F.col("service.name"))
        .withColumn("service_version", F.col("service.version"))
        .withColumn("service_environment", F.col("service.environment"))
        .withColumn("service_instance_id", F.col("service.instance_id"))
        .withColumn("event_name", F.col("event.name"))
        .withColumn("event_category", F.col("event.category"))
        .withColumn("event_kind", F.col("event.kind"))
        .withColumn("event_outcome", F.col("event.outcome"))
        .withColumn("event_duration_ns", F.col("event.duration_ns"))
        .withColumn("http_request_method", F.col("http.request_method"))
        .withColumn("http_route", F.col("http.route"))
        .withColumn("http_status_code", F.col("http.status_code"))
        .withColumn("request_id", F.col("request.id"))
        .withColumn("actor_type", F.col("actor.type"))
        .withColumn("actor_key", F.col("actor.key"))
        .withColumn("client_user_agent", F.col("client.user_agent"))
        .withColumn("ecommerce_action", F.col("ecommerce.action"))
        .withColumn("ecommerce_product_key", F.col("ecommerce.product_key"))
        .withColumn("ecommerce_variant_key", F.col("ecommerce.variant_key"))
        .withColumn("ecommerce_search_query", F.col("ecommerce.search_query"))
        .withColumn("ecommerce_search_redacted", F.col("ecommerce.search_redacted"))
        .withColumn("ecommerce_filters", F.col("ecommerce.filters"))
        .withColumn("error_code", F.col("error.code"))
        .withColumn("error_type", F.col("error.type"))
        .withColumn("_silver_ingested_at", F.current_timestamp())
        .withColumn("_source_bronze_run_id", F.lit(run_id))
        .drop("schema", "service", "event", "http", "request", "actor", "client", "ecommerce", "error", "_run_id", "_source_file", "_ingested_at")
    )

    count = enriched.count()
    if count == 0:
        return 0

    if _write_format == "iceberg":
        enriched.writeTo(LOGS_SILVER_TABLE).append()
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
git commit -m "feat(pipelines): add Silver logs anti-join dedup module"
```



---

### Task 5: Spark Submit Jobs for Silver

**Files:**
- Create: `pipelines/src/jobs/oltp/ingest_oltp_silver.py`
- Create: `pipelines/src/jobs/logs/ingest_logs_silver.py`

**Interfaces:**
- OLTP job: argparse with --config-path, --run-id, --bronze-date. Reads Bronze tables, calls merge_oltp_table for each.
- Logs job: argparse with --run-id, --ingest-date. Reads Bronze logs, calls ingest_logs_to_silver.

- [ ] **Step 1: Write OLTP Silver job script**

```python
import argparse
import sys

from lakehouse.config import load_config
from lakehouse.oltp.silver import merge_oltp_table
from lakehouse.oltp.silver_ddl import ensure_silver_tables
from lakehouse.spark import spark_session


def parse_args(args):
    parser = argparse.ArgumentParser(description="Ingest OLTP Bronze to Silver")
    parser.add_argument("--config-path", required=True, help="Path to pipeline config YAML")
    parser.add_argument("--run-id", required=True, help="Airflow DAG run ID")
    parser.add_argument("--bronze-date", required=True, help="Bronze date to process (YYYY-MM-DD)")
    return parser.parse_args(args)


def main():
    args = parse_args(sys.argv[1:])
    spark = spark_session("ingest_oltp_bronze_to_silver")
    try:
        cfg = load_config(args.config_path)
        ensure_silver_tables(spark)

        for table in cfg.tables:
            bronze_table = f"lakehouse.bronze.{table.name}"
            silver_path = f"s3a://{cfg.bucket}/warehouse/silver/{table.silver_table}"

            try:
                bronze_df = spark.read.format("iceberg").load(bronze_table)
            except Exception:
                print(f"Bronze table {bronze_table} not found, skipping.")
                continue

            result = merge_oltp_table(
                spark=spark,
                table=table,
                bronze_df=bronze_df,
                run_id=args.run_id,
                target_path=silver_path,
            )

            print(f"{table.name}: inserted={result.inserted}, updated={result.updated}, quarantined={result.quarantined}")
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Write Logs Silver job script**

```python
import argparse
import sys

from lakehouse.logs_bronze import BRONZE_EVENTS_TABLE
from lakehouse.logs_silver import ensure_logs_silver_tables, ingest_logs_to_silver
from lakehouse.spark import spark_session


def parse_args(args):
    parser = argparse.ArgumentParser(description="Ingest Logs Bronze to Silver")
    parser.add_argument("--run-id", required=True, help="Airflow DAG run ID")
    parser.add_argument("--ingest-date", required=True, help="Target date (YYYY-MM-DD)")
    return parser.parse_args(args)


def main():
    args = parse_args(sys.argv[1:])
    spark = spark_session("ingest_logs_bronze_to_silver")
    try:
        ensure_logs_silver_tables(spark)

        try:
            bronze_df = spark.read.format("iceberg").load(BRONZE_EVENTS_TABLE)
        except Exception:
            print(f"Bronze table {BRONZE_EVENTS_TABLE} not found. Exiting.")
            return

        count = ingest_logs_to_silver(
            spark=spark,
            bronze_df=bronze_df,
            run_id=args.run_id,
            target_path="",
        )

        print(f"Logs Silver: ingested={count} records")
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Commit**

```bash
git add pipelines/src/jobs/ingest_oltp_silver.py pipelines/src/jobs/ingest_logs_silver.py
git commit -m "feat(pipelines): add Spark submit jobs for Silver ingestion"
```

---

### Task 6: Airflow DAGs for Silver

**Files:**
- Create: `airflow/dags/ingest_oltp_silver.py`
- Create: `airflow/dags/ingest_logs_silver.py`

**Interfaces:**
- OLTP DAG: `ingest_oltp_bronze_to_silver`, schedule=None, SparkSubmitOperator
- Logs DAG: `ingest_logs_bronze_to_silver`, schedule="0 */2 * * *", SparkSubmitOperator

- [ ] **Step 1: Write OLTP Silver DAG**

```python
import os
import uuid
from datetime import datetime, timedelta, timezone

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator

CONFIG_PATH = os.environ["PIPELINE_CONFIG_PATH"]
SPARK_APP = "/opt/project/pipelines/src/jobs/oltp/ingest_oltp_silver.py"

DEFAULT_ARGS = {
    "owner": "batch",
    "retries": 2,
    "retry_delay": timedelta(minutes=1),
}


def begin_run(**context) -> None:
    context["ti"].xcom_push(key="run_id", value=uuid.uuid4().hex)
    context["ti"].xcom_push(
        key="bronze_date", value=datetime.now(timezone.utc).strftime("%Y-%m-%d")
    )


with DAG(
    dag_id="ingest_oltp_bronze_to_silver",
    default_args=DEFAULT_ARGS,
    schedule=None,
    catchup=False,
    start_date=datetime(2026, 8, 15, tzinfo=timezone.utc),
    description="Ingest OLTP Bronze tables to Silver via MERGE",
) as dag:

    begin = PythonOperator(task_id="begin_run", python_callable=begin_run)

    spark_ingest = SparkSubmitOperator(
        task_id="spark_oltp_bronze_to_silver",
        application=SPARK_APP,
        application_args=[
            "--config-path", CONFIG_PATH,
            "--run-id", "{{ ti.xcom_pull(task_ids='begin_run', key='run_id') }}",
            "--bronze-date", "{{ ti.xcom_pull(task_ids='begin_run', key='bronze_date') }}",
        ],
    )

    begin >> spark_ingest
```

- [ ] **Step 2: Write Logs Silver DAG**

```python
import os
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
    schedule="0 */2 * * *",
    catchup=False,
    start_date=datetime(2026, 8, 15, tzinfo=timezone.utc),
    description="Ingest Logs Bronze to Silver with dedup",
) as dag:

    begin = PythonOperator(task_id="begin_run", python_callable=begin_run)

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

- [ ] **Step 3: Commit**

```bash
git add airflow/dags/ingest_oltp_silver.py airflow/dags/ingest_logs_silver.py
git commit -m "feat(pipelines): add Airflow DAGs for Silver ingestion"
```



---

### Task 7: Integration Tests

**Files:**
- Modify: `pipelines/tests/test_silver.py`
- Modify: `pipelines/tests/test_logs_silver.py`

**Interfaces:**
- End-to-end tests testing full pipeline round-trips

- [ ] **Step 1: Write OLTP integration test**

```python
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
    data = [
        (1, "alice@test.com", "Alice", "0901", "customer", "active", "2026-01-01", "2026-08-01", "2026-08-15", "run-1"),
        (2, "bob@test.com", "Bob", "0902", "customer", "active", "2026-01-01", "2026-08-01", "2026-08-15", "run-1"),
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
        (1, "alice_new@test.com", "Alice New", "0901", "customer", "active", "2026-01-01", "2026-08-16", "2026-08-16", "run-2"),
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
    assert alice["email_pseudonymized"] is not None
    assert alice["_source_bronze_run_id"] == "run-2"


def test_quarantine_routes_violations(tmp_path):
    import os
    os.environ["SILVER_PSEUDONYMIZE_SALT"] = "test-salt"

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
        (1, 1, "SKU-001", "M", "RED", -500, "true", "2026-01-01", "2026-08-01", "2026-08-15", "run-1"),
        (2, 1, "SKU-002", "L", "BLUE", 50000, "true", "2026-01-01", "2026-08-01", "2026-08-15", "run-1"),
    ]

    spark = SparkSession.builder.master("local[1]").appName("test-quarantine").getOrCreate()
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
```

- [ ] **Step 2: Write Logs integration test**

```python
def test_full_logs_pipeline_roundtrip(spark, tmp_path):
    from pyspark.sql.types import BooleanType, LongType, MapType
    schema = StructType([
        StructField("event_id", StringType(), False),
        StructField("event_ts", TimestampType(), False),
        StructField("observed_timestamp", TimestampType(), False),
        StructField("severity_text", StringType(), False),
        StructField("severity_number", IntegerType(), False),
        StructField("request", StructType([StructField("id", StringType(), False)]), False),
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
        StructField("client", StructType([StructField("user_agent", StringType(), True)]), True),
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
        ("evt-2", "2026-08-15 10:01:00", "2026-08-15 10:01:01", "INFO", 9, {"id": "req-2"}, None, None,
         {"name": "api", "version": "1.0", "environment": "prod", "instance_id": "i-1"},
         {"name": "POST", "category": "http", "kind": "server", "outcome": "OK", "duration_ns": 200000},
         {"request_method": "POST", "route": "/cart", "status_code": 201},
         {"type": "customer", "key": "c-1"}, {"user_agent": "Mozilla/5.0"},
         {"action": "cart_add", "product_key": "p1", "variant_key": "v1", "search_query": None, "search_redacted": False, "filters": None},
         None, "observed", "run-1", "file-1.jsonl.gz", "2026-08-15"),
    ]
    bronze_df = spark.createDataFrame(data, schema)
    target = str(tmp_path / "silver_logs")

    count = ingest_logs_to_silver(spark, bronze_df, "run-1", target, _write_format="parquet")
    assert count == 2

    df = spark.read.parquet(target)
    assert df.count() == 2
    assert "_silver_ingested_at" in df.columns
    assert "_source_bronze_run_id" in df.columns
    assert "http_request_method" in df.columns
    assert "ecommerce_action" in df.columns
```

- [ ] **Step 3: Run all tests**

Run: `PYTHONPATH=pipelines/src pytest pipelines/tests/test_silver.py pipelines/tests/test_logs_silver.py -v`
Expected: ALL PASS

- [ ] **Step 4: Commit**

```bash
git add pipelines/tests/test_silver.py pipelines/tests/test_logs_silver.py
git commit -m "feat(pipelines): add integration tests for Silver OLTP and Logs pipelines"
```
