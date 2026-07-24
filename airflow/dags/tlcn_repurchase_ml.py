from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator


def execute_stage(stage_name: str, **context):
    from repurchase_ml.runner import run_stage

    return run_stage(
        stage_name=stage_name,
        run_id=context["run_id"],
        logical_date=context["logical_date"].isoformat(),
    )


stage_names = (
    "resolve_gold_publication",
    "build_point_in_time_features",
    "build_repurchase_labels",
    "validate_ml_dataset",
    "temporal_split",
    "train_dummy_and_logistic",
    "optional_train_random_forest",
    "evaluate_and_select",
    "persist_model_artifact_manifest",
    "batch_score_eligible_customers",
    "validate_predictions",
    "publish_repurchase_scores",
    "publish_ml_audit",
)

with DAG(
    dag_id="tlcn_repurchase_ml",
    description="Point-in-time repurchase training, evaluation and batch scoring",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    max_active_runs=1,
    default_args={
        "owner": "tlcn",
        "depends_on_past": False,
        "retries": 1,
        "retry_delay": timedelta(minutes=2),
    },
    tags=["tlcn", "ml", "repurchase"],
) as dag:
    tasks = [
        PythonOperator(
            task_id=stage_name,
            python_callable=execute_stage,
            op_kwargs={"stage_name": stage_name},
        )
        for stage_name in stage_names
    ]
    for current, following in zip(tasks, tasks[1:]):
        current >> following

