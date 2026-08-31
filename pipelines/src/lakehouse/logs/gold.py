from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyspark.sql import DataFrame, SparkSession

try:
    from pyspark.sql import functions as F
except ImportError:
    F = None  # type: ignore

FACT_WEB_EVENTS_TABLE = "lakehouse.gold.fact_web_events"
MART_HOURLY_ROUTE_METRICS_TABLE = "lakehouse.gold.mart_hourly_route_metrics"
MART_DAILY_PRODUCT_DEMAND_TABLE = "lakehouse.gold.mart_daily_product_demand"

FACT_WEB_EVENTS_DDL = f"""
CREATE TABLE IF NOT EXISTS {FACT_WEB_EVENTS_TABLE} (
    event_id                STRING                          COMMENT 'Unique event identifier',
    event_ts                TIMESTAMP                       COMMENT 'Event generation timestamp in UTC',
    event_date              DATE                            COMMENT 'Partition date derived from event_ts',
    actor_key               STRING                          COMMENT 'Identifier for actor (customer_id or anonymous token)',
    actor_type              STRING                          COMMENT 'Actor classification (customer, anonymous, admin)',
    http_request_method     STRING                          COMMENT 'HTTP verb (GET, POST, etc.)',
    http_route              STRING                          COMMENT 'Normalized endpoint route',
    http_status_code        INT                             COMMENT 'HTTP response status code',
    ecommerce_action        STRING                          COMMENT 'High-level business action',
    product_key             STRING                          COMMENT 'Product master key',
    variant_key             STRING                          COMMENT 'Product variant key',
    duration_ms             DOUBLE                          COMMENT 'Request execution duration in milliseconds',
    is_success              BOOLEAN                         COMMENT 'True if HTTP status is 2xx/3xx',
    is_client_error         BOOLEAN                         COMMENT 'True if HTTP status is 4xx',
    is_server_error         BOOLEAN                         COMMENT 'True if HTTP status is 5xx',
    is_slow_request         BOOLEAN                         COMMENT 'True if duration_ms >= 1000ms',
    _gold_ingested_at       TIMESTAMP                       COMMENT 'UTC timestamp when record was written to Gold',
    _source_run_id          STRING                          COMMENT 'Airflow/Spark execution batch run ID'
)
USING iceberg
PARTITIONED BY (days(event_ts))
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
"""

MART_HOURLY_ROUTE_METRICS_DDL = f"""
CREATE TABLE IF NOT EXISTS {MART_HOURLY_ROUTE_METRICS_TABLE} (
    metric_date             DATE                            COMMENT 'Metric observation date',
    metric_hour             INT                             COMMENT 'Hour of day (0-23)',
    http_route              STRING                          COMMENT 'Normalized API endpoint route',
    http_request_method     STRING                          COMMENT 'HTTP method',
    total_requests          BIGINT                          COMMENT 'Total request count in this hourly window',
    success_2xx_count       BIGINT                          COMMENT 'Successful 2xx request count',
    client_error_4xx_count  BIGINT                          COMMENT 'Client error 4xx request count',
    server_error_5xx_count  BIGINT                          COMMENT 'Server error 5xx request count',
    error_rate_pct          DOUBLE                          COMMENT 'Overall error rate percentage ((4xx+5xx)/total * 100)',
    avg_duration_ms         DOUBLE                          COMMENT 'Average duration in milliseconds',
    p50_duration_ms         DOUBLE                          COMMENT 'Median duration in milliseconds',
    p95_duration_ms         DOUBLE                          COMMENT '95th percentile duration in milliseconds',
    p99_duration_ms         DOUBLE                          COMMENT '99th percentile duration in milliseconds',
    _gold_ingested_at       TIMESTAMP                       COMMENT 'UTC timestamp when aggregation was recorded',
    _source_run_id          STRING                          COMMENT 'Airflow/Spark execution batch run ID'
)
USING iceberg
PARTITIONED BY (metric_date)
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
"""

MART_DAILY_PRODUCT_DEMAND_DDL = f"""
CREATE TABLE IF NOT EXISTS {MART_DAILY_PRODUCT_DEMAND_TABLE} (
    metric_date             DATE                            COMMENT 'Metric observation date',
    product_key             STRING                          COMMENT 'Product master key',
    detail_view_count       BIGINT                          COMMENT 'Product detail page view count',
    cart_add_count          BIGINT                          COMMENT 'Add to cart interaction count',
    cart_remove_count       BIGINT                          COMMENT 'Remove from cart interaction count',
    wishlist_add_count      BIGINT                          COMMENT 'Add to wishlist interaction count',
    checkout_quote_count    BIGINT                          COMMENT 'Checkout quote interaction count',
    unique_visitors_count   BIGINT                          COMMENT 'Distinct actor count interacting with product',
    cart_to_view_rate_pct   DOUBLE                          COMMENT 'Conversion percentage from view to cart add',
    _gold_ingested_at       TIMESTAMP                       COMMENT 'UTC timestamp when aggregation was recorded',
    _source_run_id          STRING                          COMMENT 'Airflow/Spark execution batch run ID'
)
USING iceberg
PARTITIONED BY (metric_date)
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
"""


def ensure_logs_gold_tables(spark: SparkSession) -> None:
    spark.sql("CREATE NAMESPACE IF NOT EXISTS lakehouse.gold")
    spark.sql(FACT_WEB_EVENTS_DDL)
    spark.sql(MART_HOURLY_ROUTE_METRICS_DDL)
    spark.sql(MART_DAILY_PRODUCT_DEMAND_DDL)


