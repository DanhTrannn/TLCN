from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from lakehouse.sql import identifier, literal, render_sql

log = logging.getLogger(__name__)

if TYPE_CHECKING:
    from pyflink.table import StreamTableEnvironment

import os
import time
from pathlib import Path

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
    if not client_id or not client_secret:
        raise RuntimeError("Polaris Flink credentials are missing")
    return client_id, client_secret


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
    s3_access_key = os.environ["MINIO_FLINK_ACCESS_KEY"]
    s3_secret_key = os.environ["MINIO_FLINK_SECRET_KEY"]

    t_env.execute_sql(
        render_sql(
            "flink/operations/create_polaris_catalog.sql",
            catalog_name=identifier(catalog_name),
            polaris_uri=literal(polaris_uri),
            credential=literal(f"{client_id}:{client_secret}"),
            warehouse=literal(warehouse),
            realm=literal(realm),
            minio_endpoint=literal(minio_endpoint),
            s3_access_key=literal(s3_access_key),
            s3_secret_key=literal(s3_secret_key),
        )
    )
    log.info("Registered Iceberg REST catalog '%s' via Polaris at %s", catalog_name, polaris_uri)


def ensure_medallion_namespaces(
    t_env: StreamTableEnvironment,
    catalog_name: str = "lakehouse",
) -> None:
    """Ensure Landing, Bronze, Silver, and Gold databases exist in the catalog."""
    for ns in ["landing", "bronze", "silver", "gold"]:
        t_env.execute_sql(
            render_sql("flink/operations/create_database.sql", catalog_name=identifier(catalog_name), ns=identifier(ns))
        )
