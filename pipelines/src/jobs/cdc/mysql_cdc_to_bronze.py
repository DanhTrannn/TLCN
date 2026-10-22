"""Capture Debezium MySQL change events from Kafka into Iceberg Bronze.

The sink is an immutable audit log: inserts, updates, deletes, initial snapshot
records and Debezium tombstones are retained with Kafka and binlog coordinates.
The existing Spark batch path remains the authoritative backfill/reconciliation
path; downstream consumers can deterministically order and replay this table.
"""

import logging
import os

from lakehouse.flink import (
    create_stream_environment,
    create_table_environment,
    ensure_cdc_tables,
    ensure_medallion_namespaces,
    register_polaris_catalog,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
log = logging.getLogger("flink.mysql_cdc_to_bronze")

CHECKPOINT_INTERVAL_MS = 10_000


def _sql_literal(value: str) -> str:
    """Escape a value embedded in a Flink SQL single-quoted literal."""
    return value.replace("'", "''")


def kafka_source_ddl(
    bootstrap_servers: str,
    topic_pattern: str,
    group_id: str,
) -> str:
    """Build the raw Kafka source DDL without coupling to OLTP table schemas."""
    return f"""
        CREATE TEMPORARY TABLE mysql_cdc_kafka (
            record_key STRING,
            payload STRING,
            topic STRING METADATA FROM 'topic' VIRTUAL,
            kafka_partition INT METADATA FROM 'partition' VIRTUAL,
            kafka_offset BIGINT METADATA FROM 'offset' VIRTUAL,
            kafka_timestamp TIMESTAMP_LTZ(3) METADATA FROM 'timestamp' VIRTUAL
        ) WITH (
            'connector' = 'kafka',
            'topic-pattern' = '{_sql_literal(topic_pattern)}',
            'properties.bootstrap.servers' = '{_sql_literal(bootstrap_servers)}',
            'properties.group.id' = '{_sql_literal(group_id)}',
            'properties.auto.offset.reset' = 'earliest',
            'scan.startup.mode' = 'group-offsets',
            'key.format' = 'raw',
            'key.fields' = 'record_key',
            'value.format' = 'raw',
            'value.fields-include' = 'EXCEPT_KEY',
            'value.raw.charset' = 'UTF-8'
        )
    """


CDC_INSERT_SQL = """
    INSERT INTO lakehouse.bronze.oltp_cdc_events
    SELECT
        CONCAT(topic, ':', CAST(kafka_partition AS STRING), ':', CAST(kafka_offset AS STRING)),
        topic,
        JSON_VALUE(payload, '$.source.db'),
        COALESCE(
            JSON_VALUE(payload, '$.source.table'),
            REGEXP_EXTRACT(topic, '[^.]+$', 0)
        ),
        CASE
            WHEN payload IS NULL THEN 't'
            ELSE JSON_VALUE(payload, '$.op')
        END,
        COALESCE(
            TO_TIMESTAMP_LTZ(CAST(JSON_VALUE(payload, '$.ts_ms') AS BIGINT), 3),
            kafka_timestamp
        ),
        TO_TIMESTAMP_LTZ(CAST(JSON_VALUE(payload, '$.source.ts_ms') AS BIGINT), 3),
        JSON_VALUE(payload, '$.transaction.id'),
        JSON_VALUE(payload, '$.source.server_id'),
        JSON_VALUE(payload, '$.source.file'),
        CAST(JSON_VALUE(payload, '$.source.pos') AS BIGINT),
        CAST(JSON_VALUE(payload, '$.source.row') AS INT),
        kafka_partition,
        kafka_offset,
        record_key,
        JSON_QUERY(payload, '$.before'),
        JSON_QUERY(payload, '$.after'),
        payload,
        CURRENT_TIMESTAMP,
        CAST(
            COALESCE(
                TO_TIMESTAMP_LTZ(CAST(JSON_VALUE(payload, '$.ts_ms') AS BIGINT), 3),
                kafka_timestamp,
                CURRENT_TIMESTAMP
            ) AS DATE
        )
    FROM mysql_cdc_kafka
"""


def main() -> None:
    bootstrap_servers = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    topic_prefix = os.environ.get("CDC_TOPIC_PREFIX", "ecommerce")
    database_name = os.environ.get("MYSQL_DATABASE", "ecommerce")
    topic_pattern = rf"{topic_prefix}\.{database_name}\..*"
    group_id = os.environ.get("CDC_FLINK_GROUP_ID", "flink-oltp-cdc-bronze-v1")

    env = create_stream_environment(checkpoint_interval_ms=CHECKPOINT_INTERVAL_MS)
    table_env = create_table_environment(env, pipeline_name="oltp_cdc_to_bronze")

    register_polaris_catalog(table_env, catalog_name="lakehouse")
    ensure_medallion_namespaces(table_env, catalog_name="lakehouse")
    ensure_cdc_tables(table_env)
    table_env.execute_sql(kafka_source_ddl(bootstrap_servers, topic_pattern, group_id))

    log.info(
        "Starting CDC stream Kafka[%s] -> lakehouse.bronze.oltp_cdc_events",
        topic_pattern,
    )
    table_env.execute_sql(CDC_INSERT_SQL).wait()


if __name__ == "__main__":
    main()
