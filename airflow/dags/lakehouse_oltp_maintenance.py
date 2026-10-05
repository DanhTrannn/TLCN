"""Lakehouse OLTP Iceberg Table Maintenance DAG.

Chuyên trách duy trì, tối ưu hóa và dọn dẹp định kỳ cho các bảng Iceberg OLTP (Bronze, Silver, Gold):
  1. Iceberg Compaction (rewrite_data_files & rewrite_manifests): Gom các file Parquet nhỏ sinh ra
     từ các batch nạp định kỳ thành file chuẩn 128MB, giảm thiểu small files.
  2. Expire Snapshots: Dọn dẹp metadata lịch sử, chỉ giữ lại các snapshot gần nhất (retention policy),
     ngăn chặn metadata bloat và tăng tốc độ scan của Trino Query Engine.
  3. Remove Orphan Files: Dọn dẹp các tệp rác không được tham chiếu trên MinIO/S3 phát sinh từ các
     tác vụ Spark bị ngắt quãng hoặc rollback.

Tách biệt hoàn toàn khỏi luồng Ingestion tần suất cao (lakehouse_oltp_pipeline) để bảo vệ
Data Freshness SLA và tránh lãng phí compute ngoài giờ cao điểm (chạy định kỳ 03:00 AM hàng ngày).
"""

from __future__ import annotations

import uuid
from datetime import timedelta

import pendulum
from airflow.operators.python import PythonOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.utils.task_group import TaskGroup

from airflow import DAG

VN_TZ = pendulum.timezone("Asia/Ho_Chi_Minh")

SPARK_APP_MAINTENANCE = "/opt/project/pipelines/src/jobs/maintenance/iceberg_table_maintenance.py"

DEFAULT_ARGS = {
    "owner": "lakehouse",
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}


def begin_run(**context) -> None:
    run_id = uuid.uuid4().hex
    maintenance_date = pendulum.now(VN_TZ).strftime("%Y-%m-%d")
    context["ti"].xcom_push(key="run_id", value=run_id)
    context["ti"].xcom_push(key="maintenance_date", value=maintenance_date)
    print(f"[begin_run] Initialized OLTP Iceberg maintenance run {run_id} for date {maintenance_date}")


with DAG(
    dag_id="lakehouse_oltp_maintenance",
    default_args=DEFAULT_ARGS,
    schedule="0 3 * * *",  # Daily at 3 AM Ho Chi Minh time (off-peak)
    max_active_runs=1,
    catchup=False,
    start_date=pendulum.datetime(2026, 8, 15, tz=VN_TZ),
    description=(
        "Scheduled Iceberg Table Maintenance for OLTP Lakehouse: "
        "Compaction (128MB) -> Expire Old Snapshots -> Remove Orphan Files"
    ),
    tags=["lakehouse", "oltp", "maintenance", "iceberg", "compaction"],
) as dag:

    check_context = PythonOperator(
        task_id="check_maintenance_context",
        python_callable=begin_run,
    )

    with TaskGroup(
        group_id="iceberg_maintenance",
        tooltip="Compact small Parquet files, rewrite manifests, expire old snapshots & remove orphans for OLTP tables",
    ) as tg_maintenance:
        compact_oltp = SparkSubmitOperator(
            task_id="transform_compact_tables",
            application=SPARK_APP_MAINTENANCE,
            application_args=[
                "--action", "compact",
                "--profile", "oltp",
                "--target-file-size-bytes", "134217728",
            ],
        )

        expire_oltp = SparkSubmitOperator(
            task_id="cleanup_expired_snapshots",
            application=SPARK_APP_MAINTENANCE,
            application_args=[
                "--action", "expire",
                "--profile", "oltp",
                "--retain-snapshots", "10",
            ],
        )

        remove_oltp_orphans = SparkSubmitOperator(
            task_id="cleanup_orphan_files",
            application=SPARK_APP_MAINTENANCE,
            application_args=[
                "--action", "orphan",
                "--profile", "oltp",
            ],
        )

        compact_oltp >> expire_oltp >> remove_oltp_orphans

    # Orchestration Flow:
    # 1. Check Context -> 2. Iceberg Maintenance (Compaction -> Expire Snapshots -> Remove Orphans)
    check_context >> tg_maintenance
