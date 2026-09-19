import shutil
from datetime import datetime, date

import pytest

pyspark = pytest.importorskip("pyspark", reason="pyspark not installed")
pytestmark = pytest.mark.skipif(
    shutil.which("java") is None,
    reason="Java not found -- Spark tests require a JDK",
)

from pyspark.sql import SparkSession
from pyspark.sql.types import (
    BooleanType,
    DateType,
    DoubleType,
    IntegerType,
    LongType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)

from lakehouse.oltp.gold import (
    build_dim_customer,
    build_dim_date,
    build_dim_delivery_staff,
    build_dim_product,
    build_dim_store,
    build_dim_variant,
    build_fact_inventory_daily_snapshot,
    build_fact_order,
    build_fact_order_item,
    build_fact_return_exchange,
    build_fact_shipment,
    build_mart_inventory_health,
    build_mart_logistics_performance,
    build_mart_product_returns,
    build_mart_sales_daily,
)
from lakehouse.oltp.gold_ddl import GOLD_TABLE_DDL


@pytest.fixture(scope="session")
def spark():
    return (
        SparkSession.builder.master("local[1]")
        .appName("test-oltp-gold")
        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
    )


def test_gold_table_ddl_declarations():
    assert len(GOLD_TABLE_DDL) == 15
    for table_name, ddl in GOLD_TABLE_DDL.items():
        assert "CREATE TABLE IF NOT EXISTS" in ddl
        assert "USING iceberg" in ddl
        assert "lakehouse.gold." in ddl


def test_build_dim_date(spark):
    dim_date = build_dim_date(spark, start_date="2026-08-01", end_date="2026-08-03")
    assert dim_date.count() == 3

    rows = {r.date_key: r for r in dim_date.collect()}
    assert 20260801 in rows
    # 2026-08-01 was Saturday (day_of_week 7 in Spark default Sunday=1)
    r1 = rows[20260801]
    assert r1.is_weekend is True
    assert r1.year == 2026
    assert r1.month == 8
    assert r1.quarter == 3


def test_build_dim_product_and_variant(spark):
    p_schema = StructType([
        StructField("product_id", LongType(), False),
        StructField("name", StringType(), False),
        StructField("slug", StringType(), False),
        StructField("category_id", LongType(), False),
        StructField("base_price_vnd", LongType(), False),
        StructField("is_active", BooleanType(), False),
        StructField("created_at", TimestampType(), False),
    ])
    c_schema = StructType([
        StructField("category_id", LongType(), False),
        StructField("name", StringType(), False),
    ])
    v_schema = StructType([
        StructField("variant_id", LongType(), False),
        StructField("product_id", LongType(), False),
        StructField("sku", StringType(), False),
        StructField("color", StringType(), False),
        StructField("size", StringType(), False),
        StructField("price_vnd", LongType(), False),
        StructField("cost_price_vnd", LongType(), True),
        StructField("is_active", BooleanType(), False),
    ])

    now = datetime(2026, 8, 1, 10, 0, 0)
    p_df = spark.createDataFrame([(10, "Áo Polo Nam", "ao-polo-nam", 1, 300000, True, now)], p_schema)
    c_df = spark.createDataFrame([(1, "Áo Nam")], c_schema)
    v_df = spark.createDataFrame([(101, 10, "POLO-BLK-M", "Black", "M", 300000, 120000, True)], v_schema)

    dim_product = build_dim_product(p_df, c_df, "run-1")
    p_row = dim_product.collect()[0]
    assert p_row.product_key == 10
    assert p_row.product_name == "Áo Polo Nam"
    assert p_row.category_name == "Áo Nam"

    dim_variant = build_dim_variant(v_df, p_df, "run-1")
    v_row = dim_variant.collect()[0]
    assert v_row.variant_key == 101
    assert v_row.cost_price_vnd == 120000
    # Margin = (300000 - 120000) / 300000 = 60.0%
    assert v_row.margin_pct == 60.0


