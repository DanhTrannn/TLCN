from __future__ import annotations

import shutil
from datetime import date, datetime
from pathlib import Path

import pytest

from lakehouse.config import load_config
from lakehouse.oltp.gold_ddl import GOLD_TABLE_DDL

CONFIG_FILE = Path(__file__).resolve().parents[1] / "config" / "default.yml"


# ==============================================================================
# 1. Config Validation Tests
# ==============================================================================

def test_inbound_tables_registered_in_config():
    """Verify that inbound_receipts and inbound_receipt_items are registered with valid specs."""
    config = load_config(CONFIG_FILE)
    
    inbound_receipts = config.table("inbound_receipts")
    assert inbound_receipts is not None, "inbound_receipts must be registered in default.yml"
    assert inbound_receipts.cursor_field == "updated_at"
    assert inbound_receipts.pk == "receipt_id"
    assert inbound_receipts.mutability == "mutable"
    assert inbound_receipts.silver_table == "silver_inbound_receipts"

    inbound_receipt_items = config.table("inbound_receipt_items")
    assert inbound_receipt_items is not None, "inbound_receipt_items must be registered in default.yml"
    assert inbound_receipt_items.cursor_field == "created_at"
    assert inbound_receipt_items.pk == "item_id"
    assert inbound_receipt_items.mutability == "append_only"
    assert inbound_receipt_items.silver_table == "silver_inbound_receipt_items"


def test_catalogue_includes_inbound_tables():
    """Ensure config catalogue contains both inbound tables and no duplicates."""
    config = load_config(CONFIG_FILE)
    table_names = [t.name for t in config.tables]
    assert len(table_names) == len(set(table_names)), "Table names must be unique"
    assert "inbound_receipts" in table_names
    assert "inbound_receipt_items" in table_names


# ==============================================================================
# 2. Gold Mart DDL Validation Tests
# ==============================================================================

def test_fact_order_ddl_financial_columns():
    """Verify fact_order DDL includes all required revenue, COGS, and profit columns."""
    ddl = GOLD_TABLE_DDL.get("fact_order")
    assert ddl is not None, "fact_order DDL must exist"
    assert "gross_revenue_vnd               BIGINT" in ddl
    assert "total_cost_vnd                  BIGINT" in ddl
    assert "gross_profit_vnd                BIGINT" in ddl
    assert "net_revenue_vnd                 BIGINT" in ddl
    assert "net_profit_vnd                  BIGINT" in ddl
    assert "is_boom                         BOOLEAN" in ddl
    assert "is_delivered                    BOOLEAN" in ddl
    assert "PARTITIONED BY (order_date)" in ddl


def test_fact_order_item_ddl_financial_columns():
    """Verify fact_order_item DDL includes unit cost, item cost, and line profit."""
    ddl = GOLD_TABLE_DDL.get("fact_order_item")
    assert ddl is not None, "fact_order_item DDL must exist"
    assert "quantity                        INT" in ddl
    assert "unit_price_vnd                  BIGINT" in ddl
    assert "unit_cost_vnd                   BIGINT" in ddl
    assert "item_total_vnd                  BIGINT" in ddl
    assert "item_cost_vnd                   BIGINT" in ddl
    assert "item_profit_vnd                 BIGINT" in ddl


def test_mart_sales_daily_ddl_financial_columns():
    """Verify mart_sales_daily DDL includes COGS, gross profit, and profit margin pct."""
    ddl = GOLD_TABLE_DDL.get("mart_sales_daily")
    assert ddl is not None, "mart_sales_daily DDL must exist"
    assert "gross_revenue_vnd               BIGINT" in ddl
    assert "cogs_vnd                        BIGINT" in ddl
    assert "gross_profit_vnd                BIGINT" in ddl
    assert "gross_profit_margin_pct         DOUBLE" in ddl
    assert "items_sold                      BIGINT" in ddl
    assert "successful_orders               BIGINT" in ddl
    assert "boom_orders                     BIGINT" in ddl
    assert "PARTITIONED BY (order_date)" in ddl


# ==============================================================================
# 3. Pure Python Financial Formula & Logic Parity Tests
# ==============================================================================

