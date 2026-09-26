"""PyFlink streaming job: Kafka → Iceberg Landing.

Reads JSON access log events from the Kafka topic ``ecommerce.access_logs`` and
writes them to the Iceberg table ``lakehouse.landing.access_logs`` managed by
Apache Polaris via the Iceberg REST catalog.

Submission (from inside the Flink cluster):
    flink run --python /opt/project/flink/jobs/kafka_to_landing.py

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
from datetime import timezone
from datetime import datetime as _dt

from pyflink.common import Configuration
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
log = logging.getLogger("flink.kafka_to_landing")

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
KAFKA_GROUP_ID = "flink-landing-consumer"
LANDING_TABLE = "lakehouse.landing.access_logs"
CHECKPOINT_INTERVAL_MS = 10_000  # 10 seconds


# ---------------------------------------------------------------------------
# Event parsing
# ---------------------------------------------------------------------------
class ParseAccessLog(MapFunction):
    """Parse a raw JSON string from Kafka into a landing row tuple.

    Output tuple columns (match Iceberg landing schema exactly):
        event_id, event_ts, ingest_ts, service_name,
        http_method, http_route, http_status_code,
        duration_ns, actor_type, ecommerce_action, raw_payload
    """

    def map(self, raw: str):  # noqa: ANN001
        try:
            msg = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            log.warning("Unparseable message dropped: %.120s", raw)
            return None

        now_ts = _dt.now(timezone.utc)

        # Parse ISO-8601 event timestamp (e.g. "2026-09-26T10:14:21.524385Z")
        ts_str: str = msg.get("timestamp", "")
        try:
            event_ts = _dt.fromisoformat(ts_str.replace("Z", "+00:00"))
        except ValueError:
            event_ts = now_ts

        # Nested field extraction with safe defaults
        request = msg.get("request") or {}
        service = msg.get("service") or {}
        http = msg.get("http") or {}
        event = msg.get("event") or {}
        actor = msg.get("actor") or {}
        ecommerce = msg.get("ecommerce") or {}

        event_id: str = request.get("id") or str(uuid.uuid4())
        service_name: str = service.get("name") or "ecommerce-api"
        http_method: str = (http.get("request_method") or "UNKNOWN").upper()
        http_route: str = http.get("route") or "UNKNOWN"
        http_status: int = int(http.get("status_code") or 200)
        duration_ns: int = int(event.get("duration_ns") or 0)
        actor_type: str = actor.get("type") or "anonymous"
        action: str = ecommerce.get("action") or "unknown"

        return (
            event_id,                                   # STRING
            event_ts.strftime("%Y-%m-%d %H:%M:%S.%f"),  # TIMESTAMP string
            now_ts.strftime("%Y-%m-%d %H:%M:%S.%f"),    # TIMESTAMP string
            service_name,                               # STRING
            http_method,                                # STRING
            http_route,                                 # STRING
            http_status,                                # INT
            duration_ns,                                # BIGINT
            actor_type,                                 # STRING
            action,                                     # STRING
            raw,                                        # STRING (raw_payload)
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    # 1. DataStream environment
    config = Configuration()
    env = StreamExecutionEnvironment.get_execution_environment(config)

    # Checkpointing
    env.enable_checkpointing(CHECKPOINT_INTERVAL_MS, CheckpointingMode.EXACTLY_ONCE)
    env.get_checkpoint_config().set_checkpoint_storage_dir("file:///opt/flink/checkpoints")
    env.get_checkpoint_config().set_min_pause_between_checkpoints(5_000)
    env.get_checkpoint_config().set_checkpoint_timeout(60_000)

    # Table environment (needed for Iceberg catalog + sink)
    t_env = StreamTableEnvironment.create(env, EnvironmentSettings.new_instance().in_streaming_mode().build())

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
    log.info("Iceberg catalog 'lakehouse' registered via Polaris REST at %s", MINIO_ENDPOINT)

    # Ensure Landing database and Iceberg table exist
    t_env.execute_sql("CREATE DATABASE IF NOT EXISTS lakehouse.landing")
    t_env.execute_sql("""
        CREATE TABLE IF NOT EXISTS lakehouse.landing.access_logs (
            event_id            STRING,
            event_ts            TIMESTAMP(6),
            ingest_ts           TIMESTAMP(6),
            service_name        STRING,
            http_method         STRING,
            http_route          STRING,
            http_status_code    INT,
            duration_ns         BIGINT,
            actor_type          STRING,
            ecommerce_action    STRING,
            raw_payload         STRING
        )
        PARTITIONED BY (service_name)
        WITH (
            'format-version' = '2',
            'write.parquet.compression-codec' = 'zstd',
            'write.delete.mode' = 'merge-on-read',
            'write.update.mode' = 'merge-on-read',
            'write.merge.mode' = 'merge-on-read'
        )
    """)
    # Ensure existing table also has Merge-On-Read enabled for row-level writes
    t_env.execute_sql("""
        ALTER TABLE lakehouse.landing.access_logs SET (
            'write.delete.mode' = 'merge-on-read',
            'write.update.mode' = 'merge-on-read',
            'write.merge.mode' = 'merge-on-read'
        )
    """)
    log.info("Ensured lakehouse.landing database and access_logs table exist with Merge-On-Read write mode")

    # 3. Kafka source (DataStream API – pure Java/Python bridge, no SQL connector DDL)
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

    # 4. Parse JSON → typed tuples (filter out unparseable nulls)
    parsed_stream = (
        raw_stream
        .map(ParseAccessLog(), output_type=Types.TUPLE([
            Types.STRING(),   # event_id
            Types.STRING(),   # event_ts
            Types.STRING(),   # ingest_ts
            Types.STRING(),   # service_name
            Types.STRING(),   # http_method
            Types.STRING(),   # http_route
            Types.INT(),      # http_status_code
            Types.LONG(),     # duration_ns
            Types.STRING(),   # actor_type
            Types.STRING(),   # ecommerce_action
            Types.STRING(),   # raw_payload
        ]))
        .filter(lambda row: row is not None)
    )

    # 5. Convert DataStream → Table using explicit Schema object (PyFlink 1.19 API)
    landing_schema = (
        Schema.new_builder()
        .column("f0",  DataTypes.STRING())    # event_id
        .column("f1",  DataTypes.STRING())    # event_ts  (ISO string → cast in SQL)
        .column("f2",  DataTypes.STRING())    # ingest_ts
        .column("f3",  DataTypes.STRING())    # service_name
        .column("f4",  DataTypes.STRING())    # http_method
        .column("f5",  DataTypes.STRING())    # http_route
        .column("f6",  DataTypes.INT())       # http_status_code
        .column("f7",  DataTypes.BIGINT())    # duration_ns
        .column("f8",  DataTypes.STRING())    # actor_type
        .column("f9",  DataTypes.STRING())    # ecommerce_action
        .column("f10", DataTypes.STRING())    # raw_payload
        .build()
    )
    landing_tbl = t_env.from_data_stream(parsed_stream, landing_schema)
    t_env.create_temporary_view("landing_stream", landing_tbl)

    # Cast string timestamps to proper TIMESTAMP type before writing to Iceberg
    statement_set = t_env.create_statement_set()
    statement_set.add_insert_sql(f"""
        INSERT INTO lakehouse.landing.access_logs
        SELECT
            f0,
            TO_TIMESTAMP(f1,  'yyyy-MM-dd HH:mm:ss.SSSSSS'),
            TO_TIMESTAMP(f2,  'yyyy-MM-dd HH:mm:ss.SSSSSS'),
            f3,
            f4,
            f5,
            f6,
            f7,
            f8,
            f9,
            f10
        FROM landing_stream
    """)

    log.info(
        "Submitting PyFlink job: Kafka[%s] → Iceberg[%s]",
        KAFKA_TOPIC,
        LANDING_TABLE,
    )
    statement_set.execute().wait()


if __name__ == "__main__":
    main()
