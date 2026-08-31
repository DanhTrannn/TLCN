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
    DoubleType,
    IntegerType,
    LongType,
    MapType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)
from lakehouse.logs.gold import (
    FACT_WEB_EVENTS_TABLE,
    MART_DAILY_PRODUCT_DEMAND_TABLE,
    MART_HOURLY_ROUTE_METRICS_TABLE,
    build_fact_web_events,
    build_mart_daily_product_demand,
    build_mart_hourly_route_metrics,
)


@pytest.fixture(scope="session")
def spark():
    return SparkSession.builder.master("local[1]").appName("test-logs-gold").getOrCreate()


def _make_silver_df(spark):
    schema = StructType([
        StructField("event_id", StringType(), False),
        StructField("event_ts", TimestampType(), False),
        StructField("observed_timestamp", TimestampType(), False),
        StructField("schema_name", StringType(), True),
        StructField("schema_version", StringType(), True),
        StructField("service_name", StringType(), False),
        StructField("service_version", StringType(), False),
        StructField("service_environment", StringType(), False),
        StructField("service_instance_id", StringType(), False),
        StructField("severity_number", IntegerType(), False),
        StructField("severity_text", StringType(), False),
        StructField("trace_id", StringType(), True),
        StructField("span_id", StringType(), True),
        StructField("event_name", StringType(), False),
        StructField("event_category", StringType(), False),
        StructField("event_kind", StringType(), False),
        StructField("event_outcome", StringType(), False),
        StructField("event_duration_ns", LongType(), False),
        StructField("http_request_method", StringType(), False),
        StructField("http_route", StringType(), False),
        StructField("http_status_code", IntegerType(), False),
        StructField("request_id", StringType(), False),
        StructField("actor_type", StringType(), False),
        StructField("actor_key", StringType(), True),
        StructField("client_user_agent", StringType(), True),
        StructField("ecommerce_action", StringType(), False),
        StructField("ecommerce_product_key", StringType(), True),
        StructField("ecommerce_variant_key", StringType(), True),
        StructField("ecommerce_search_query", StringType(), True),
        StructField("ecommerce_search_redacted", BooleanType(), True),
        StructField("ecommerce_filters", MapType(StringType(), StringType()), True),
        StructField("error_code", StringType(), True),
        StructField("error_type", StringType(), True),
        StructField("data_origin", StringType(), False),
        StructField("_silver_ingested_at", TimestampType(), False),
        StructField("_source_bronze_run_id", StringType(), False),
    ])
    ts1 = datetime(2026, 8, 15, 10, 15, 0)
    ts2 = datetime(2026, 8, 15, 10, 30, 0)
    ts3 = datetime(2026, 8, 15, 11, 0, 0)
    ingested = datetime(2026, 8, 15, 12, 0, 0)
    data = [
        ("e-1", ts1, ts1, "s", "1", "api", "1", "prod", "i-1", 9, "INFO", None, None,
         "req", "http", "server", "OK", 50_000_000, "GET", "/products", 200, "r-1",
         "anonymous", "act-1", "ua", "product_detail", "p-100", "v-100", None, False, None,
         None, None, "prod", ingested, "run-1"),
        ("e-2", ts2, ts2, "s", "1", "api", "1", "prod", "i-1", 9, "INFO", None, None,
         "req", "http", "server", "OK", 1_500_000_000, "POST", "/cart/items", 201, "r-2",
         "customer", "act-1", "ua", "cart_add", "p-100", "v-100", None, False, None,
         None, None, "prod", ingested, "run-1"),
        ("e-3", ts3, ts3, "s", "1", "api", "1", "prod", "i-1", 9, "INFO", None, None,
         "req", "http", "server", "FAIL", 80_000_000, "GET", "/products", 404, "r-3",
         "customer", "act-2", "ua", "product_detail", "p-200", "v-200", None, False, None,
         "NOT_FOUND", "client", "prod", ingested, "run-1"),
    ]
    return spark.createDataFrame(data, schema)


def test_build_fact_web_events(spark):
    silver_df = _make_silver_df(spark)
    fact_df = build_fact_web_events(silver_df, "test-run")

    assert fact_df.count() == 3
    rows = {r.event_id: r for r in fact_df.collect()}

    # Check metrics on fast successful request
    assert rows["e-1"].duration_ms == 50.0
    assert rows["e-1"].is_success is True
    assert rows["e-1"].is_client_error is False
    assert rows["e-1"].is_slow_request is False

    # Check metrics on slow request (> 1000ms)
    assert rows["e-2"].duration_ms == 1500.0
    assert rows["e-2"].is_success is True
    assert rows["e-2"].is_slow_request is True

    # Check client error request (404)
    assert rows["e-3"].is_success is False
    assert rows["e-3"].is_client_error is True
    assert rows["e-3"].is_server_error is False


def test_build_mart_hourly_route_metrics(spark):
    silver_df = _make_silver_df(spark)
    fact_df = build_fact_web_events(silver_df, "test-run")
    mart_df = build_mart_hourly_route_metrics(fact_df, "test-run")

    # Grouped by (event_date, hour, route, method):
    # - (2026-08-15, 10, /products, GET): 1 request, 200
    # - (2026-08-15, 10, /cart/items, POST): 1 request, 201
    # - (2026-08-15, 11, /products, GET): 1 request, 404
    assert mart_df.count() == 3
    rows = mart_df.collect()
    products_h11 = [r for r in rows if r.metric_hour == 11 and r.http_route == "/products"][0]

    assert products_h11.total_requests == 1
    assert products_h11.client_error_4xx_count == 1
    assert products_h11.error_rate_pct == 100.0


def test_build_mart_daily_product_demand(spark):
    silver_df = _make_silver_df(spark)
    fact_df = build_fact_web_events(silver_df, "test-run")
    demand_df = build_mart_daily_product_demand(fact_df, "test-run")

    # p-100 has 1 view, 1 cart_add -> cart_to_view_rate = 100.0%
    # p-200 has 1 view, 0 cart_add -> cart_to_view_rate = 0.0%
    assert demand_df.count() == 2
    rows = {r.product_key: r for r in demand_df.collect()}

    assert rows["p-100"].detail_view_count == 1
    assert rows["p-100"].cart_add_count == 1
    assert rows["p-100"].cart_to_view_rate_pct == 100.0
    assert rows["p-100"].unique_visitors_count == 1

    assert rows["p-200"].detail_view_count == 1
    assert rows["p-200"].cart_add_count == 0
    assert rows["p-200"].cart_to_view_rate_pct == 0.0
