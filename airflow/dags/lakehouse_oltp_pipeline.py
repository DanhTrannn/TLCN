"""Lakehouse OLTP Batch Data Pipeline DAG.

Unified end-to-end Medallion pipeline for OLTP transactions:
  1. landing_zone: Extract incremental MySQL tables with composite cursors (cursor_field, pk)
                   to MinIO landing zone and validate cryptographic manifests.
  2. bronze_layer: Ingest landing Parquet files into Iceberg Bronze tables (Append-only).
  3. silver_layer: Deduplicate, hash PII (SHA-256), and MERGE/Upsert into Iceberg Silver tables.
  4. gold_layer:   Build Star Schema Dimensions, Facts, and Data Marts with COGS & financial metrics.
"""

from __future__ import annotations


import os
from datetime import timedelta

import pendulum
from airflow.operators.python import PythonOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.utils.task_group import TaskGroup
from lakehouse.orchestration.batch import (
    begin_run,
    check_mysql,
    capture_high_watermarks,
    validate_landing_manifests,
    commit_cursors,
)

from airflow import DAG

VN_TZ = pendulum.timezone("Asia/Ho_Chi_Minh")
CONFIG_PATH = os.environ.get("PIPELINE_CONFIG_PATH", "/opt/project/pipelines/config/default.yml")

SPARK_APP_EXTRACT = "/opt/project/pipelines/src/jobs/oltp/extract_oltp.py"
SPARK_APP_BRONZE = "/opt/project/pipelines/src/jobs/oltp/ingest_oltp_to_bronze.py"
SPARK_APP_SILVER = "/opt/project/pipelines/src/jobs/oltp/ingest_oltp_silver.py"
SPARK_APP_RECONCILE = "/opt/project/pipelines/src/jobs/oltp/run_reconciliation_gate.py"
SPARK_APP_GOLD = "/opt/project/pipelines/src/jobs/oltp/build_oltp_gold.py"
SPARK_APP_GOLD_QUALITY = "/opt/project/pipelines/src/jobs/oltp/run_gold_quality_gate.py"

