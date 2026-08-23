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

    window = Window.partitionBy("event_id").orderBy(F.col("_ingested_at").desc())
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
