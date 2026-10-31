"""Capture Debezium MySQL change events from Kafka into Iceberg Bronze.

The sink is an immutable audit log: inserts, updates, deletes, initial snapshot
records and Debezium tombstones are retained with Kafka and binlog coordinates.
The existing Spark batch path remains the authoritative backfill/reconciliation
path; downstream consumers can deterministically order and replay this table.
"""

from lakehouse.sql import literal, load_sql, render_sql

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


def kafka_source_ddl(
    bootstrap_servers: str,
    topic_pattern: str,
    group_id: str,
) -> str:
    """Build the raw Kafka source DDL without coupling to OLTP table schemas."""
    return render_sql(
        "flink/cdc/kafka_source.sql",
        topic_pattern=literal(topic_pattern),
        bootstrap_servers=literal(bootstrap_servers),
        group_id=literal(group_id),
    )


CDC_INSERT_SQL = load_sql("flink/cdc/insert_events.sql")


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
