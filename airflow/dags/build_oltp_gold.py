import uuid
from datetime import timedelta

import pendulum
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator

VN_TZ = pendulum.timezone("Asia/Ho_Chi_Minh")
SPARK_APP = "/opt/project/pipelines/src/jobs/oltp/build_oltp_gold.py"

DEFAULT_ARGS = {
    "owner": "batch",
    "retries": 2,
    "retry_delay": timedelta(minutes=1),
}


def begin_run(**context) -> None:
    context["ti"].xcom_push(key="run_id", value=uuid.uuid4().hex)
    context["ti"].xcom_push(
        key="snapshot_date", value=pendulum.now(VN_TZ).strftime("%Y-%m-%d")
    )


with DAG(
    dag_id="build_oltp_gold",
    default_args=DEFAULT_ARGS,
    schedule="30 2 * * *",
    catchup=False,
    start_date=pendulum.datetime(2026, 8, 15, tz=VN_TZ),
    description="Build OLTP Gold layer tables (Star Schema & Marts) from Silver",
) as dag:

    begin = PythonOperator(task_id="begin_run", python_callable=begin_run)

    spark_gold = SparkSubmitOperator(
        task_id="spark_build_oltp_gold",
        application=SPARK_APP,
        application_args=[
            "--run-id", "{{ ti.xcom_pull(task_ids='begin_run', key='run_id') }}",
            "--snapshot-date", "{{ ti.xcom_pull(task_ids='begin_run', key='snapshot_date') }}",
        ],
    )

    begin >> spark_gold
