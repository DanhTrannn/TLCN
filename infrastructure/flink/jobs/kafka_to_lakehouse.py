"""PyFlink Pure Streaming Job: Kafka → Medallion Lakehouse (Landing, Bronze, Silver, Gold).

Consumes access logs in real time from Kafka topic ``ecommerce.access_logs``,
transforms timestamps using Pendulum in the Asia/Ho_Chi_Minh timezone,
and writes concurrently into all 4 Medallion layers using an Apache Flink StatementSet
with Merge-on-Read Iceberg tables:
  1. lakehouse.landing.access_logs     (Raw JSON + routing metadata)
  2. lakehouse.bronze.web_events       (OpenTelemetry structured events)
  3. lakehouse.silver.silver_logs      (Flattened, sanitized, typed log records)
  4. lakehouse.gold.fact_web_events    (Real-time dimensional facts with duration & status flags)

Environment variables (injected by docker-compose / with-polaris-credentials.sh):
    POLARIS_FLINK_CLIENT_ID      – Polaris OAuth2 client id
    POLARIS_FLINK_CLIENT_SECRET  – Polaris OAuth2 client secret
    POLARIS_REALM                – Polaris realm name  (default: POLARIS)
    KAFKA_BOOTSTRAP_SERVERS      – Kafka broker address (default: kafka:9092)
    MINIO_ENDPOINT               – MinIO S3 endpoint   (default: http://minio:9000)
    AWS_ACCESS_KEY_ID            – MinIO access key     (default: minioadmin)
    AWS_SECRET_ACCESS_KEY        – MinIO secret key     (default: password)
"""

import json
import logging
import os
import uuid

import pendulum

VN_TZ = pendulum.timezone("Asia/Ho_Chi_Minh")

from pyflink.common import Configuration, Row
from pyflink.common.serialization import SimpleStringSchema
from pyflink.common.typeinfo import Types
from pyflink.common.watermark_strategy import WatermarkStrategy
from pyflink.datastream import StreamExecutionEnvironment, CheckpointingMode
from pyflink.datastream.connectors.kafka import (
    KafkaSource,
    KafkaOffsetsInitializer,
)
from pyflink.datastream.functions import MapFunction
from pyflink.table import StreamTableEnvironment, EnvironmentSettings, Schema
from pyflink.table.types import DataTypes

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s – %(message)s",
)
log = logging.getLogger("flink.kafka_to_lakehouse")

# ---------------------------------------------------------------------------
# Configuration from environment
# ---------------------------------------------------------------------------
POLARIS_CLIENT_ID = os.environ["POLARIS_FLINK_CLIENT_ID"]
POLARIS_CLIENT_SECRET = os.environ["POLARIS_FLINK_CLIENT_SECRET"]
POLARIS_REALM = os.environ.get("POLARIS_REALM", "POLARIS")
KAFKA_BOOTSTRAP = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT", "http://minio:9000")
S3_ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY_ID", "minioadmin")
S3_SECRET_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "password")

KAFKA_TOPIC = "ecommerce.access_logs"
KAFKA_GROUP_ID = "flink-lakehouse-pure-stream"
CHECKPOINT_INTERVAL_MS = 10_000  # 10 seconds micro-commits