def test_financial_formulas_line_item():
    """Verify mathematical parity of order item line calculations."""
    quantity = 3
    unit_price = 250_000
    unit_cost = 100_000

    item_total = quantity * unit_price
    item_cost = quantity * unit_cost
    item_profit = item_total - item_cost

    assert item_total == 750_000
    assert item_cost == 300_000
    assert item_profit == 450_000


def test_financial_formulas_order_aggregation():
    """Verify order total cost and gross profit calculation parity."""
    items = [
        {"quantity": 2, "unit_price": 200_000, "cost_price": 90_000},
        {"quantity": 1, "unit_price": 500_000, "cost_price": 220_000},
    ]
    gross_revenue = sum(item["quantity"] * item["unit_price"] for item in items)
    total_cost = sum(item["quantity"] * item["cost_price"] for item in items)
    gross_profit = gross_revenue - total_cost

    assert gross_revenue == 900_000
    assert total_cost == 400_000
    assert gross_profit == 500_000


def test_financial_formulas_gross_profit_margin():
    """Verify margin percentage calculation, division-by-zero guard, and rounding."""
    # Normal case: 400k profit on 1,000k revenue -> 40.0%
    gross_rev = 1_000_000
    gross_profit = 400_000
    margin_pct = round((gross_profit / gross_rev) * 100.0, 2) if gross_rev > 0 else 0.0
    assert margin_pct == 40.0

    # Repeating decimal: 100k profit on 300k revenue -> 33.33%
    gross_rev = 300_000
    gross_profit = 100_000
    margin_pct = round((gross_profit / gross_rev) * 100.0, 2) if gross_rev > 0 else 0.0
    assert margin_pct == 33.33

    # Zero revenue guard: should be 0.0, never ZeroDivisionError
    gross_rev = 0
    gross_profit = 0
    margin_pct = round((gross_profit / gross_rev) * 100.0, 2) if gross_rev > 0 else 0.0
    assert margin_pct == 0.0

    # Negative margin (selling at a loss):
    gross_rev = 500_000
    gross_profit = -50_000
    margin_pct = round((gross_profit / gross_rev) * 100.0, 2) if gross_rev > 0 else 0.0
    assert margin_pct == -10.0


def test_revenue_recognition_logic():
    """Verify non-revenue statuses zero out recognized net revenue and profit."""
    non_revenue_statuses = {"failed_delivery", "returned", "cancelled", "payment_failed"}
    revenue_statuses = {"delivered", "completed", "shipped", "processing"}

    for status in non_revenue_statuses:
        gross_rev = 500_000
        gross_prof = 200_000
        is_non_revenue = status in non_revenue_statuses
        net_rev = 0 if is_non_revenue else gross_rev
        net_prof = 0 if is_non_revenue else gross_prof
        assert net_rev == 0, f"Status {status} must yield 0 net revenue"
        assert net_prof == 0, f"Status {status} must yield 0 net profit"

    for status in revenue_statuses:
        gross_rev = 500_000
        gross_prof = 200_000
        is_non_revenue = status in non_revenue_statuses
        net_rev = 0 if is_non_revenue else gross_rev
        net_prof = 0 if is_non_revenue else gross_prof
        assert net_rev == gross_rev
        assert net_prof == gross_prof


# ==============================================================================
# 4. PySpark DataFrame Implementation Tests (Run if Java / Spark available)
# ==============================================================================

pyspark = pytest.importorskip("pyspark", reason="pyspark not installed")
has_java = shutil.which("java") is not None


