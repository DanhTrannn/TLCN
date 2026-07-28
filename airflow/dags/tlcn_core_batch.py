from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator


def execute_stage(stage_name: str, **context):
    from tlcn_pipeline.runner import run_stage

    return run_stage(
        stage_name=stage_name,
        run_id=context["run_id"],
        logical_date=context["logical_date"].isoformat(),
    )


default_args = {
    "owner": "tlcn",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="tlcn_core_batch",
    description="MySQL OLTP to Bronze, Silver, Gold and analytics serving",
    start_date=datetime(2026, 1, 1),
    schedule="0 1 * * *",
    catchup=False,
    max_active_runs=1,
    default_args=default_args,
    tags=["tlcn", "core", "lakehouse"],
) as dag:
    task_names = (
        "check_services",
        "capture_mysql_high_cursors",
        "extract_mysql",
        "write_bronze",
        "validate_bronze",
        "build_silver_domain",
        "run_silver_dq",
        "build_gold_dimensions",
        "build_gold_facts",
        "build_gold_marts",
        "reconcile_source_to_gold",
        "publish_analytics_staging",
        "validate_publish",
        "swap_or_upsert_analytics",
        "commit_cursors",
        "publish_pipeline_audit",
    )
    tasks = {
        name: PythonOperator(
            task_id=name,
            python_callable=execute_stage,
            op_kwargs={"stage_name": name},
        )
        for name in task_names
    }

    tasks["check_services"] >> tasks["capture_mysql_high_cursors"]
    tasks["capture_mysql_high_cursors"] >> tasks["extract_mysql"]
    tasks["extract_mysql"] >> tasks["write_bronze"]
    tasks["write_bronze"] >> tasks["validate_bronze"]
    tasks["validate_bronze"] >> tasks["build_silver_domain"]
    tasks["build_silver_domain"] >> tasks["run_silver_dq"]
    tasks["run_silver_dq"] >> [tasks["build_gold_dimensions"], tasks["build_gold_facts"]]
    [tasks["build_gold_dimensions"], tasks["build_gold_facts"]] >> tasks["build_gold_marts"]
    tasks["build_gold_marts"] >> tasks["reconcile_source_to_gold"]
    tasks["reconcile_source_to_gold"] >> tasks["publish_analytics_staging"]
    tasks["publish_analytics_staging"] >> tasks["validate_publish"]
    tasks["validate_publish"] >> tasks["swap_or_upsert_analytics"]
    tasks["swap_or_upsert_analytics"] >> tasks["commit_cursors"]
    tasks["commit_cursors"] >> tasks["publish_pipeline_audit"]

