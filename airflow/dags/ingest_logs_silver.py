import os
import uuid
from datetime import datetime, timedelta, timezone

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator

SPARK_APP = "/opt/project/pipelines/src/jobs/ingest_logs_silver.py"

DEFAULT_ARGS = {
    "owner": "batch",
    "retries": 2,
    "retry_delay": timedelta(minutes=1),
}


def begin_run(**context) -> None:
    context["ti"].xcom_push(key="run_id", value=uuid.uuid4().hex)
    context["ti"].xcom_push(
        key="ingest_date", value=datetime.now(timezone.utc).strftime("%Y-%m-%d")
    )


with DAG(
    dag_id="ingest_logs_bronze_to_silver",
    default_args=DEFAULT_ARGS,
    schedule="0 */2 * * *",
    catchup=False,
    start_date=datetime(2026, 8, 15, tzinfo=timezone.utc),
    description="Ingest Logs Bronze to Silver with dedup",
) as dag:

    begin = PythonOperator(task_id="begin_run", python_callable=begin_run)

    spark_ingest = SparkSubmitOperator(
        task_id="spark_logs_bronze_to_silver",
        application=SPARK_APP,
        application_args=[
            "--run-id", "{{ ti.xcom_pull(task_ids='begin_run', key='run_id') }}",
            "--ingest-date", "{{ ti.xcom_pull(task_ids='begin_run', key='ingest_date') }}",
        ],
    )

    begin >> spark_ingest