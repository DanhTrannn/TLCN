"""PyFlink helper factory for Apache Iceberg Lakehouse with Apache Polaris REST Catalog.

Mirrors the design of ``pipelines.src.lakehouse.spark`` to provide unified environment,
checkpointing, Polaris OAuth2 catalog registration, and S3 FileIO configuration.
"""

import logging
import os
import time
from pathlib import Path

from pyflink.common import Configuration
from pyflink.datastream import CheckpointingMode, StreamExecutionEnvironment
from pyflink.table import EnvironmentSettings, StreamTableEnvironment

log = logging.getLogger("lakehouse.flink")

DEFAULT_REALM = "POLARIS"


def polaris_flink_credentials() -> tuple[str, str]:
    """Retrieve Polaris OAuth2 client id and secret for Flink."""
    # First check environment variables
    client_id = os.environ.get("POLARIS_FLINK_CLIENT_ID")
    client_secret = os.environ.get("POLARIS_FLINK_CLIENT_SECRET")
    if client_id and client_secret:
        return client_id, client_secret

    # Otherwise read from client credentials volume
    cred_file = Path(os.environ.get("POLARIS_CREDENTIAL_FILE", "/run/polaris/clients.env"))
    for _ in range(120):
        if cred_file.is_file() and cred_file.stat().st_size > 0:
            break
        time.sleep(1)

    env = {}
    if cred_file.is_file():
        for line in cred_file.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, _, v = line.partition("=")
                v = v.strip()
                if len(v) >= 2 and v[0] == v[-1] and v[0] in ("'", '"'):
                    v = v[1:-1]
                env[k.strip()] = v

    client_id = env.get("POLARIS_FLINK_CLIENT_ID", "")
    client_secret = env.get("POLARIS_FLINK_CLIENT_SECRET", "")
    return client_id, client_secret


def create_stream_environment(
    checkpoint_interval_ms: int = 10_000,
    checkpoint_dir: str = "file:///opt/flink/checkpoints",
) -> StreamExecutionEnvironment:
    """Create and configure StreamExecutionEnvironment with exactly-once checkpointing."""
    config = Configuration()
    env = StreamExecutionEnvironment.get_execution_environment(config)
    env.enable_checkpointing(checkpoint_interval_ms, CheckpointingMode.EXACTLY_ONCE)
    env.get_checkpoint_config().set_checkpoint_storage_dir(checkpoint_dir)
    env.get_checkpoint_config().set_min_pause_between_checkpoints(5_000)
    env.get_checkpoint_config().set_checkpoint_timeout(60_000)
    return env


def create_table_environment(
    env: StreamExecutionEnvironment,
    pipeline_name: str = "kafka_to_lakehouse_pure_streaming",
) -> StreamTableEnvironment:
    """Create StreamTableEnvironment with streaming settings and pipeline name."""
    t_env = StreamTableEnvironment.create(
        env,
        EnvironmentSettings.new_instance().in_streaming_mode().build(),
    )
    t_env.get_config().set("pipeline.name", pipeline_name)
    return t_env


def register_polaris_catalog(
    t_env: StreamTableEnvironment,
    catalog_name: str = "lakehouse",
    warehouse: str = "lakehouse",
) -> None:
    """Register Polaris Iceberg REST Catalog in Flink Table Environment."""
    client_id, client_secret = polaris_flink_credentials()
    realm = os.environ.get("POLARIS_REALM", DEFAULT_REALM)
    polaris_uri = os.environ.get("POLARIS_CATALOG_URI", "http://polaris:8181/api/catalog")
    minio_endpoint = os.environ.get("MINIO_ENDPOINT", "http://minio:9000")
    s3_access_key = os.environ.get("AWS_ACCESS_KEY_ID", os.environ.get("MINIO_ACCESS_KEY", "minioadmin"))
    s3_secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY", os.environ.get("MINIO_SECRET_KEY", "password"))

    t_env.execute_sql(f"""
        CREATE CATALOG {catalog_name} WITH (
            'type'                   = 'iceberg',
            'catalog-type'           = 'rest',
            'uri'                    = '{polaris_uri}',
            'credential'             = '{client_id}:{client_secret}',
            'warehouse'              = '{warehouse}',
            'scope'                  = 'PRINCIPAL_ROLE:ALL',
            'header.Polaris-Realm'   = '{realm}',
            'io-impl'                = 'org.apache.iceberg.aws.s3.S3FileIO',
            's3.endpoint'            = '{minio_endpoint}',
            's3.path-style-access'   = 'true',
            's3.access-key-id'       = '{s3_access_key}',
            's3.secret-access-key'   = '{s3_secret_key}'
        )
    """)
    log.info("Registered Iceberg REST catalog '%s' via Polaris at %s", catalog_name, polaris_uri)


def ensure_medallion_namespaces(
    t_env: StreamTableEnvironment,
    catalog_name: str = "lakehouse",
) -> None:
    """Ensure Landing, Bronze, Silver, and Gold databases exist in the catalog."""
    for ns in ["landing", "bronze", "silver", "gold"]:
        t_env.execute_sql(f"CREATE DATABASE IF NOT EXISTS {catalog_name}.{ns}")


def ensure_merge_on_read(
    t_env: StreamTableEnvironment,
    tables: list[str],
) -> None:
    """Configure Merge-on-Read write mode on target Iceberg tables."""
    for tbl in tables:
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