def test_build_dim_store_and_delivery_staff(spark):
    city_schema = StructType([
        StructField("city_id", LongType(), False),
        StructField("name", StringType(), False),
    ])
    store_schema = StructType([
        StructField("store_id", LongType(), False),
        StructField("code", StringType(), False),
        StructField("name", StringType(), False),
        StructField("city_id", LongType(), False),
        StructField("address", StringType(), False),
        StructField("phone", StringType(), False),
        StructField("is_active", BooleanType(), False),
    ])
    staff_schema = StructType([
        StructField("staff_id", LongType(), False),
        StructField("staff_code", StringType(), False),
        StructField("full_name", StringType(), False),
        StructField("full_name_pseudonymized", StringType(), True),
        StructField("phone", StringType(), False),
        StructField("phone_pseudonymized", StringType(), True),
        StructField("assigned_city_id", LongType(), False),
        StructField("vehicle_type", StringType(), False),
        StructField("is_active", BooleanType(), False),
    ])

    city_df = spark.createDataFrame([(1, "Hà Nội")], city_schema)
    store_df = spark.createDataFrame([(1, "HN01", "D&K Ba Đình", 1, "123 Kim Mã", "024123456", True)], store_schema)
    staff_df = spark.createDataFrame([
        (10, "DK-SHIP-01", "Nguyễn Văn A", "hash_name", "0901234567", "hash_phone", 1, "motorbike", True)
    ], staff_schema)

    dim_store = build_dim_store(store_df, city_df, "run-1")
    s_row = dim_store.collect()[0]
    assert s_row.store_code == "HN01"
    assert s_row.city_name == "Hà Nội"

    dim_staff = build_dim_delivery_staff(staff_df, city_df, "run-1")
    st_row = dim_staff.collect()[0]
    assert st_row.full_name == "hash_name"
    assert st_row.assigned_city_name == "Hà Nội"


def test_build_dim_customer(spark):
    city_schema = StructType([
        StructField("city_id", LongType(), False),
        StructField("name", StringType(), False),
    ])
    cust_schema = StructType([
        StructField("customer_id", LongType(), False),
        StructField("email_normalized", StringType(), False),
        StructField("email_pseudonymized", StringType(), True),
        StructField("phone", StringType(), False),
        StructField("phone_pseudonymized", StringType(), True),
        StructField("full_name", StringType(), False),
        StructField("full_name_pseudonymized", StringType(), True),
        StructField("role", StringType(), False),
        StructField("status", StringType(), False),
        StructField("city_id", LongType(), False),
        StructField("store_id", LongType(), True),
        StructField("is_cod_blocked", BooleanType(), True),
        StructField("boom_count", IntegerType(), True),
        StructField("created_at", TimestampType(), False),
    ])

    now = datetime(2026, 8, 1, 10, 0, 0)
    city_df = spark.createDataFrame([(1, "Hồ Chí Minh")], city_schema)
    cust_df = spark.createDataFrame([
        (5, "a@b.com", "h_email", "0987654321", "h_phone", "Tran B", "h_name",
         "customer", "active", 1, None, True, 3, now)
    ], cust_schema)

    dim_cust = build_dim_customer(cust_df, city_df, "run-1")
    c_row = dim_cust.collect()[0]
    assert c_row.customer_key == 5
    assert c_row.is_cod_blocked is True
    assert c_row.boom_count == 3
    assert c_row.city_name == "Hồ Chí Minh"


