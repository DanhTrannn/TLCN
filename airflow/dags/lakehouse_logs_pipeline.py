import uuid
from datetime import timedelta

import pendulum
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.utils.task_group import TaskGroup

VN_TZ = pendulum.timezone("Asia/Ho_Chi_Minh")

SPARK_APP_BRONZE = "/opt/project/pipelines/src/jobs/logs/ingest_logs_to_bronze.py"
SPARK_APP_SILVER = "/opt/project/pipelines/src/jobs/logs/ingest_logs_silver.py"
SPARK_APP_GOLD = "/opt/project/pipelines/src/jobs/logs/build_logs_gold.py"

DEFAULT_ARGS = {
    "owner": "lakehouse",
    "retries": 2,
    "retry_delay": timedelta(minutes=1),
}


def begin_run(**context) -> None:
    run_id = uuid.uuid4().hex
    ingest_date = pendulum.now("UTC").strftime("%Y-%m-%d")
    context["ti"].xcom_push(key="run_id", value=run_id)
    context["ti"].xcom_push(key="ingest_date", value=ingest_date)


def check_iceberg_landing(**context) -> int:
    """Count rows in lakehouse.landing.access_logs for today's ingest date.

    Uses the Trino REST API so Airflow workers need no Spark session.
    Returns the row count and stores it as XCom for downstream visibility.
    """
    import os

    import requests

    ingest_date = context["ti"].xcom_pull(task_ids="begin_run", key="ingest_date")

    trino_host = os.environ.get("TRINO_HOST", "trino")
    trino_port = os.environ.get("TRINO_PORT", "8080")
    trino_user = os.environ.get("TRINO_USER", "trino_admin")

    # Count landing rows written today (event_ts cast to date for partition awareness)
    query = (
        "SELECT COUNT(*) FROM lakehouse.landing.access_logs "
        f"WHERE CAST(event_ts AS DATE) = DATE '{ingest_date}'"
    )

    url = f"http://{trino_host}:{trino_port}/v1/statement"
    headers = {"X-Trino-User": trino_user, "X-Trino-Catalog": "lakehouse", "X-Trino-Schema": "landing"}

    # Trino REST API: POST query then follow nextUri until done
    resp = requests.post(url, data=query, headers=headers, timeout=30)
    resp.raise_for_status()
    result = resp.json()

    # Follow pagination until final response with data
    while "nextUri" in result:
        resp = requests.get(result["nextUri"], headers=headers, timeout=30)
        resp.raise_for_status()
        result = resp.json()

    rows = result.get("data", [])
    count = int(rows[0][0]) if rows else 0

    print(f"[check_iceberg_landing] landing.access_logs rows for {ingest_date}: {count}")
    context["ti"].xcom_push(key="landing_row_count", value=count)
    return count


with DAG(
    dag_id="lakehouse_logs_pipeline",
    default_args=DEFAULT_ARGS,
    schedule="0 */2 * * *",  # Every 2 hours
    catchup=False,
    start_date=pendulum.datetime(2026, 8, 15, tz=VN_TZ),
    description=(
        "End-to-End Medallion Lakehouse Logs Pipeline: "
        "Iceberg Landing (via Flink) -> Bronze -> Silver -> Gold"
    ),
    tags=["lakehouse", "logs", "medallion", "production", "streaming"],
) as dag:

    begin = PythonOperator(
        task_id="begin_run",
        python_callable=begin_run,
    )

    # 1. LANDING LAYER CHECK (Iceberg – written by Flink streaming job)
    with TaskGroup(
        group_id="landing_layer",
        tooltip="Verify Iceberg Landing table has rows for today (written by Flink+Kafka)",
    ) as tg_landing:
        check_landing = PythonOperator(
            task_id="check_iceberg_landing",
            python_callable=check_iceberg_landing,
        )

    # 2. BRONZE LAYER
    with TaskGroup(
        group_id="bronze_layer",
        tooltip="Read from Iceberg Landing, parse/validate & append to Bronze",
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

    # 4. GOLD LAYER (Star Schema Fact & Data Marts)
    with TaskGroup(
        group_id="gold_layer",
        tooltip="Build Web Event Facts, Route Latency & Product Demand Data Marts",
    ) as tg_gold:
        spark_gold = SparkSubmitOperator(
            task_id="build_logs_gold",
            application=SPARK_APP_GOLD,
            application_args=[
                "--run-id", "{{ ti.xcom_pull(task_ids='begin_run', key='run_id') }}",
                "--ingest-date", "{{ ti.xcom_pull(task_ids='begin_run', key='ingest_date') }}",
            ],
        )

    # Pipeline: Landing Check -> Bronze -> Silver -> Gold
    begin >> tg_landing >> tg_bronze >> tg_silver >> tg_gold
