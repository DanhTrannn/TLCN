"""Flink adapter for named access events and external SQL sinks."""

import logging
import os
from dataclasses import astuple

from pyflink.common import Row
from pyflink.common.serialization import SimpleStringSchema
from pyflink.common.typeinfo import Types
from pyflink.common.watermark_strategy import WatermarkStrategy
from pyflink.datastream.connectors.kafka import KafkaOffsetsInitializer, KafkaSource
from pyflink.datastream.functions import MapFunction
from pyflink.table import Schema
from pyflink.table.types import DataTypes

from lakehouse.flink import (
    create_stream_environment,
    create_table_environment,
    ensure_medallion_namespaces,
    ensure_merge_on_read,
    ensure_streaming_tables,
    ensure_upsert_mode,
    register_polaris_catalog,
)
from lakehouse.logs.parser import InvalidAccessEvent, parse_access_event
from lakehouse.logs.stream_schema import FIELD_SPECS
from lakehouse.sql import load_sql

log = logging.getLogger(__name__)
CHECKPOINT_INTERVAL_MS = 10_000


class ParseAccessLog(MapFunction):
    def map(self, raw):
        try:
            return Row(*astuple(parse_access_event(raw)))
        except InvalidAccessEvent as exc:
            log.warning("Rejected malformed access event: %s", exc)
            return None


def run_access_stream():
    topic = os.environ.get("KAFKA_ACCESS_LOG_TOPIC", "ecommerce.access_logs")
    # 1. Environments
    env = create_stream_environment(checkpoint_interval_ms=CHECKPOINT_INTERVAL_MS)
    t_env = create_table_environment(env, pipeline_name="kafka_to_lakehouse_pure_streaming")

    # 2. Polaris Iceberg REST Catalog
    register_polaris_catalog(t_env, catalog_name="lakehouse")
    ensure_medallion_namespaces(t_env, catalog_name="lakehouse")
    ensure_streaming_tables(t_env)
    ensure_merge_on_read(
        t_env,
        [
            "lakehouse.landing.access_logs",
            "lakehouse.bronze.web_events",
        ],
    )
    ensure_upsert_mode(
        t_env,
        [
            "lakehouse.silver.silver_logs",
            "lakehouse.gold.fact_web_events",
        ],
    )

    # 3. Kafka Source

    kafka_source = (
        KafkaSource.builder()
        .set_bootstrap_servers(os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"))
        .set_topics(topic)
        .set_group_id(os.environ.get("KAFKA_ACCESS_LOG_GROUP_ID", "flink-lakehouse-pure-stream"))
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
    field_names = [name for name, _ in FIELD_SPECS]
    field_types = [getattr(Types, kind)() for _, kind in FIELD_SPECS]
    parsed_type = Types.ROW_NAMED(field_names, field_types)

    parsed_stream = raw_stream.map(ParseAccessLog(), output_type=parsed_type).filter(lambda row: row is not None)

    # 5. Convert DataStream to Table
    schema = Schema.new_builder()
    for name, kind in FIELD_SPECS:
        table_kind = {"LONG": "BIGINT"}.get(kind, kind)
        schema.column(name, getattr(DataTypes, table_kind)())
    parsed_schema = schema.build()

    tbl = t_env.from_data_stream(parsed_stream, parsed_schema)
    t_env.create_temporary_view("raw_events_view", tbl)

    # 6. StatementSet: Multi-sink parallel ingestion to Landing, Bronze, Silver, Gold
    statement_set = t_env.create_statement_set()

    # 6.1 Landing Layer
    statement_set.add_insert_sql(load_sql("flink/inserts/lakehouse_landing_access_logs.sql"))

    # 6.2 Bronze Layer (OpenTelemetry Schema with Structs)
    statement_set.add_insert_sql(load_sql("flink/inserts/lakehouse_bronze_web_events.sql"))

    # 6.3 Silver Layer (Flattened, Sanitized, Enriched)
    statement_set.add_insert_sql(load_sql("flink/inserts/lakehouse_silver_silver_logs.sql"))

    # 6.4 Gold Layer (Real-time Facts)
    statement_set.add_insert_sql(load_sql("flink/inserts/lakehouse_gold_fact_web_events.sql"))

    log.info("Submitting Pure Streaming Job: Kafka[%s] → Medallion Lakehouse", topic)
    statement_set.execute().wait()
