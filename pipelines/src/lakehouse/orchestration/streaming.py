"""Streaming health and interval context, independent of Airflow imports."""

import os
import uuid

REQUIRED_JOBS = ("kafka_to_lakehouse_pure_streaming", "oltp_cdc_to_bronze")


def validate_streaming_jobs(jobs: list[dict], required=REQUIRED_JOBS) -> list[dict]:
    running = {job.get("name"): job for job in jobs if job.get("state") == "RUNNING"}
    missing = set(required) - running.keys()
    if missing:
        raise RuntimeError(f"Required streaming jobs are not RUNNING: {sorted(missing)}")
    return [running[name] for name in required]


def begin_run(**context):
    import pendulum

    logical = context.get("data_interval_start") or context.get("logical_date")
    logical = logical or pendulum.now("Asia/Ho_Chi_Minh")
    ti = context["ti"]
    ti.xcom_push(key="run_id", value=uuid.uuid4().hex)
    ti.xcom_push(key="ingest_date", value=logical.in_timezone("UTC").strftime("%Y-%m-%d"))


def check_flink_streaming_health(**context):
    import requests

    host = os.environ.get("FLINK_JOBMANAGER_HOST", "flink-jobmanager")
    port = os.environ.get("FLINK_JOBMANAGER_PORT", "8081")
    response = requests.get(f"http://{host}:{port}/jobs/overview", timeout=15)
    response.raise_for_status()
    required = tuple(filter(None, os.environ.get("FLINK_REQUIRED_JOBS", ",".join(REQUIRED_JOBS)).split(",")))
    if not required:
        raise ValueError("FLINK_REQUIRED_JOBS must not be empty")
    jobs = validate_streaming_jobs(response.json().get("jobs", []), required)
    context["ti"].xcom_push(key="active_flink_jobs", value=jobs)
    return jobs
