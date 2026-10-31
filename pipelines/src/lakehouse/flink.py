"""Compatibility exports for existing Flink job entrypoints."""

from .streaming.runtime import create_stream_environment, create_table_environment
from .streaming.catalog import polaris_flink_credentials, register_polaris_catalog, ensure_medallion_namespaces
from .streaming.tables import ensure_streaming_tables, ensure_cdc_tables, ensure_merge_on_read, ensure_upsert_mode

__all__ = [
    "create_stream_environment",
    "create_table_environment",
    "polaris_flink_credentials",
    "register_polaris_catalog",
    "ensure_medallion_namespaces",
    "ensure_streaming_tables",
    "ensure_cdc_tables",
    "ensure_merge_on_read",
    "ensure_upsert_mode",
]