def test_build_fact_order_revenue_recognition(spark):
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

    now = datetime(2026, 8, 1, 12, 0, 0)
    # Order 1: delivered (gross 500,000, cost 200,000 -> gross profit 300,000, net revenue 500,000)
    # Order 2: failed_delivery (boom) -> net revenue 0, net profit 0
    # Order 3: returned -> net revenue 0, net profit 0
    orders = [
        (1, "ORD-001", 101, None, "delivered", "vietqr", "succeeded", None, 500000, 0, 0, 500000, now),
        (2, "ORD-002", 102, None, "failed_delivery", "cod", "pending", None, 400000, 0, 30000, 430000, now),
        (3, "ORD-003", 103, 1, "returned", "cod", "succeeded", None, 300000, 0, 0, 300000, now),
    ]
    items = [
        (1, 1, 10, 101, 1, 500000, 200000),
        (2, 2, 10, 101, 1, 400000, 150000),
        (3, 3, 10, 101, 1, 300000, 100000),
    ]

    o_df = spark.createDataFrame(orders, o_schema)
    oi_df = spark.createDataFrame(items, oi_schema)

    fact_df = build_fact_order(o_df, oi_df, "run-1")
    rows = {r.order_id: r for r in fact_df.collect()}

    # Delivered order
    ord1 = rows[1]
    assert ord1.gross_revenue_vnd == 500000
    assert ord1.total_cost_vnd == 200000
    assert ord1.gross_profit_vnd == 300000
    assert ord1.net_revenue_vnd == 500000
    assert ord1.net_profit_vnd == 300000
    assert ord1.is_delivered is True
    assert ord1.is_boom is False
    assert ord1.channel == "online"

    # Boom order
    ord2 = rows[2]
    assert ord2.gross_revenue_vnd == 430000
    assert ord2.net_revenue_vnd == 0
    assert ord2.net_profit_vnd == 0
    assert ord2.is_delivered is False
    assert ord2.is_boom is True

    # Returned order
    ord3 = rows[3]
    assert ord3.channel == "pos"
    assert ord3.store_key == 1
    assert ord3.net_revenue_vnd == 0
    assert ord3.net_profit_vnd == 0


