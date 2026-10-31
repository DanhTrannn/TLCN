from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from lakehouse.sql import identifier, load_sql, render_sql

log = logging.getLogger(__name__)

if TYPE_CHECKING:
    from pyflink.table import StreamTableEnvironment

STREAMING_TABLE_DDLS = (
    load_sql("flink/tables/lakehouse_landing_access_logs.sql"),
    load_sql("flink/tables/lakehouse_bronze_web_events.sql"),
    load_sql("flink/tables/lakehouse_silver_silver_logs.sql"),
    load_sql("flink/tables/lakehouse_gold_fact_web_events.sql"),
)
CDC_TABLE_DDLS = (load_sql("flink/tables/lakehouse_bronze_oltp_cdc_events.sql"),)


def ensure_streaming_tables(t_env: StreamTableEnvironment) -> None:
    """Provision the Iceberg sinks required by the standalone streaming profile."""
    for ddl in STREAMING_TABLE_DDLS:
        t_env.execute_sql(ddl)
    log.info("Ensured %d streaming Iceberg sink tables", len(STREAMING_TABLE_DDLS))


def ensure_cdc_tables(t_env: StreamTableEnvironment) -> None:
    """Provision the append-only Iceberg audit log for MySQL CDC envelopes."""
    for ddl in CDC_TABLE_DDLS:
        t_env.execute_sql(ddl)
    log.info("Ensured %d CDC Iceberg sink tables", len(CDC_TABLE_DDLS))


def ensure_merge_on_read(
    t_env: StreamTableEnvironment,
    tables: list[str],
) -> None:
    """Configure Merge-on-Read write mode on target Iceberg tables."""
    for tbl in tables:
        t_env.execute_sql(render_sql("flink/operations/enable_merge_on_read.sql", tbl=identifier(tbl)))


def ensure_upsert_mode(
    t_env: StreamTableEnvironment,
    tables: list[str],
) -> None:
    """Configure upsert mode on target Iceberg v2 tables to ensure deduplication on primary key."""
    for tbl in tables:
        t_env.execute_sql(render_sql("flink/operations/enable_upsert.sql", tbl=identifier(tbl)))
