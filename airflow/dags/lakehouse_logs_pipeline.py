import os
import uuid
from datetime import datetime, timedelta, timezone

from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.utils.task_group import TaskGroup

from lakehouse.validate import s3_client

SPARK_APP_BRONZE = "/opt/project/pipelines/src/jobs/ingest_logs_to_bronze.py"
SPARK_APP_SILVER = "/opt/project/pipelines/src/jobs/ingest_logs_silver.py"

DEFAULT_ARGS = {
    "owner": "lakehouse",
    "retries": 2,
    "retry_delay": timedelta(minutes=1),
}


def begin_run(**context) -> None:
    run_id = uuid.uuid4().hex
    ingest_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    context["ti"].xcom_push(key="run_id", value=run_id)
    context["ti"].xcom_push(key="ingest_date", value=ingest_date)


def check_minio_landing() -> str:
    s3 = s3_client(
        os.environ.get("MINIO_ENDPOINT", "http://minio:9000"),
        os.environ.get("MINIO_ACCESS_KEY", "minioadmin"),
        os.environ.get("MINIO_SECRET_KEY", "password"),
    )
    bucket = os.environ.get("MINIO_LAKEHOUSE_BUCKET", "lakehouse")
    s3.head_bucket(Bucket=bucket)
    return "ok"


def discover_landing_logs(**context) -> int:
    s3 = s3_client(
        os.environ.get("MINIO_ENDPOINT", "http://minio:9000"),
        os.environ.get("MINIO_ACCESS_KEY", "minioadmin"),
        os.environ.get("MINIO_SECRET_KEY", "password"),
    )
    bucket = os.environ.get("MINIO_LAKEHOUSE_BUCKET", "lakehouse")
    ingest_date = context["ti"].xcom_pull(task_ids="begin_run", key="ingest_date")
    prefix = f"landing/logs/ingest_date={ingest_date}/"
    
    paginator = s3.get_paginator("list_objects_v2")
    count = 0
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        count += len(page.get("Contents", []))
    
    context["ti"].xcom_push(key="discovered_files_count", value=count)
    return count


with DAG(
    dag_id="lakehouse_logs_pipeline",
    default_args=DEFAULT_ARGS,
    schedule="0 */2 * * *",  # Every 2 hours (micro-batch or continuous interval)
    catchup=False,
    start_date=datetime(2026, 8, 15, tzinfo=timezone.utc),
    description="End-to-End Medallion Lakehouse Logs Pipeline: Staging -> Bronze -> Silver -> Gold",
    tags=["lakehouse", "logs", "medallion", "production"],
) as dag:

    begin = PythonOperator(
        task_id="begin_run",
        python_callable=begin_run,
    )

    # 1. STAGING / LANDING LAYER
    with TaskGroup(
        group_id="staging_layer",
        tooltip="Verify MinIO S3 Landing Zone & Discover Rotated Access Log Batches",
    ) as tg_staging:
        check_storage = PythonOperator(
            task_id="check_minio_landing",
            python_callable=check_minio_landing,
        )

        discover_logs = PythonOperator(
            task_id="discover_landing_logs",
            python_callable=discover_landing_logs,
        )

        check_storage >> discover_logs

    # 2. BRONZE LAYER
    with TaskGroup(
        group_id="bronze_layer",
        tooltip="Parse OpenTelemetry JSON, Anti-join via Partition Pruning & Append to Bronze",
    ) as tg_bronze:
        spark_bronze = SparkSubmitOperator(
            task_id="ingest_logs_to_bronze",
            application=SPARK_APP_BRONZE,
            application_args=[
                "--run-id", "{{ ti.xcom_pull(task_ids='begin_run', key='run_id') }}",
                "--ingest-date", "{{ ti.xcom_pull(task_ids='begin_run', key='ingest_date') }}",
            ],
        )

    # 3. SILVER LAYER
    with TaskGroup(
        group_id="silver_layer",
        tooltip="Deduplicate by event_id, Flatten OpenTelemetry Structs & Append to Silver Logs",
    ) as tg_silver:
        spark_silver = SparkSubmitOperator(
            task_id="ingest_logs_to_silver",
            application=SPARK_APP_SILVER,
            application_args=[
                "--run-id", "{{ ti.xcom_pull(task_ids='begin_run', key='run_id') }}",
                "--ingest-date", "{{ ti.xcom_pull(task_ids='begin_run', key='ingest_date') }}",
            ],
        )

    # 4. GOLD LAYER (Ready for Web Traffic Facts & Route Performance Marts)
    with TaskGroup(
        group_id="gold_layer",
        tooltip="Build Traffic Facts, Search Demand Marts & Latency Aggregates",
    ) as tg_gold:
        gold_placeholder = EmptyOperator(
            task_id="gold_traffic_marts_ready",
        )

    # Pipeline End-to-End Orchestration: Staging -> Bronze -> Silver -> Gold
    begin >> tg_staging >> tg_bronze >> tg_silver >> tg_gold
