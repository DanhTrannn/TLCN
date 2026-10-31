"""Batch task operations: source checks, run identity, manifests and cursor publication."""

from datetime import datetime, timezone
import json
import os
import uuid
from urllib.parse import unquote, urlsplit

import pymysql

from lakehouse.config import config_path, load_config
from lakehouse.landing import RunPaths
from lakehouse.oltp.cursor import verified_cursor_advancements, write_committed_cursor
from lakehouse.sql import identifier, render_sql
from lakehouse.validate import s3_client, validate_run

CONFIG_PATH = str(config_path())


def _mysql_conn():
    """Establish connection to MySQL OLTP database.

    Default credentials ("ecommerce_app:password") are local development defaults.
    In production, override via MYSQL_ECOMMERCE_READER_URL or Airflow Connections vault.
    """
    reader_url = os.environ.get(
        "MYSQL_ECOMMERCE_READER_URL",
        "mysql+pymysql://ecommerce_app:password@mysql:3306/ecommerce",
    )
    url = urlsplit(reader_url)
    return pymysql.connect(
        host=url.hostname,
        port=url.port or 3306,
        user=unquote(url.username or ""),
        password=unquote(url.password or ""),
        database=url.path.lstrip("/"),
        connect_timeout=10,
    )


def check_mysql() -> str:
    conn = _mysql_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
    finally:
        conn.close()
    print("[check_mysql] MySQL connection successfully verified.")
    return "ok"


def begin_run(**context) -> None:
    import pendulum

    vn_tz = pendulum.timezone("Asia/Ho_Chi_Minh")
    run_id = uuid.uuid4().hex
    # Use Airflow execution interval for true idempotency and deterministic backfilling
    logical_dt = context.get("data_interval_start") or context.get("logical_date")
    if logical_dt:
        batch_date = logical_dt.in_timezone(vn_tz).strftime("%Y-%m-%d")
    else:
        batch_date = pendulum.now(vn_tz).strftime("%Y-%m-%d")

    context["ti"].xcom_push(key="run_id", value=run_id)
    context["ti"].xcom_push(key="batch_date", value=batch_date)
    context["ti"].xcom_push(key="extract_date", value=batch_date)
    context["ti"].xcom_push(key="bronze_date", value=batch_date)
    context["ti"].xcom_push(key="snapshot_date", value=batch_date)
    print(f"[begin_run] Initialized OLTP pipeline run {run_id} for interval {batch_date} (Asia/Ho_Chi_Minh)")


def capture_high_watermarks() -> dict:
    cfg = load_config(CONFIG_PATH)
    conn = _mysql_conn()
    result = {}
    try:
        with conn.cursor() as cur:
            for table in cfg.tables:
                cur.execute(
                    render_sql(
                        "mysql/high_watermark.sql",
                        table_cursor_field=identifier(table.cursor_field),
                        table_pk=identifier(table.pk),
                        table_name=identifier(table.name),
                        table_cursor_field_2=identifier(table.cursor_field),
                        table_cursor_field_3=identifier(table.cursor_field),
                        table_name_2=identifier(table.name),
                    )
                )
                row = cur.fetchone()
                result[table.name] = {
                    "at": str(row[0]) if row[0] is not None else None,
                    "pk": row[1],
                }
    finally:
        conn.close()
    return result


def _s3_conn():
    """Construct the Airflow S3/MinIO client with its dedicated reader/writer identity."""
    return s3_client(
        os.environ.get("MINIO_ENDPOINT", "http://minio:9000"),
        os.environ["MINIO_AIRFLOW_ACCESS_KEY"],
        os.environ["MINIO_AIRFLOW_SECRET_KEY"],
    )


def validate_landing_manifests(**context) -> None:
    cfg = load_config(CONFIG_PATH)
    run_id = context["ti"].xcom_pull(task_ids="check_pipeline_context", key="run_id")
    extract_date = context["ti"].xcom_pull(task_ids="check_pipeline_context", key="batch_date")
    s3 = _s3_conn()
    violations = validate_run(s3, cfg.bucket, [t.name for t in cfg.tables], extract_date, run_id)
    bad = {table: v for table, v in violations.items() if v}
    if bad:
        raise RuntimeError(f"Manifest validation failed with violations: {json.dumps(bad)}")
    print(f"[validate_landing_manifests] All {len(cfg.tables)} tables passed manifest validation.")


def commit_cursors(**context) -> None:
    cfg = load_config(CONFIG_PATH)
    watermarks = context["ti"].xcom_pull(task_ids="landing_zone.extract_high_watermarks")
    s3 = _s3_conn()
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    run_id = context["ti"].xcom_pull(task_ids="check_pipeline_context", key="run_id")
    batch_date = context["ti"].xcom_pull(task_ids="check_pipeline_context", key="batch_date")
    completions = {}
    for table in cfg.tables:
        paths = RunPaths(cfg.bucket, table.name, batch_date, run_id)
        body = s3.get_object(Bucket=cfg.bucket, Key=f"{paths.run_prefix()}/bronze_complete.json")["Body"].read()
        completions[table.name] = json.loads(body)
    states = verified_cursor_advancements(watermarks, completions, [t.name for t in cfg.tables], run_id, now_utc)
    for table, state in states.items():
        write_committed_cursor(s3, cfg.bucket, table, state)
    print(f"[load_committed_cursors] Successfully advanced cursors for {len(states)} tables.")
