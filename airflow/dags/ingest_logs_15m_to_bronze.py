import uuid
from datetime import datetime, timedelta, timezone

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator

SPARK_APP = "/opt/project/pipelines/src/jobs/ingest_logs_to_bronze.py"

DEFAULT_ARGS = {
    "owner": "batch",
    "retries": 2,
    "retry_delay": timedelta(minutes=1),
}


def begin_run(**context) -> None:
    context["ti"].xcom_push(key="run_id", value=uuid.uuid4().hex)


with DAG(
    dag_id="ingest_logs_15m_to_bronze",
    default_args=DEFAULT_ARGS,
    schedule_interval="*/15 * * * *",
    start_date=datetime(2026, 8, 15, tzinfo=timezone.utc),
    catchup=False,
    max_active_runs=1,
    description="15-minute micro-batch ingestion of structured access logs from Landing to Bronze Iceberg",
) as dag:

    begin = PythonOperator(
        task_id="begin_run",
        python_callable=begin_run,
    )

    spark_ingest = SparkSubmitOperator(
        task_id="spark_logs_to_bronze",
        application=SPARK_APP,
        application_args=[
            "--run-id", "{{ ti.xcom_pull(task_ids='begin_run', key='run_id') }}",
            "--ingest-date", "{{ data_interval_start.strftime('%Y-%m-%d') }}",
            "--ingest-hour", "{{ data_interval_start.strftime('%H') }}",
        ],
    )

    begin >> spark_ingest
