import os
import uuid
from datetime import datetime, timedelta, timezone

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator

CONFIG_PATH = os.environ["PIPELINE_CONFIG_PATH"]
SPARK_APP = "/opt/project/pipelines/src/jobs/ingest_oltp_silver.py"

DEFAULT_ARGS = {
    "owner": "batch",
    "retries": 2,
    "retry_delay": timedelta(minutes=1),
}


def begin_run(**context) -> None:
    context["ti"].xcom_push(key="run_id", value=uuid.uuid4().hex)
    context["ti"].xcom_push(
        key="bronze_date", value=datetime.now(timezone.utc).strftime("%Y-%m-%d")
    )


with DAG(
    dag_id="ingest_oltp_bronze_to_silver",
    default_args=DEFAULT_ARGS,
    schedule=None,
    catchup=False,
    start_date=datetime(2026, 8, 15, tzinfo=timezone.utc),
    description="Ingest OLTP Bronze tables to Silver via MERGE",
) as dag:

    begin = PythonOperator(task_id="begin_run", python_callable=begin_run)

    spark_ingest = SparkSubmitOperator(
        task_id="spark_oltp_bronze_to_silver",
        application=SPARK_APP,
        application_args=[
            "--config-path", CONFIG_PATH,
            "--run-id", "{{ ti.xcom_pull(task_ids='begin_run', key='run_id') }}",
            "--bronze-date", "{{ ti.xcom_pull(task_ids='begin_run', key='bronze_date') }}",
        ],
    )

    begin >> spark_ingest