DEFAULT_ARGS = {
    "owner": "lakehouse",
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
}


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
    check_context = PythonOperator(
        task_id="check_pipeline_context",
        python_callable=begin_run,
    )

    # 1. LANDING ZONE EXTRACTION & MANIFEST VALIDATION
    with TaskGroup(
        group_id="landing_zone",
        tooltip="Extract MySQL tables to MinIO landing with composite cursors and MD5 manifests",
    ) as tg_landing:
        check = PythonOperator(
            task_id="check_mysql_connection",
            python_callable=check_mysql,
        )

        capture = PythonOperator(
            task_id="extract_high_watermarks",
            python_callable=capture_high_watermarks,
        )

        extract = SparkSubmitOperator(
            task_id="extract_mysql_tables",
            application=SPARK_APP_EXTRACT,
            application_args=[
                "--config-path",
                CONFIG_PATH,
                "--run-id",
                "{{ ti.xcom_pull(task_ids='check_pipeline_context', key='run_id') }}",
                "--extract-date",
                "{{ ti.xcom_pull(task_ids='check_pipeline_context', key='batch_date') }}",
                "--high-watermarks",
                "{{ ti.xcom_pull(task_ids='landing_zone.extract_high_watermarks') | tojson }}",
            ],
        )

        validate = PythonOperator(
            task_id="validate_landing_manifests",
            python_callable=validate_landing_manifests,
        )

        check >> capture >> extract >> validate

    # 2. BRONZE LAYER INGESTION (APPEND-ONLY)
    with TaskGroup(
        group_id="bronze_layer",
        tooltip="Ingest Landing Parquet files into Iceberg Bronze tables",
    ) as tg_bronze:
        load_bronze = SparkSubmitOperator(
            task_id="load_to_bronze",
            application=SPARK_APP_BRONZE,
            application_args=[
                "--run-id",
                "{{ ti.xcom_pull(task_ids='check_pipeline_context', key='run_id') }}",
                "--extract-date",
                "{{ ti.xcom_pull(task_ids='check_pipeline_context', key='batch_date') }}",
            ],
        )

    # 3. HIGH WATERMARK COMMIT (Only advance cursors AFTER Bronze successfully ingests Landing data)
    load_cursors = PythonOperator(
        task_id="load_committed_cursors",
        python_callable=commit_cursors,
    )

    # 4. SILVER LAYER MERGE & PII PSEUDONYMIZATION
    with TaskGroup(
        group_id="silver_layer",
        tooltip="Deduplicate, hash PII, and MERGE/Upsert Bronze tables into Iceberg Silver tables",
    ) as tg_silver:
        transform_silver = SparkSubmitOperator(
            task_id="transform_bronze_to_silver",
            application=SPARK_APP_SILVER,
            application_args=[
                "--config-path",
                CONFIG_PATH,
                "--run-id",
                "{{ ti.xcom_pull(task_ids='check_pipeline_context', key='run_id') }}",
                "--bronze-date",
                "{{ ti.xcom_pull(task_ids='check_pipeline_context', key='batch_date') }}",
            ],
        )

    # 5. RECONCILIATION GATE (Pre-Gold Publishing Quality Gate)
    # Audits row count and financial metric parity between Source MySQL and Silver Iceberg.
    # Halts execution and blocks Gold publishing if variance exceeds 0.05%.
    validate_reconciliation = SparkSubmitOperator(
        task_id="validate_data_reconciliation",
        application=SPARK_APP_RECONCILE,
        application_args=[
            "--config-path",
            CONFIG_PATH,
            "--run-id",
            "{{ ti.xcom_pull(task_ids='check_pipeline_context', key='run_id') }}",
            "--batch-date",
            "{{ ti.xcom_pull(task_ids='check_pipeline_context', key='batch_date') }}",
            "--tolerance-pct",
            "0.05",
        ],
    )

    # 6. GOLD LAYER STAR SCHEMA & DATA MARTS
    with TaskGroup(
        group_id="gold_layer",
        tooltip="Build Star Schema Dimensions, Facts, and Data Marts with financial COGS and KPI rollups",
    ) as tg_gold:
        build_dimensions = SparkSubmitOperator(
            task_id="build_gold_dimensions",
            application=SPARK_APP_GOLD,
            application_args=[
                "--run-id",
                "{{ ti.xcom_pull(task_ids='check_pipeline_context', key='run_id') }}",
                "--snapshot-date",
                "{{ ti.xcom_pull(task_ids='check_pipeline_context', key='batch_date') }}",
                "--stage",
                "dimensions",
            ],
        )

        build_facts = SparkSubmitOperator(
            task_id="build_gold_facts",
            application=SPARK_APP_GOLD,
            application_args=[
                "--run-id",
                "{{ ti.xcom_pull(task_ids='check_pipeline_context', key='run_id') }}",
                "--snapshot-date",
                "{{ ti.xcom_pull(task_ids='check_pipeline_context', key='batch_date') }}",
                "--stage",
                "facts",
            ],
        )

        aggregate_marts = SparkSubmitOperator(
            task_id="aggregate_gold_marts",
            application=SPARK_APP_GOLD,
            application_args=[
                "--run-id",
                "{{ ti.xcom_pull(task_ids='check_pipeline_context', key='run_id') }}",
                "--snapshot-date",
                "{{ ti.xcom_pull(task_ids='check_pipeline_context', key='batch_date') }}",
                "--stage",
                "marts",
            ],
        )

        [build_dimensions, build_facts] >> aggregate_marts

    # 7. POST-GOLD QUALITY GATE
    # Persists auditable results and verifies completeness, monetary parity,
    # primary keys, references, freshness markers, and PII pseudonymization.
    validate_gold_quality = SparkSubmitOperator(
        task_id="validate_gold_data_quality",
        application=SPARK_APP_GOLD_QUALITY,
        application_args=[
            "--run-id",
            "{{ ti.xcom_pull(task_ids='check_pipeline_context', key='run_id') }}",
            "--batch-date",
            "{{ ti.xcom_pull(task_ids='check_pipeline_context', key='batch_date') }}",
        ],
    )

    # Sequential End-to-End Orchestration:
    # 1. Check Context -> 2. Landing Zone -> 3. Bronze Layer -> 4. Load Cursors ->
    # 5. Silver Layer -> 6. Reconciliation Gate -> 7. Gold Layer (Dimensions, Facts, Marts)
    # (Iceberg Table Maintenance is decoupled into dedicated off-peak DAG: lakehouse_oltp_maintenance)
    (
        check_context
        >> tg_landing
        >> tg_bronze
        >> load_cursors
        >> tg_silver
        >> validate_reconciliation
        >> tg_gold
        >> validate_gold_quality
    )