def build_fact_web_events(silver_df: DataFrame, run_id: str) -> DataFrame:
    duration_ms_col = F.round(F.col("event_duration_ns") / 1000000.0, 3)
    return (
        silver_df
        .withColumn("event_date", F.to_date(F.col("event_ts")))
        .withColumn("product_key", F.col("ecommerce_product_key"))
        .withColumn("variant_key", F.col("ecommerce_variant_key"))
        .withColumn("duration_ms", duration_ms_col)
        .withColumn("is_success", F.col("http_status_code") < 400)
        .withColumn("is_client_error", (F.col("http_status_code") >= 400) & (F.col("http_status_code") < 500))
        .withColumn("is_server_error", F.col("http_status_code") >= 500)
        .withColumn("is_slow_request", duration_ms_col >= 1000.0)
        .withColumn("_gold_ingested_at", F.current_timestamp())
        .withColumn("_source_run_id", F.lit(run_id))
        .select(
            "event_id",
            "event_ts",
            "event_date",
            "actor_key",
            "actor_type",
            "http_request_method",
            "http_route",
            "http_status_code",
            "ecommerce_action",
            "product_key",
            "variant_key",
            "duration_ms",
            "is_success",
            "is_client_error",
            "is_server_error",
            "is_slow_request",
            "_gold_ingested_at",
            "_source_run_id",
        )
    )


def build_mart_hourly_route_metrics(fact_df: DataFrame, run_id: str) -> DataFrame:
    percentiles = F.percentile_approx(F.col("duration_ms"), [0.5, 0.95, 0.99])

    return (
        fact_df
        .withColumn("metric_hour", F.hour(F.col("event_ts")))
        .groupBy("event_date", "metric_hour", "http_route", "http_request_method")
        .agg(
            F.count("*").alias("total_requests"),
            F.sum(F.when(F.col("is_success"), 1).otherwise(0)).alias("success_2xx_count"),
            F.sum(F.when(F.col("is_client_error"), 1).otherwise(0)).alias("client_error_4xx_count"),
            F.sum(F.when(F.col("is_server_error"), 1).otherwise(0)).alias("server_error_5xx_count"),
            F.round(F.avg("duration_ms"), 3).alias("avg_duration_ms"),
            percentiles.alias("pcts"),
        )
        .withColumn(
            "error_rate_pct",
            F.round(
                ((F.col("client_error_4xx_count") + F.col("server_error_5xx_count")) / F.col("total_requests")) * 100.0,
                2,
            ),
        )
        .withColumn("p50_duration_ms", F.round(F.col("pcts")[0], 3))
        .withColumn("p95_duration_ms", F.round(F.col("pcts")[1], 3))
        .withColumn("p99_duration_ms", F.round(F.col("pcts")[2], 3))
        .withColumn("metric_date", F.col("event_date"))
        .withColumn("_gold_ingested_at", F.current_timestamp())
        .withColumn("_source_run_id", F.lit(run_id))
        .select(
            "metric_date",
            "metric_hour",
            "http_route",
            "http_request_method",
            "total_requests",
            "success_2xx_count",
            "client_error_4xx_count",
            "server_error_5xx_count",
            "error_rate_pct",
            "avg_duration_ms",
            "p50_duration_ms",
            "p95_duration_ms",
            "p99_duration_ms",
            "_gold_ingested_at",
            "_source_run_id",
        )
    )


def build_mart_daily_product_demand(fact_df: DataFrame, run_id: str) -> DataFrame:
    product_events = fact_df.filter(F.col("product_key").isNotNull() & (F.col("product_key") != ""))

    return (
        product_events
        .groupBy("event_date", "product_key")
        .agg(
            F.sum(F.when(F.col("ecommerce_action") == "product_detail", 1).otherwise(0)).alias("detail_view_count"),
            F.sum(F.when(F.col("ecommerce_action") == "cart_add", 1).otherwise(0)).alias("cart_add_count"),
            F.sum(F.when(F.col("ecommerce_action") == "cart_remove", 1).otherwise(0)).alias("cart_remove_count"),
            F.sum(F.when(F.col("ecommerce_action") == "wishlist_add", 1).otherwise(0)).alias("wishlist_add_count"),
            F.sum(F.when(F.col("ecommerce_action") == "checkout_quote", 1).otherwise(0)).alias("checkout_quote_count"),
            F.countDistinct("actor_key").alias("unique_visitors_count"),
        )
        .withColumn(
            "cart_to_view_rate_pct",
            F.when(
                F.col("detail_view_count") > 0,
                F.round((F.col("cart_add_count") / F.col("detail_view_count")) * 100.0, 2),
            ).otherwise(0.0),
        )
        .withColumn("metric_date", F.col("event_date"))
        .withColumn("_gold_ingested_at", F.current_timestamp())
        .withColumn("_source_run_id", F.lit(run_id))
        .select(
            "metric_date",
            "product_key",
            "detail_view_count",
            "cart_add_count",
            "cart_remove_count",
            "wishlist_add_count",
            "checkout_quote_count",
            "unique_visitors_count",
            "cart_to_view_rate_pct",
            "_gold_ingested_at",
            "_source_run_id",
        )
    )