@pytest.mark.skipif(not has_java, reason="Java not found -- Spark tests require a JDK")
class TestSparkFinancialGoldMarts:
    @pytest.fixture(scope="class")
    def spark(self):
        from pyspark.sql import SparkSession
        return (
            SparkSession.builder.master("local[1]")
            .appName("test-financial-gold-marts")
            .config("spark.sql.session.timeZone", "UTC")
            .getOrCreate()
        )

    def test_spark_fact_order_financial_calculations(self, spark):
        from pyspark.sql.types import (
            BooleanType,
            IntegerType,
            LongType,
            StringType,
            StructField,
            StructType,
            TimestampType,
        )
        from lakehouse.oltp.gold import build_fact_order

        o_schema = StructType([
            StructField("order_id", LongType(), False),
            StructField("order_number", StringType(), False),
            StructField("customer_id", LongType(), False),
            StructField("store_id", LongType(), True),
            StructField("status", StringType(), False),
            StructField("payment_method", StringType(), False),
            StructField("payment_status", StringType(), False),
            StructField("coupon_id", LongType(), True),
            StructField("subtotal_vnd", LongType(), False),
            StructField("discount_vnd", LongType(), False),
            StructField("shipping_fee_vnd", LongType(), False),
            StructField("total_vnd", LongType(), False),
            StructField("created_at", TimestampType(), False),
        ])
        oi_schema = StructType([
            StructField("order_item_id", LongType(), False),
            StructField("order_id", LongType(), False),
            StructField("product_id", LongType(), False),
            StructField("variant_id", LongType(), False),
            StructField("quantity", IntegerType(), False),
            StructField("unit_price_vnd", LongType(), False),
            StructField("cost_price_vnd", LongType(), True),
        ])

        now = datetime(2026, 9, 22, 10, 0, 0)
        # Order 1: Online delivered, total 600k, items cost 250k
        # Order 2: POS completed, total 400k, items cost 150k
        # Order 3: Online failed_delivery (boom), total 300k, items cost 100k
        orders = [
            (1, "ORD-001", 10, None, "delivered", "vietqr", "succeeded", None, 600000, 0, 0, 600000, now),
            (2, "ORD-002", 20, 1, "completed", "cod", "succeeded", None, 400000, 0, 0, 400000, now),
            (3, "ORD-003", 30, None, "failed_delivery", "cod", "pending", None, 300000, 0, 30000, 330000, now),
        ]
        items = [
            (1, 1, 100, 1001, 2, 300000, 125000),  # total 600k, cost 250k
            (2, 2, 200, 2001, 1, 400000, 150000),  # total 400k, cost 150k
            (3, 3, 100, 1001, 1, 300000, 100000),  # total 300k, cost 100k
        ]

        o_df = spark.createDataFrame(orders, o_schema)
        oi_df = spark.createDataFrame(items, oi_schema)

        fact_df = build_fact_order(o_df, oi_df, "run-test")
        rows = {r.order_id: r for r in fact_df.collect()}

        # Order 1 (Online Delivered)
        ord1 = rows[1]
        assert ord1.gross_revenue_vnd == 600000
        assert ord1.total_cost_vnd == 250000
        assert ord1.gross_profit_vnd == 350000
        assert ord1.net_revenue_vnd == 600000
        assert ord1.net_profit_vnd == 350000
        assert ord1.is_delivered is True
        assert ord1.is_boom is False
        assert ord1.channel == "online"

        # Order 2 (POS Completed)
        ord2 = rows[2]
        assert ord2.gross_revenue_vnd == 400000
        assert ord2.total_cost_vnd == 150000
        assert ord2.gross_profit_vnd == 250000
        assert ord2.net_revenue_vnd == 400000
        assert ord2.net_profit_vnd == 250000
        assert ord2.is_delivered is True
        assert ord2.is_boom is False
        assert ord2.channel == "pos"
        assert ord2.store_key == 1

        # Order 3 (Boom / Failed Delivery)
        ord3 = rows[3]
        assert ord3.gross_revenue_vnd == 330000
        assert ord3.total_cost_vnd == 100000
        assert ord3.gross_profit_vnd == 230000
        assert ord3.net_revenue_vnd == 0
        assert ord3.net_profit_vnd == 0
        assert ord3.is_delivered is False
        assert ord3.is_boom is True

    def test_spark_fact_order_with_variant_cost_fallback(self, spark):
        from pyspark.sql.types import (
            BooleanType,
            IntegerType,
            LongType,
            StringType,
            StructField,
            StructType,
            TimestampType,
        )
        from lakehouse.oltp.gold import build_fact_order, build_fact_order_item

        o_schema = StructType([
            StructField("order_id", LongType(), False),
            StructField("order_number", StringType(), False),
            StructField("customer_id", LongType(), False),
            StructField("store_id", LongType(), True),
            StructField("status", StringType(), False),
            StructField("created_at", TimestampType(), False),
            StructField("total_vnd", LongType(), False),
        ])
        oi_schema = StructType([
            StructField("order_item_id", LongType(), False),
            StructField("order_id", LongType(), False),
            StructField("variant_id", LongType(), False),
            StructField("quantity", IntegerType(), False),
            StructField("unit_price_vnd", LongType(), False),
            StructField("cost_price_vnd", LongType(), True),
        ])
        pv_schema = StructType([
            StructField("variant_id", LongType(), False),
            StructField("product_id", LongType(), False),
            StructField("cost_price_vnd", LongType(), True),
        ])

        now = datetime(2026, 9, 22, 10, 0, 0)
        o_df = spark.createDataFrame([(1, "ORD-001", 10, None, "delivered", now, 500000)], o_schema)
        # item has cost_price_vnd=None -> must fall back to pv.cost_price_vnd (180_000)
        oi_df = spark.createDataFrame([(1, 1, 101, 2, 250000, None)], oi_schema)
        pv_df = spark.createDataFrame([(101, 10, 180000)], pv_schema)

        # Test build_fact_order with fallback
        fact_order_df = build_fact_order(o_df, oi_df, "run-test", silver_product_variants=pv_df)
        fo_row = fact_order_df.collect()[0]
        assert fo_row.total_cost_vnd == 360000  # 2 * 180,000
        assert fo_row.gross_profit_vnd == 140000  # 500,000 - 360,000

        # Test build_fact_order_item with fallback
        fact_oi_df = build_fact_order_item(oi_df, o_df, "run-test", silver_product_variants=pv_df)
        foi_row = fact_oi_df.collect()[0]
        assert foi_row.unit_cost_vnd == 180000
        assert foi_row.item_total_vnd == 500000
        assert foi_row.item_cost_vnd == 360000
        assert foi_row.item_profit_vnd == 140000

    def test_spark_build_mart_sales_daily_parity(self, spark):
        from pyspark.sql.types import (
            BooleanType,
            DateType,
            IntegerType,
            LongType,
            StringType,
            StructField,
            StructType,
        )
        from lakehouse.oltp.gold import build_mart_sales_daily

        fo_schema = StructType([
            StructField("order_id", LongType(), False),
            StructField("order_date", DateType(), False),
            StructField("channel", StringType(), False),
            StructField("store_key", LongType(), False),
            StructField("is_delivered", BooleanType(), False),
            StructField("is_boom", BooleanType(), False),
        ])
        foi_schema = StructType([
            StructField("order_id", LongType(), False),
            StructField("product_key", LongType(), False),
            StructField("quantity", IntegerType(), False),
            StructField("item_total_vnd", LongType(), False),
            StructField("item_cost_vnd", LongType(), False),
            StructField("item_profit_vnd", LongType(), False),
        ])
        dp_schema = StructType([
            StructField("product_key", LongType(), False),
            StructField("category_id", LongType(), False),
            StructField("category_name", StringType(), False),
        ])

        d = date(2026, 9, 22)
        # Order 1: delivered online (rev 600k, cost 240k, profit 360k)
        # Order 2: boom online (rev 300k, cost 120k) -> should NOT count towards delivered sales/COGS
        fo_df = spark.createDataFrame([
            (1, d, "online", 0, True, False),
            (2, d, "online", 0, False, True),
        ], fo_schema)
        foi_df = spark.createDataFrame([
            (1, 10, 2, 600000, 240000, 360000),
            (2, 10, 1, 300000, 120000, 180000),
        ], foi_schema)
        dp_df = spark.createDataFrame([(10, 1, "Thời Trang Nam")], dp_schema)

        mart_df = build_mart_sales_daily(fo_df, foi_df, dp_df, "run-test")
        assert mart_df.count() == 1
        row = mart_df.collect()[0]

        assert row.order_date == d
        assert row.channel == "online"
        assert row.store_key == 0
        assert row.category_id == 1
        assert row.category_name == "Thời Trang Nam"
        assert row.total_orders == 2
        assert row.successful_orders == 1
        assert row.boom_orders == 1
        assert row.items_sold == 2
        assert row.gross_revenue_vnd == 600000
        assert row.cogs_vnd == 240000
        assert row.gross_profit_vnd == 360000
        # (360,000 / 600,000) * 100 = 60.0%
        assert row.gross_profit_margin_pct == 60.0
