from lakehouse.sql import identifier, render_sql

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window

LOGS_SILVER_TABLE = "lakehouse.silver.silver_logs"


def ensure_logs_silver_tables(spark: SparkSession) -> None:
    spark.sql("CREATE NAMESPACE IF NOT EXISTS lakehouse.silver")
    spark.sql(render_sql("spark/logs/silver_logs.sql", logs_silver_table=identifier(LOGS_SILVER_TABLE)))


SILVER_LOGS_COLUMNS = [
    "event_id",
    "event_ts",
    "observed_timestamp",
    "schema_name",
    "schema_version",
    "service_name",
    "service_version",
    "service_environment",
    "service_instance_id",
    "severity_number",
    "severity_text",
    "trace_id",
    "span_id",
    "event_name",
    "event_category",
    "event_kind",
    "event_outcome",
    "event_duration_ns",
    "http_request_method",
    "http_route",
    "http_status_code",
    "request_id",
    "actor_type",
    "actor_key",
    "client_user_agent",
    "ecommerce_action",
    "ecommerce_product_key",
    "ecommerce_variant_key",
    "ecommerce_search_query",
    "ecommerce_search_redacted",
    "ecommerce_filters",
    "error_code",
    "error_type",
    "data_origin",
    "_silver_ingested_at",
    "_source_bronze_run_id",
]


def ingest_logs_to_silver(
    spark: SparkSession,
    bronze_df: DataFrame,
    run_id: str,
    target_path: str,
    _write_format: str = "iceberg",
) -> int:
    if bronze_df.limit(1).count() == 0:
        return 0

    window = Window.partitionBy("event_id").orderBy(F.col("_ingested_at").desc())
    deduped = bronze_df.withColumn("_rn", F.row_number().over(window)).filter(F.col("_rn") == 1).drop("_rn")

    enriched = (
        deduped.withColumn("schema_name", F.col("schema.name"))
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
    )

    final_df = enriched.select(*SILVER_LOGS_COLUMNS)

    count = final_df.count()
    if count == 0:
        return 0

    if _write_format == "iceberg":
        final_df.writeTo(LOGS_SILVER_TABLE).append()
    else:
        final_df.write.format(_write_format).mode("append").save(target_path)

    return count
