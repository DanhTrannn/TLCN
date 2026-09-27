"""Lakehouse OLTP Batch Data Pipeline DAG.

Unified end-to-end Medallion pipeline for OLTP transactions:
  1. landing_zone: Extract incremental MySQL tables with composite cursors (cursor_field, pk)
                   to MinIO landing zone and validate cryptographic manifests.
  2. bronze_layer: Ingest landing Parquet files into Iceberg Bronze tables (Append-only).
  3. silver_layer: Deduplicate, hash PII (SHA-256), and MERGE/Upsert into Iceberg Silver tables.
  4. gold_layer:   Build Star Schema Dimensions, Facts, and Data Marts with COGS & financial metrics.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import timedelta

import pendulum
import pymysql
from airflow import DAG
from airflow.exceptions import AirflowException
from airflow.operators.python import PythonOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.utils.task_group import TaskGroup
from sqlalchemy.engine.url import make_url

from lakehouse.config import load_config
from lakehouse.oltp.cursor import build_cursor_advancements, write_committed_cursor
from lakehouse.validate import s3_client, validate_run

VN_TZ = pendulum.timezone("Asia/Ho_Chi_Minh")
CONFIG_PATH = os.environ.get("PIPELINE_CONFIG_PATH", "/opt/project/pipelines/config/default.yml")

SPARK_APP_EXTRACT = "/opt/project/pipelines/src/jobs/oltp/extract_oltp.py"
SPARK_APP_BRONZE = "/opt/project/pipelines/src/jobs/oltp/ingest_oltp_to_bronze.py"
SPARK_APP_SILVER = "/opt/project/pipelines/src/jobs/oltp/ingest_oltp_silver.py"
SPARK_APP_GOLD = "/opt/project/pipelines/src/jobs/oltp/build_oltp_gold.py"

DEFAULT_ARGS = {
    "owner": "lakehouse",
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
}


def _mysql_conn():
    reader_url = os.environ.get(
        "MYSQL_ECOMMERCE_READER_URL",
        "mysql+pymysql://ecommerce_app:password@mysql:3306/ecommerce",
    )
    url = make_url(reader_url)
    return pymysql.connect(
        host=url.host,
        port=url.port or 3306,
        user=url.username,
        password=url.password,
        database=url.database,
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
    run_id = uuid.uuid4().hex
    batch_date = pendulum.now(VN_TZ).strftime("%Y-%m-%d")
    context["ti"].xcom_push(key="run_id", value=run_id)
    context["ti"].xcom_push(key="batch_date", value=batch_date)
    context["ti"].xcom_push(key="extract_date", value=batch_date)
    context["ti"].xcom_push(key="bronze_date", value=batch_date)
    context["ti"].xcom_push(key="snapshot_date", value=batch_date)
    print(f"[begin_run] Initialized OLTP pipeline run {run_id} for date {batch_date} (Asia/Ho_Chi_Minh)")


def capture_high_watermarks() -> dict:
    cfg = load_config(CONFIG_PATH)
    conn = _mysql_conn()
    result = {}
    try:
        with conn.cursor() as cur:
            for table in cfg.tables:
                cur.execute(
                    f"SELECT MAX(`{table.cursor_field}`) AS at, "
                    f"MAX(`{table.pk}`) AS pk_at_max "
                    f"FROM `{table.name}` "
                    f"WHERE `{table.cursor_field}` = "
                    f"(SELECT MAX(`{table.cursor_field}`) FROM `{table.name}`)"
                )
                row = cur.fetchone()
                result[table.name] = {
                    "at": str(row[0]) if row[0] is not None else None,
                    "pk": row[1],
                }
    finally:
        conn.close()
    return result


def validate_landing_manifests(**context) -> None:
    cfg = load_config(CONFIG_PATH)
    run_id = context["ti"].xcom_pull(task_ids="begin_run", key="run_id")
    extract_date = context["ti"].xcom_pull(task_ids="begin_run", key="batch_date")
    s3 = s3_client(
        os.environ.get("MINIO_ENDPOINT", "http://minio:9000"),
        os.environ.get("MINIO_ACCESS_KEY", "minioadmin"),
        os.environ.get("MINIO_SECRET_KEY", "password"),
    )
    violations = validate_run(
        s3, cfg.bucket, [t.name for t in cfg.tables], extract_date, run_id
    )
    bad = {table: v for table, v in violations.items() if v}
    if bad:
        raise AirflowException(f"Manifest validation failed with violations: {json.dumps(bad)}")
    print(f"[validate_landing_manifests] All {len(cfg.tables)} tables passed manifest validation.")


def commit_cursors(**context) -> None:
    cfg = load_config(CONFIG_PATH)
    watermarks = context["ti"].xcom_pull(task_ids="landing_zone.capture_high_watermarks")
    s3 = s3_client(
        os.environ.get("MINIO_ENDPOINT", "http://minio:9000"),
        os.environ.get("MINIO_ACCESS_KEY", "minioadmin"),
        os.environ.get("MINIO_SECRET_KEY", "password"),
    )
    now_utc = pendulum.now("UTC").strftime("%Y-%m-%dT%H:%M:%SZ")
    states = build_cursor_advancements(
        watermarks, [t.name for t in cfg.tables], now_utc
    )
    for table, state in states.items():
        write_committed_cursor(s3, cfg.bucket, table, state)
    print(f"[commit_cursors] Successfully advanced cursors for {len(states)} tables.")


with DAG(
    dag_id="lakehouse_oltp_pipeline",
    default_args=DEFAULT_ARGS,
    schedule="0 2 * * *",  # Daily at 02:00 AM VN Time (Asia/Ho_Chi_Minh)
    catchup=False,
    max_active_runs=1,
    start_date=pendulum.datetime(2026, 8, 15, tz=VN_TZ),
    description="End-to-end OLTP Batch Data Lakehouse Pipeline (MySQL -> Landing -> Bronze -> Silver -> Gold)",
    tags=["lakehouse", "oltp", "batch", "medallion", "gold"],
) as dag:

    begin = PythonOperator(
        task_id="begin_run",
        python_callable=begin_run,
    )

    # 1. LANDING ZONE EXTRACTION & MANIFEST VALIDATION
    with TaskGroup(
        group_id="landing_zone",
        tooltip="Extract MySQL tables to MinIO landing with composite cursors and MD5 manifests",
    ) as tg_landing:
        check = PythonOperator(
            task_id="check_mysql",
            python_callable=check_mysql,
        )

        capture = PythonOperator(
            task_id="capture_high_watermarks",
            python_callable=capture_high_watermarks,
        )

        extract = SparkSubmitOperator(
            task_id="extract_tables_to_landing",
            application=SPARK_APP_EXTRACT,
            application_args=[
                "--config-path", CONFIG_PATH,
                "--run-id", "{{ ti.xcom_pull(task_ids='begin_run', key='run_id') }}",
                "--extract-date", "{{ ti.xcom_pull(task_ids='begin_run', key='batch_date') }}",
                "--high-watermarks",
                "{{ ti.xcom_pull(task_ids='landing_zone.capture_high_watermarks') | tojson }}",
            ],
        )

        validate = PythonOperator(
            task_id="validate_landing_manifests",
            python_callable=validate_landing_manifests,
        )

        commit = PythonOperator(
            task_id="commit_cursors",
            python_callable=commit_cursors,
        )

        check >> capture >> extract >> validate >> commit

    # 2. BRONZE LAYER INGESTION (APPEND-ONLY)
    with TaskGroup(
        group_id="bronze_layer",
        tooltip="Ingest Landing Parquet files into Iceberg Bronze tables",
    ) as tg_bronze:
        ingest_bronze = SparkSubmitOperator(
            task_id="ingest_oltp_to_bronze",
            application=SPARK_APP_BRONZE,
            application_args=[
                "--run-id", "{{ ti.xcom_pull(task_ids='begin_run', key='run_id') }}",
                "--extract-date", "{{ ti.xcom_pull(task_ids='begin_run', key='batch_date') }}",
            ],
        )

    # 3. SILVER LAYER MERGE & PII PSEUDONYMIZATION
    with TaskGroup(
        group_id="silver_layer",
        tooltip="Deduplicate, hash PII, and MERGE/Upsert Bronze tables into Iceberg Silver tables",
    ) as tg_silver:
        merge_silver = SparkSubmitOperator(
            task_id="spark_oltp_bronze_to_silver",
            application=SPARK_APP_SILVER,
            application_args=[
                "--config-path", CONFIG_PATH,
                "--run-id", "{{ ti.xcom_pull(task_ids='begin_run', key='run_id') }}",
                "--bronze-date", "{{ ti.xcom_pull(task_ids='begin_run', key='batch_date') }}",
            ],
        )

    # 4. GOLD LAYER STAR SCHEMA & DATA MARTS
    with TaskGroup(
        group_id="gold_layer",
        tooltip="Build Star Schema Dimensions, Facts, and Data Marts with financial COGS and KPI rollups",
    ) as tg_gold:
        build_gold = SparkSubmitOperator(
            task_id="spark_build_oltp_gold",
            application=SPARK_APP_GOLD,
            application_args=[
                "--run-id", "{{ ti.xcom_pull(task_ids='begin_run', key='run_id') }}",
                "--snapshot-date", "{{ ti.xcom_pull(task_ids='begin_run', key='batch_date') }}",
            ],
        )

    # Sequential End-to-End Orchestration:
    # 1. Begin Run -> 2. Landing Zone -> 3. Bronze Layer -> 4. Silver Layer -> 5. Gold Layer
    begin >> tg_landing >> tg_bronze >> tg_silver >> tg_gold