# ---------------------------------------------------------------------------
# Event parsing with Pendulum Asia/Ho_Chi_Minh timezone
# ---------------------------------------------------------------------------
class ParseAccessLog(MapFunction):
    """Parse raw JSON string from Kafka into multi-layer schema fields.

    Converts timestamps to Asia/Ho_Chi_Minh timezone via Pendulum.
    Computes duration_ms and HTTP status flags for real-time Gold facts.
    """

    def map(self, raw: str):  # noqa: ANN001
        try:
            msg = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            log.warning("Unparseable message dropped: %.120s", raw)
            return None

        now_dt = pendulum.now(VN_TZ)
        now_ts_str = now_dt.strftime("%Y-%m-%d %H:%M:%S.%f")

        # Parse event timestamp in Asia/Ho_Chi_Minh
        ts_str: str = msg.get("timestamp") or ""
        try:
            event_dt = pendulum.parse(ts_str).in_timezone(VN_TZ)
        except Exception:
            event_dt = now_dt
        event_ts_str = event_dt.strftime("%Y-%m-%d %H:%M:%S.%f")
        event_date_str = event_dt.strftime("%Y-%m-%d")

        # Observed timestamp in container
        obs_str: str = msg.get("observed_timestamp") or ""
        try:
            obs_dt = pendulum.parse(obs_str).in_timezone(VN_TZ)
        except Exception:
            obs_dt = event_dt
        obs_ts_str = obs_dt.strftime("%Y-%m-%d %H:%M:%S.%f")

        # Nested objects with safe defaults
        request = msg.get("request") or {}
        service = msg.get("service") or {}
        http = msg.get("http") or {}
        event = msg.get("event") or {}
        actor = msg.get("actor") or {}
        client = msg.get("client") or {}
        ecommerce = msg.get("ecommerce") or {}
        error = msg.get("error") or {}
        schema = msg.get("schema") or {}

        event_id: str = str(request.get("id") or uuid.uuid4())
        schema_name: str = schema.get("name") or "ecommerce.access"
        schema_version: str = schema.get("version") or "1.0.0"
        service_name: str = service.get("name") or "ecommerce-api"
        service_version: str = service.get("version") or "0.1.0"
        service_env: str = service.get("environment") or "production"
        service_instance_id: str = service.get("instance_id") or service_name
        severity_number: int = int(msg.get("severity_number") or 9)
        severity_text: str = msg.get("severity_text") or "INFO"
        trace_id: str = msg.get("trace_id") or ""
        span_id: str = msg.get("span_id") or ""
        event_name: str = event.get("name") or "http.server.request"
        event_category: str = event.get("category") or "web"
        event_kind: str = event.get("kind") or "event"
        event_outcome: str = event.get("outcome") or "success"
        duration_ns: int = int(event.get("duration_ns") or 0)
        duration_ms: float = round(duration_ns / 1_000_000.0, 3)

        http_method: str = (http.get("request_method") or "UNKNOWN").upper()
        http_route: str = http.get("route") or "UNKNOWN"
        http_status: int = int(http.get("status_code") or 200)
        is_success: bool = http_status < 400
        is_client_error: bool = (http_status >= 400) and (http_status < 500)
        is_server_error: bool = http_status >= 500
        is_slow_request: bool = duration_ms >= 1000.0

        actor_type: str = actor.get("type") or "anonymous"
        actor_key: str = actor.get("key") or ""
        client_user_agent: str = client.get("user_agent") or ""
        action: str = ecommerce.get("action") or "unknown"
        product_key: str = ecommerce.get("product_key") or ""
        variant_key: str = ecommerce.get("variant_key") or ""
        search_query: str = ecommerce.get("search_query") or ""
        search_redacted: bool = bool(ecommerce.get("search_redacted") or False)

        error_code: str = error.get("code") or ""
        error_type: str = error.get("type") or ""
        data_origin: str = msg.get("data_origin") or "observed"

        return Row(
            event_id,                   # f0
            event_ts_str,               # f1
            now_ts_str,                 # f2
            event_date_str,             # f3
            obs_ts_str,                 # f4
            schema_name,                # f5
            schema_version,             # f6
            service_name,               # f7
            service_version,            # f8
            service_env,                # f9
            service_instance_id,        # f10
            severity_number,            # f11
            severity_text,              # f12
            trace_id,                   # f13
            span_id,                    # f14
            event_name,                 # f15
            event_category,             # f16
            event_kind,                 # f17
            event_outcome,              # f18
            duration_ns,                # f19
            duration_ms,                # f20
            http_method,                # f21
            http_route,                 # f22
            http_status,                # f23
            is_success,                 # f24
            is_client_error,            # f25
            is_server_error,            # f26
            is_slow_request,            # f27
            actor_type,                 # f28
            actor_key,                  # f29
            client_user_agent,          # f30
            action,                     # f31
            product_key,                # f32
            variant_key,                # f33
            search_query,               # f34
            search_redacted,            # f35
            error_code,                 # f36
            error_type,                 # f37
            data_origin,                # f38
            raw,                        # f39
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    # 1. StreamExecutionEnvironment
    config = Configuration()
    env = StreamExecutionEnvironment.get_execution_environment(config)

    # Exactly-Once Checkpointing
    env.enable_checkpointing(CHECKPOINT_INTERVAL_MS, CheckpointingMode.EXACTLY_ONCE)
    env.get_checkpoint_config().set_checkpoint_storage_dir("file:///opt/flink/checkpoints")
    env.get_checkpoint_config().set_min_pause_between_checkpoints(5_000)
    env.get_checkpoint_config().set_checkpoint_timeout(60_000)

    # Table Environment
    t_env = StreamTableEnvironment.create(env, EnvironmentSettings.new_instance().in_streaming_mode().build())
    t_env.get_config().set("pipeline.name", "kafka_to_lakehouse_pure_streaming")

    # 2. Register Polaris Iceberg REST catalog
    t_env.execute_sql(f"""
        CREATE CATALOG lakehouse WITH (
            'type'                   = 'iceberg',
            'catalog-type'           = 'rest',
            'uri'                    = 'http://polaris:8181/api/catalog',
            'credential'             = '{POLARIS_CLIENT_ID}:{POLARIS_CLIENT_SECRET}',
            'warehouse'              = 'lakehouse',
            'scope'                  = 'PRINCIPAL_ROLE:ALL',
            'header.Polaris-Realm'   = '{POLARIS_REALM}',
            'io-impl'                = 'org.apache.iceberg.aws.s3.S3FileIO',
            's3.endpoint'            = '{MINIO_ENDPOINT}',
            's3.path-style-access'   = 'true',
            's3.access-key-id'       = '{S3_ACCESS_KEY}',
            's3.secret-access-key'   = '{S3_SECRET_KEY}'
        )
    """)
    log.info("Iceberg catalog 'lakehouse' registered via Polaris REST")

    # Ensure namespaces exist
    t_env.execute_sql("CREATE DATABASE IF NOT EXISTS lakehouse.landing")
    t_env.execute_sql("CREATE DATABASE IF NOT EXISTS lakehouse.bronze")
    t_env.execute_sql("CREATE DATABASE IF NOT EXISTS lakehouse.silver")
    t_env.execute_sql("CREATE DATABASE IF NOT EXISTS lakehouse.gold")

    # Ensure Merge-on-Read write mode on all 4 tables
    tables_to_ensure = [
        "lakehouse.landing.access_logs",
        "lakehouse.bronze.web_events",
        "lakehouse.silver.silver_logs",
        "lakehouse.gold.fact_web_events",
    ]
    for tbl in tables_to_ensure:
        try:
            t_env.execute_sql(f"""
                ALTER TABLE {tbl} SET (
                    'write.delete.mode' = 'merge-on-read',
                    'write.update.mode' = 'merge-on-read',
                    'write.merge.mode'  = 'merge-on-read'
                )
            """)
        except Exception as exc:
            log.warning("Could not set merge-on-read on %s: %s", tbl, exc)

    log.info("Ensured Merge-On-Read write mode on Lakehouse Medallion tables")

    # 3. Kafka DataStream Source
    kafka_source = (
        KafkaSource.builder()
        .set_bootstrap_servers(KAFKA_BOOTSTRAP)
        .set_topics(KAFKA_TOPIC)
        .set_group_id(KAFKA_GROUP_ID)
        .set_starting_offsets(KafkaOffsetsInitializer.earliest())
        .set_value_only_deserializer(SimpleStringSchema())
        .build()
    )

    raw_stream = env.from_source(
        kafka_source,
        WatermarkStrategy.no_watermarks(),
        "kafka-access-logs-source",
    )

    # 4. Map & Parse JSON
    field_names = [f"f{i}" for i in range(40)]
    field_types = [
        Types.STRING(),   # f0: event_id
        Types.STRING(),   # f1: event_ts_str
        Types.STRING(),   # f2: now_ts_str
        Types.STRING(),   # f3: event_date_str
        Types.STRING(),   # f4: obs_ts_str
        Types.STRING(),   # f5: schema_name
        Types.STRING(),   # f6: schema_version
        Types.STRING(),   # f7: service_name
        Types.STRING(),   # f8: service_version
        Types.STRING(),   # f9: service_env
        Types.STRING(),   # f10: service_instance_id
        Types.INT(),      # f11: severity_number
        Types.STRING(),   # f12: severity_text
        Types.STRING(),   # f13: trace_id
        Types.STRING(),   # f14: span_id
        Types.STRING(),   # f15: event_name
        Types.STRING(),   # f16: event_category
        Types.STRING(),   # f17: event_kind
        Types.STRING(),   # f18: event_outcome
        Types.LONG(),     # f19: duration_ns
        Types.DOUBLE(),   # f20: duration_ms
        Types.STRING(),   # f21: http_method
        Types.STRING(),   # f22: http_route
        Types.INT(),      # f23: http_status
        Types.BOOLEAN(),  # f24: is_success
        Types.BOOLEAN(),  # f25: is_client_error
        Types.BOOLEAN(),  # f26: is_server_error
        Types.BOOLEAN(),  # f27: is_slow_request
        Types.STRING(),   # f28: actor_type
        Types.STRING(),   # f29: actor_key
        Types.STRING(),   # f30: client_user_agent
        Types.STRING(),   # f31: action
        Types.STRING(),   # f32: product_key
        Types.STRING(),   # f33: variant_key
        Types.STRING(),   # f34: search_query
        Types.BOOLEAN(),  # f35: search_redacted
        Types.STRING(),   # f36: error_code
        Types.STRING(),   # f37: error_type
        Types.STRING(),   # f38: data_origin
        Types.STRING(),   # f39: raw
    ]
    parsed_type = Types.ROW_NAMED(field_names, field_types)

    parsed_stream = (
        raw_stream
        .map(ParseAccessLog(), output_type=parsed_type)
        .filter(lambda row: row is not None)
    )

    # 5. Convert DataStream to Table
    parsed_schema = (
        Schema.new_builder()
        .column("f0",  DataTypes.STRING())
        .column("f1",  DataTypes.STRING())
        .column("f2",  DataTypes.STRING())
        .column("f3",  DataTypes.STRING())
        .column("f4",  DataTypes.STRING())
        .column("f5",  DataTypes.STRING())
        .column("f6",  DataTypes.STRING())
        .column("f7",  DataTypes.STRING())
        .column("f8",  DataTypes.STRING())
        .column("f9",  DataTypes.STRING())
        .column("f10", DataTypes.STRING())
        .column("f11", DataTypes.INT())
        .column("f12", DataTypes.STRING())
        .column("f13", DataTypes.STRING())
        .column("f14", DataTypes.STRING())
        .column("f15", DataTypes.STRING())
        .column("f16", DataTypes.STRING())
        .column("f17", DataTypes.STRING())
        .column("f18", DataTypes.STRING())
        .column("f19", DataTypes.BIGINT())
        .column("f20", DataTypes.DOUBLE())
        .column("f21", DataTypes.STRING())
        .column("f22", DataTypes.STRING())
        .column("f23", DataTypes.INT())
        .column("f24", DataTypes.BOOLEAN())
        .column("f25", DataTypes.BOOLEAN())
        .column("f26", DataTypes.BOOLEAN())
        .column("f27", DataTypes.BOOLEAN())
        .column("f28", DataTypes.STRING())
        .column("f29", DataTypes.STRING())
        .column("f30", DataTypes.STRING())
        .column("f31", DataTypes.STRING())
        .column("f32", DataTypes.STRING())
        .column("f33", DataTypes.STRING())
        .column("f34", DataTypes.STRING())
        .column("f35", DataTypes.BOOLEAN())
        .column("f36", DataTypes.STRING())
        .column("f37", DataTypes.STRING())
        .column("f38", DataTypes.STRING())
        .column("f39", DataTypes.STRING())
        .build()
    )

    tbl = t_env.from_data_stream(parsed_stream, parsed_schema)
    t_env.create_temporary_view("raw_events_view", tbl)

    # 6. StatementSet: Multi-sink parallel ingestion to Landing, Bronze, Silver, Gold
    statement_set = t_env.create_statement_set()

    # 6.1 Landing Layer
    statement_set.add_insert_sql("""
        INSERT INTO lakehouse.landing.access_logs
        SELECT
            f0  as event_id,
            CAST(f1 AS TIMESTAMP(6)) as event_ts,
            CAST(f2 AS TIMESTAMP(6)) as ingest_ts,
            f7  as service_name,
            f21 as http_method,
            f22 as http_route,
            f23 as http_status_code,
            f19 as duration_ns,
            f28 as actor_type,
            f31 as ecommerce_action,
            f39 as raw_payload
        FROM raw_events_view
    """)

    # 6.2 Bronze Layer (OpenTelemetry Schema with Structs)
    statement_set.add_insert_sql("""
        INSERT INTO lakehouse.bronze.web_events
        SELECT
            f0 as event_id,
            CAST(f1 AS TIMESTAMP_LTZ(6)) as event_ts,
            CAST(f4 AS TIMESTAMP_LTZ(6)) as observed_timestamp,
            ROW(f5, f6) as `schema`,
            ROW(f7, f8, f9, f10) as service,
            f11 as severity_number,
            f12 as severity_text,
            CASE WHEN f13 = '' THEN CAST(NULL AS STRING) ELSE f13 END as trace_id,
            CASE WHEN f14 = '' THEN CAST(NULL AS STRING) ELSE f14 END as span_id,
            ROW(f15, f16, f17, f18, f19) as `event`,
            ROW(f21, f22, f23) as http,
            ROW(f0) as request,
            ROW(f28, CASE WHEN f29 = '' THEN CAST(NULL AS STRING) ELSE f29 END) as actor,
            ROW(f30) as client,
            ROW(
                f31,
                CASE WHEN f32 = '' THEN CAST(NULL AS STRING) ELSE f32 END,
                CASE WHEN f33 = '' THEN CAST(NULL AS STRING) ELSE f33 END,
                CASE WHEN f34 = '' THEN CAST(NULL AS STRING) ELSE f34 END,
                f35,
                CAST(NULL AS MAP<STRING, STRING>)
            ) as ecommerce,
            ROW(
                CASE WHEN f36 = '' THEN CAST(NULL AS STRING) ELSE f36 END,
                CASE WHEN f37 = '' THEN CAST(NULL AS STRING) ELSE f37 END
            ) as error,
            f38 as data_origin,
            'flink-streaming-job' as _run_id,
            'ecommerce-api-access-log' as _source_system,
            'kafka://ecommerce.access_logs' as _source_file,
            CAST(f2 AS TIMESTAMP_LTZ(6)) as _ingested_at
        FROM raw_events_view
    """)

    # 6.3 Silver Layer (Flattened, Sanitized, Enriched)
    statement_set.add_insert_sql("""
        INSERT INTO lakehouse.silver.silver_logs
        SELECT
            f0  as event_id,
            CAST(f1 AS TIMESTAMP_LTZ(6)) as event_ts,
            CAST(f4 AS TIMESTAMP_LTZ(6)) as observed_timestamp,
            f5  as schema_name,
            f6  as schema_version,
            f7  as service_name,
            f8  as service_version,
            f9  as service_environment,
            f10 as service_instance_id,
            f11 as severity_number,
            f12 as severity_text,
            CASE WHEN f13 = '' THEN CAST(NULL AS STRING) ELSE f13 END as trace_id,
            CASE WHEN f14 = '' THEN CAST(NULL AS STRING) ELSE f14 END as span_id,
            f15 as event_name,
            f16 as event_category,
            f17 as event_kind,
            f18 as event_outcome,
            f19 as event_duration_ns,
            f21 as http_request_method,
            f22 as http_route,
            f23 as http_status_code,
            f0  as request_id,
            f28 as actor_type,
            CASE WHEN f29 = '' THEN CAST(NULL AS STRING) ELSE f29 END as actor_key,
            f30 as client_user_agent,
            f31 as ecommerce_action,
            CASE WHEN f32 = '' THEN CAST(NULL AS STRING) ELSE f32 END as ecommerce_product_key,
            CASE WHEN f33 = '' THEN CAST(NULL AS STRING) ELSE f33 END as ecommerce_variant_key,
            CASE WHEN f34 = '' THEN CAST(NULL AS STRING) ELSE f34 END as ecommerce_search_query,
            f35 as ecommerce_search_redacted,
            CAST(NULL AS MAP<STRING, STRING>) as ecommerce_filters,
            CASE WHEN f36 = '' THEN CAST(NULL AS STRING) ELSE f36 END as error_code,
            CASE WHEN f37 = '' THEN CAST(NULL AS STRING) ELSE f37 END as error_type,
            f38 as data_origin,
            CAST(f2 AS TIMESTAMP_LTZ(6)) as _silver_ingested_at,
            'flink-streaming-job' as _source_bronze_run_id
        FROM raw_events_view
    """)

    # 6.4 Gold Layer (Real-time Facts)
    statement_set.add_insert_sql("""
        INSERT INTO lakehouse.gold.fact_web_events
        SELECT
            f0  as event_id,
            CAST(f1 AS TIMESTAMP_LTZ(6)) as event_ts,
            CAST(f3 AS DATE) as event_date,
            CASE WHEN f29 = '' THEN CAST(NULL AS STRING) ELSE f29 END as actor_key,
            f28 as actor_type,
            f21 as http_request_method,
            f22 as http_route,
            f23 as http_status_code,
            f31 as ecommerce_action,
            CASE WHEN f32 = '' THEN CAST(NULL AS STRING) ELSE f32 END as product_key,
            CASE WHEN f33 = '' THEN CAST(NULL AS STRING) ELSE f33 END as variant_key,
            f20 as duration_ms,
            f24 as is_success,
            f25 as is_client_error,
            f26 as is_server_error,
            f27 as is_slow_request,
            CAST(f2 AS TIMESTAMP_LTZ(6)) as _gold_ingested_at,
            'flink-streaming-job' as _source_run_id
        FROM raw_events_view
    """)

    log.info(
        "Submitting Pure Streaming Job: Kafka[%s] → Medallion Lakehouse (Landing, Bronze, Silver, Gold)",
        KAFKA_TOPIC,
    )
    statement_set.execute().wait()


if __name__ == "__main__":
    main()
