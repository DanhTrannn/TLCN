import uuid
from datetime import timedelta

import pendulum
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator

VN_TZ = pendulum.timezone("Asia/Ho_Chi_Minh")
SPARK_APP = "/opt/project/pipelines/src/jobs/oltp/ingest_oltp_to_bronze.py"

DEFAULT_ARGS = {
    "owner": "batch",
    "retries": 2,
    "retry_delay": timedelta(minutes=1),
}


def begin_run(**context) -> None:
    context["ti"].xcom_push(
        key="extract_date", value=pendulum.now("UTC").strftime("%Y-%m-%d")
    )


with DAG(
    dag_id="ingest_oltp_landing_to_bronze",
    default_args=DEFAULT_ARGS,
    schedule="0 2 * * *",  # Daily at 2 AM
    catchup=False,
    start_date=pendulum.datetime(2026, 8, 15, tz=VN_TZ),
    description="Ingest OLTP data from MinIO Landing Zone to Iceberg Bronze tables",
) as dag:

    begin = PythonOperator(
        task_id="begin_run",
        python_callable=begin_run,
    )

    ingest = SparkSubmitOperator(
        task_id="ingest_oltp_to_bronze",
        application=SPARK_APP,
        application_args=[
            "--extract-date", "{{ ti.xcom_pull(task_ids='begin_run', key='extract_date') }}",
        ],
    )

    begin >> ingest