def test_build_fact_order_item(spark):
    o_schema = StructType([
        StructField("order_id", LongType(), False),
        StructField("customer_id", LongType(), False),
        StructField("store_id", LongType(), True),
        StructField("status", StringType(), False),
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

    now = datetime(2026, 8, 1, 12, 0, 0)
    o_df = spark.createDataFrame([(1, 101, None, "delivered", now)], o_schema)
    oi_df = spark.createDataFrame([(10, 1, 20, 201, 2, 350000, 150000)], oi_schema)

    fact_oi = build_fact_order_item(oi_df, o_df, "run-1")
    row = fact_oi.collect()[0]
    assert row.item_total_vnd == 700000
    assert row.item_cost_vnd == 300000
    assert row.item_profit_vnd == 400000


def test_build_fact_shipment(spark):
    ship_schema = StructType([
        StructField("shipment_id", LongType(), False),
        StructField("shipment_code", StringType(), False),
        StructField("order_id", LongType(), False),
        StructField("delivery_staff_id", LongType(), False),
        StructField("status", StringType(), False),
        StructField("attempt_count", IntegerType(), False),
        StructField("cod_amount_expected_vnd", LongType(), False),
        StructField("cod_amount_collected_vnd", LongType(), True),
        StructField("dispatched_at", TimestampType(), True),
        StructField("delivered_at", TimestampType(), True),
        StructField("failed_at", TimestampType(), True),
        StructField("estimated_delivery_at", TimestampType(), True),
        StructField("created_at", TimestampType(), False),
    ])

    c_at = datetime(2026, 8, 1, 8, 0, 0)
    disp = datetime(2026, 8, 1, 8, 30, 0)
    deliv = datetime(2026, 8, 1, 9, 30, 0)  # 60 minutes
    est = datetime(2026, 8, 1, 10, 0, 0)

    ship_df = spark.createDataFrame([
        (1, "SHIP-01", 100, 10, "delivered", 1, 500000, 500000, disp, deliv, None, est, c_at),
        (2, "SHIP-02", 101, 10, "failed", 3, 300000, 0, disp, None, deliv, est, c_at),
    ], ship_schema)

    fact_ship = build_fact_shipment(ship_df, "run-1")
    rows = {r.shipment_id: r for r in fact_ship.collect()}

    s1 = rows[1]
    assert s1.is_delivered is True
    assert s1.is_boom is False
    assert s1.delivery_duration_minutes == 60.0
    assert s1.is_on_time is True

    s2 = rows[2]
    assert s2.is_delivered is False
    assert s2.is_boom is True


def test_build_fact_return_exchange(spark):
    rr_schema = StructType([
        StructField("return_id", LongType(), False),
        StructField("return_number", StringType(), False),
        StructField("order_id", LongType(), False),
        StructField("action_type", StringType(), False),
        StructField("status", StringType(), False),
        StructField("reason", StringType(), False),
        StructField("refund_amount_vnd", LongType(), True),
        StructField("created_at", TimestampType(), False),
    ])
    ri_schema = StructType([
        StructField("return_item_id", LongType(), False),
        StructField("return_id", LongType(), False),
        StructField("order_item_id", LongType(), False),
        StructField("returned_variant_id", LongType(), False),
        StructField("exchanged_variant_id", LongType(), True),
        StructField("quantity", IntegerType(), False),
    ])

    now = datetime(2026, 8, 2, 10, 0, 0)
    rr_df = spark.createDataFrame([
        (1, "RET-01", 100, "exchange", "completed", "wrong_size", 0, now),
        (2, "RET-02", 101, "refund", "completed", "defective", 350000, now),
    ], rr_schema)
    ri_df = spark.createDataFrame([
        (10, 1, 1001, 201, 202, 1),
        (11, 2, 1002, 301, None, 1),
    ], ri_schema)

    fact_re = build_fact_return_exchange(rr_df, ri_df, "run-1")
    assert fact_re.count() == 2
    rows = {r.return_id: r for r in fact_re.collect()}

    r1 = rows[1]
    assert r1.action_type == "exchange"
    assert r1.returned_variant_key == 201
    assert r1.exchanged_variant_key == 202
    assert r1.refund_amount_vnd == 0

    r2 = rows[2]
    assert r2.action_type == "refund"
    assert r2.refund_amount_vnd == 350000


def test_build_fact_inventory_daily_snapshot(spark):
    inv_schema = StructType([
        StructField("variant_id", LongType(), False),
        StructField("on_hand", IntegerType(), False),
        StructField("reserved", IntegerType(), False),
    ])
    store_inv_schema = StructType([
        StructField("store_id", LongType(), False),
        StructField("variant_id", LongType(), False),
        StructField("on_hand", IntegerType(), False),
        StructField("reserved", IntegerType(), False),
    ])
    pv_schema = StructType([
        StructField("variant_id", LongType(), False),
        StructField("product_id", LongType(), False),
        StructField("cost_price_vnd", LongType(), True),
    ])

    inv_df = spark.createDataFrame([(101, 50, 5)], inv_schema)
    store_inv_df = spark.createDataFrame([(1, 101, 5, 1), (1, 102, 0, 0)], store_inv_schema)
    pv_df = spark.createDataFrame([(101, 10, 100000), (102, 10, 150000)], pv_schema)

    snap_df = build_fact_inventory_daily_snapshot(inv_df, store_inv_df, pv_df, "2026-08-01", "run-1")
    assert snap_df.count() == 3

    rows = snap_df.collect()
    wh = [r for r in rows if r.location_type == "warehouse"][0]
    assert wh.on_hand_quantity == 50
    assert wh.inventory_value_cost_vnd == 50 * 100000
    assert wh.is_low_stock is False
    assert wh.is_out_of_stock is False

    oos = [r for r in rows if r.variant_key == 102][0]
    assert oos.is_out_of_stock is True
    assert oos.is_low_stock is True


def test_build_mart_sales_daily(spark):
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

    d = date(2026, 8, 1)
    fo_df = spark.createDataFrame([
        (1, d, "online", 0, True, False),
        (2, d, "online", 0, False, True),
    ], fo_schema)
    foi_df = spark.createDataFrame([
        (1, 10, 2, 600000, 240000, 360000),
        (2, 10, 1, 300000, 120000, 180000),
    ], foi_schema)
    dp_df = spark.createDataFrame([(10, 1, "Áo Nam")], dp_schema)

    mart_df = build_mart_sales_daily(fo_df, foi_df, dp_df, "run-1")
    assert mart_df.count() == 1
    row = mart_df.collect()[0]
    assert row.total_orders == 2
    assert row.successful_orders == 1
    assert row.boom_orders == 1
    assert row.items_sold == 2
    assert row.gross_revenue_vnd == 600000
    assert row.cogs_vnd == 240000
    assert row.gross_profit_vnd == 360000
    assert row.gross_profit_margin_pct == 60.0


def test_build_mart_logistics_performance(spark):
    fs_schema = StructType([
        StructField("shipment_date", DateType(), False),
        StructField("staff_key", LongType(), False),
        StructField("status", StringType(), False),
        StructField("is_boom", BooleanType(), False),
        StructField("is_on_time", BooleanType(), True),
        StructField("delivery_duration_minutes", DoubleType(), True),
        StructField("cod_amount_collected_vnd", LongType(), True),
    ])
    ds_schema = StructType([
        StructField("staff_key", LongType(), False),
        StructField("staff_code", StringType(), False),
        StructField("assigned_city_id", LongType(), False),
        StructField("assigned_city_name", StringType(), False),
    ])

    d = date(2026, 8, 1)
    fs_df = spark.createDataFrame([
        (d, 10, "delivered", False, True, 45.0, 500000),
        (d, 10, "failed", True, None, 60.0, 0),
    ], fs_schema)
    ds_df = spark.createDataFrame([(10, "DK-SHIP-01", 1, "Hà Nội")], ds_schema)

    mart_df = build_mart_logistics_performance(fs_df, ds_df, "run-1")
    assert mart_df.count() == 1
    row = mart_df.collect()[0]
    assert row.total_shipments == 2
    assert row.delivered_count == 1
    assert row.boom_count == 1
    assert row.boom_rate_pct == 50.0
    assert row.on_time_rate_pct == 100.0
    assert row.total_cod_collected_vnd == 500000


def test_build_mart_product_returns(spark):
    fr_schema = StructType([
        StructField("return_date", DateType(), False),
        StructField("returned_variant_key", LongType(), False),
        StructField("action_type", StringType(), False),
        StructField("reason", StringType(), False),
        StructField("returned_quantity", IntegerType(), False),
        StructField("refund_amount_vnd", LongType(), False),
    ])
    dv_schema = StructType([
        StructField("variant_key", LongType(), False),
        StructField("product_id", LongType(), False),
        StructField("product_name", StringType(), False),
        StructField("sku", StringType(), False),
        StructField("size", StringType(), False),
        StructField("color", StringType(), False),
    ])

    d = date(2026, 8, 2)
    fr_df = spark.createDataFrame([(d, 101, "exchange", "wrong_size", 2, 0)], fr_schema)
    dv_df = spark.createDataFrame([(101, 10, "Áo Polo", "POLO-M", "M", "White")], dv_schema)

    mart_df = build_mart_product_returns(fr_df, dv_df, "run-1")
    assert mart_df.count() == 1
    row = mart_df.collect()[0]
    assert row.total_returned_quantity == 2
    assert row.action_type == "exchange"
    assert row.size == "M"


def test_build_mart_inventory_health(spark):
    fi_schema = StructType([
        StructField("snapshot_date", DateType(), False),
        StructField("location_type", StringType(), False),
        StructField("location_id", LongType(), False),
        StructField("variant_key", LongType(), False),
        StructField("product_key", LongType(), False),
        StructField("on_hand_quantity", IntegerType(), False),
        StructField("inventory_value_cost_vnd", LongType(), False),
        StructField("is_low_stock", BooleanType(), False),
        StructField("is_out_of_stock", BooleanType(), False),
    ])
    dp_schema = StructType([
        StructField("product_key", LongType(), False),
        StructField("category_id", LongType(), False),
        StructField("category_name", StringType(), False),
    ])

    d = date(2026, 8, 1)
    fi_df = spark.createDataFrame([
        (d, "warehouse", 0, 101, 10, 50, 5000000, False, False),
        (d, "warehouse", 0, 102, 10, 0, 0, True, True),
    ], fi_schema)
    dp_df = spark.createDataFrame([(10, 1, "Áo Nam")], dp_schema)

    mart_df = build_mart_inventory_health(fi_df, dp_df, "run-1")
    assert mart_df.count() == 1
    row = mart_df.collect()[0]
    assert row.total_variants == 2
    assert row.out_of_stock_count == 1
    assert row.low_stock_count == 1
    assert row.total_on_hand_units == 50
    assert row.total_inventory_value_vnd == 5000000
