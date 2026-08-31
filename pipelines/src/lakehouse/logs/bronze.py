SOURCE_SYSTEM = "ecommerce-api-access-log"
BRONZE_EVENTS_TABLE = "lakehouse.bronze.web_events"
BRONZE_QUARANTINE_TABLE = "lakehouse.quarantine.bronze_corrupt_logs"

BRONZE_EVENTS_DDL = f"""
CREATE TABLE IF NOT EXISTS {BRONZE_EVENTS_TABLE} (
    event_id            STRING                          COMMENT 'Unique event identifier mapped from request.id',
    event_ts            TIMESTAMP                       COMMENT 'Event generation timestamp in UTC',
    observed_timestamp  TIMESTAMP                       COMMENT 'Timestamp when event was recorded by container',
    schema              STRUCT<name: STRING, version: STRING>,
    service             STRUCT<name: STRING, version: STRING, environment: STRING, instance_id: STRING>,
    severity_number     INT,
    severity_text       STRING,
    trace_id            STRING,
    span_id             STRING,
    event               STRUCT<name: STRING, category: STRING, kind: STRING, outcome: STRING, duration_ns: BIGINT>,
    http                STRUCT<request_method: STRING, route: STRING, status_code: INT>,
    request             STRUCT<id: STRING>,
    actor               STRUCT<type: STRING, key: STRING>,
    client              STRUCT<user_agent: STRING>,
    ecommerce           STRUCT<action: STRING, product_key: STRING, variant_key: STRING, search_query: STRING, search_redacted: BOOLEAN, filters: MAP<STRING, STRING>>,
    error               STRUCT<code: STRING, type: STRING>,
    data_origin         STRING,
    _run_id             STRING                          COMMENT 'Airflow/Spark batch execution run ID',
    _source_system      STRING                          COMMENT 'Source system identifier',
    _source_file        STRING                          COMMENT 'Source .jsonl.gz S3 URI',
    _ingested_at        TIMESTAMP                       COMMENT 'UTC timestamp when record was committed to Bronze'
)
USING iceberg
PARTITIONED BY (days(event_ts))
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
"""

BRONZE_QUARANTINE_DDL = f"""
CREATE TABLE IF NOT EXISTS {BRONZE_QUARANTINE_TABLE} (
    raw_corrupt_record    STRING                          COMMENT 'Raw unparseable line or malformed JSON text',
    error_message         STRING                          COMMENT 'Diagnostic error description',
    quarantine_stage      STRING                          COMMENT 'Pipeline isolation stage',
    _run_id               STRING                          COMMENT 'Batch execution run ID',
    _source_system        STRING                          COMMENT 'Source system identifier',
    _source_file          STRING                          COMMENT 'Source .jsonl.gz S3 URI containing corrupt line',
    _quarantined_at       TIMESTAMP                       COMMENT 'UTC timestamp when record was routed to quarantine'
)
USING iceberg
PARTITIONED BY (days(_quarantined_at))
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
"""

try:
    from pyspark.sql import DataFrame, SparkSession
    from pyspark.sql.functions import col, current_timestamp, input_file_name, lit, to_timestamp
    from pyspark.sql.types import (
        BooleanType,
        IntegerType,
        LongType,
        MapType,
        StringType,
        StructField,
        StructType,
    )

    OTEL_LOG_SCHEMA = StructType([
        StructField("schema", StructType([
            StructField("name", StringType(), False),
            StructField("version", StringType(), False),
        ]), False),
        StructField("timestamp", StringType(), False),
        StructField("observed_timestamp", StringType(), False),
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
        StructField("_corrupt_record", StringType(), True),
    ])

    def ensure_bronze_tables(spark: SparkSession) -> None:
        """Ensure namespaces and tables exist in Polaris catalog."""
        spark.sql("CREATE NAMESPACE IF NOT EXISTS lakehouse.bronze")
        spark.sql("CREATE NAMESPACE IF NOT EXISTS lakehouse.quarantine")
        spark.sql(BRONZE_EVENTS_DDL)
        spark.sql(BRONZE_QUARANTINE_DDL)

    def get_committed_landing_files(spark: SparkSession, query_date: str) -> set[str]:
        """Retrieve distinct _source_file paths for a target date with partition & column pruning."""
        try:
            df = (
                spark.read.table(BRONZE_EVENTS_TABLE)
                .filter(col("event_ts") >= f"{query_date} 00:00:00")
                .filter(col("event_ts") <= f"{query_date} 23:59:59")
                .select("_source_file")
                .distinct()
            )
            return set(row[0] for row in df.collect())
        except Exception:
            return set()

    def transform_valid_logs(valid_df: DataFrame, run_id: str) -> DataFrame:
        """Enrich valid OpenTelemetry log records with event keys and technical lineage metadata."""
        df = valid_df
        if "_source_file" not in df.columns:
            df = df.withColumn("_source_file", input_file_name())
        return (
            df
            .withColumn("event_id", col("request.id"))
            .withColumn("event_ts", to_timestamp(col("timestamp")))
            .withColumn("observed_timestamp", to_timestamp(col("observed_timestamp")))
            .withColumn("_run_id", lit(run_id))
            .withColumn("_source_system", lit(SOURCE_SYSTEM))
            .withColumn("_ingested_at", current_timestamp())
            .drop("_corrupt_record", "timestamp")
        )

    def transform_corrupt_logs(corrupt_df: DataFrame, run_id: str) -> DataFrame:
        """Format corrupt records for the quarantine table."""
        df = corrupt_df
        if "_source_file" not in df.columns:
            df = df.withColumn("_source_file", input_file_name())
        return (
            df
            .select(
                col("_corrupt_record").alias("raw_corrupt_record"),
                lit("Malformed JSON syntax or schema validation failure").alias("error_message"),
                lit("bronze_landing_ingestion").alias("quarantine_stage"),
                lit(run_id).alias("_run_id"),
                lit(SOURCE_SYSTEM).alias("_source_system"),
                col("_source_file"),
                current_timestamp().alias("_quarantined_at"),
            )
        )

except ImportError:
    OTEL_LOG_SCHEMA = None
    ensure_bronze_tables = None
    get_committed_landing_files = None
    transform_valid_logs = None
    transform_corrupt_logs = None
