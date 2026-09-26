"""Lakehouse Streaming Maintenance & Data Marts DAG.

Chuyên trách duy trì, tối ưu hóa và tổng hợp dữ liệu cho luồng Pure Streaming:
  1. Healthcheck & giám sát luồng Flink streaming (JobManager REST API).
  2. Iceberg Compaction (rewrite_data_files & rewrite_manifests) gom nhỏ files Parquet.
  3. Expire Snapshots dọn dẹp metadata lịch sử, giảm dung lượng catalog.
  4. Remove Orphan Files dọn dẹp các tệp rác không được tham chiếu trên MinIO.
  5. Rollup Gold Data Marts (mart_hourly_route_metrics, mart_daily_product_demand) từ fact_web_events real-time.
"""

import os
import uuid
from datetime import timedelta
import pendulum
import requests

from airflow import DAG
from airflow.exceptions import AirflowException
from airflow.operators.python import PythonOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.utils.task_group import TaskGroup

VN_TZ = pendulum.timezone("Asia/Ho_Chi_Minh")

SPARK_APP_MAINTENANCE = "/opt/project/pipelines/src/jobs/maintenance/iceberg_table_maintenance.py"
SPARK_APP_GOLD_MARTS = "/opt/project/pipelines/src/jobs/logs/build_logs_gold.py"

TABLES_LIST = "landing.access_logs,bronze.web_events,silver.silver_logs,gold.fact_web_events"

DEFAULT_ARGS = {
    "owner": "lakehouse",
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}


def begin_run(**context) -> None:
    run_id = uuid.uuid4().hex
    ingest_date = pendulum.now(VN_TZ).strftime("%Y-%m-%d")
    context["ti"].xcom_push(key="run_id", value=run_id)
    context["ti"].xcom_push(key="ingest_date", value=ingest_date)
    print(f"[begin_run] Initialized maintenance run {run_id} for date {ingest_date}")


def check_flink_streaming_health(**context) -> dict:
    """Monitor Flink JobManager to ensure the Pure Streaming pipeline is healthy.

    Queries Flink REST API at http://flink-jobmanager:8081/jobs/overview.
    Ensures at least one streaming job is in state 'RUNNING'.
    """
    flink_host = os.environ.get("FLINK_JOBMANAGER_HOST", "flink-jobmanager")
    flink_port = os.environ.get("FLINK_JOBMANAGER_PORT", "8081")
    url = f"http://{flink_host}:{flink_port}/jobs/overview"

    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        raise AirflowException(f"Cannot reach Flink JobManager at {url}: {exc}") from exc

    jobs = data.get("jobs", [])
    running_jobs = [j for j in jobs if j.get("state") == "RUNNING"]

    if not running_jobs:
        raise AirflowException(
            f"No running Flink streaming jobs detected! Total jobs found: {len(jobs)}. "
            f"Details: {jobs}"
        )

    matched_jobs = [
        j for j in running_jobs
        if any(term in j.get("name", "").lower() for term in ["kafka", "lakehouse", "landing", "access_logs"])
    ]

    active_job = matched_jobs[0] if matched_jobs else running_jobs[0]
    job_info = {
        "job_id": active_job.get("jid"),
        "name": active_job.get("name"),
        "state": active_job.get("state"),
        "uptime_ms": active_job.get("duration"),
        "last_modification": active_job.get("last-modification"),
    }

    print(
        f"[check_flink_streaming_health] Healthy! Active streaming job: "
        f"{job_info['name']} (ID: {job_info['job_id']}, state: {job_info['state']}, duration: {job_info['uptime_ms']}ms)"
    )
    context["ti"].xcom_push(key="active_flink_job", value=job_info)
    return job_info


with DAG(
    dag_id="lakehouse_streaming_maintenance",
    default_args=DEFAULT_ARGS,
    schedule="0 */2 * * *",  # Every 2 hours
    max_active_runs=1,
    catchup=False,
    start_date=pendulum.datetime(2026, 8, 15, tz=VN_TZ),
    description=(
        "Pure Streaming Lakehouse Maintenance DAG: "
        "Flink Healthcheck -> Iceberg Compaction & Snapshot Expiry -> Gold Marts Rollup"
    ),
    tags=["lakehouse", "streaming", "maintenance", "iceberg", "compaction"],
) as dag:

    begin = PythonOperator(
        task_id="begin_run",
        python_callable=begin_run,
    )

    # 1. STREAMING HEALTH MONITORING
    with TaskGroup(
        group_id="stream_monitoring",
        tooltip="Verify Flink streaming pipeline is actively RUNNING",
    ) as tg_stream:
        monitor_flink = PythonOperator(
            task_id="check_flink_streaming_health",
            python_callable=check_flink_streaming_health,
        )

    # 2. ICEBERG COMPACTION & MAINTENANCE
    with TaskGroup(
        group_id="iceberg_maintenance",
        tooltip="Compact small files, rewrite manifests, expire old snapshots & remove orphan files",
    ) as tg_maintenance:
        compact_tables = SparkSubmitOperator(
            task_id="compact_iceberg_tables",
            application=SPARK_APP_MAINTENANCE,
            application_args=[
                "--action", "compact",
                "--tables", TABLES_LIST,
            ],
        )

        expire_snapshots = SparkSubmitOperator(
            task_id="expire_iceberg_snapshots",
            application=SPARK_APP_MAINTENANCE,
            application_args=[
                "--action", "expire",
                "--retain-snapshots", "20",
                "--tables", TABLES_LIST,
            ],
        )

        remove_orphans = SparkSubmitOperator(
            task_id="remove_orphan_files",
            application=SPARK_APP_MAINTENANCE,
            application_args=[
                "--action", "orphan",
                "--tables", TABLES_LIST,
            ],
        )

        compact_tables >> expire_snapshots >> remove_orphans

    # 3. GOLD DATA MARTS PERIODIC ROLLUP
    with TaskGroup(
        group_id="gold_marts",
        tooltip="Refresh hourly route latency & daily product demand data marts from fact_web_events",
    ) as tg_gold_marts:
        rollup_gold = SparkSubmitOperator(
            task_id="rollup_logs_gold_marts",
            application=SPARK_APP_GOLD_MARTS,
            application_args=[
                "--run-id", "{{ ti.xcom_pull(task_ids='begin_run', key='run_id') }}",
                "--ingest-date", "{{ ti.xcom_pull(task_ids='begin_run', key='ingest_date') }}",
            ],
        )

    # Pipeline Flow:
    # 1. Begin -> 2. Check Flink Stream Health -> 3. Iceberg Maintenance -> 4. Gold Marts Rollup
    begin >> tg_stream >> tg_maintenance >> tg_gold_marts
