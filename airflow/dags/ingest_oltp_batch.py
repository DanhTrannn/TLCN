import json
import os
import uuid
from datetime import datetime, timedelta, timezone

import pymysql
from airflow import DAG
from airflow.exceptions import AirflowException
from airflow.operators.python import PythonOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from sqlalchemy.engine.url import make_url

from lakehouse.config import load_config
from lakehouse.validate import s3_client, validate_run

CONFIG_PATH = os.environ["PIPELINE_CONFIG_PATH"]
SPARK_APP = "/opt/project/pipelines/src/jobs/extract_oltp.py"

DEFAULT_ARGS = {
    "owner": "batch",
    "retries": 2,
    "retry_delay": timedelta(minutes=1),
}


def _mysql_conn():
    url = make_url(os.environ["MYSQL_ECOMMERCE_READER_URL"])
    return pymysql.connect(
        host=url.host, port=url.port or 3306, user=url.username,
        password=url.password, database=url.database, connect_timeout=10,
    )


def check_mysql() -> str:
    conn = _mysql_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
    finally:
        conn.close()
    return "ok"


def begin_run(**context) -> None:
    context["ti"].xcom_push(key="run_id", value=uuid.uuid4().hex)
    context["ti"].xcom_push(
        key="extract_date", value=datetime.now(timezone.utc).strftime("%Y-%m-%d")
    )


def capture_high_watermarks() -> dict:
    cfg = load_config(CONFIG_PATH)
    conn = _mysql_conn()
    result = {}
    try:
        with conn.cursor() as cur:
            for table in cfg.tables:
                cur.execute(
                    f"SELECT MAX(`{table.cursor_field}`) AS at, "
                    f"MAX(`{table.pk}`) AS pk_at_max "
                    f"FROM `{table.name}` "
                    f"WHERE `{table.cursor_field}` = "
                    f"(SELECT MAX(`{table.cursor_field}`) FROM `{table.name}`)"
                )
                row = cur.fetchone()
                result[table.name] = {"at": str(row[0]), "pk": row[1]}
    finally:
        conn.close()
    return result


def validate_landing_manifests(**context) -> None:
    cfg = load_config(CONFIG_PATH)
    run_id = context["ti"].xcom_pull(task_ids="begin_run", key="run_id")
    extract_date = context["ti"].xcom_pull(task_ids="begin_run", key="extract_date")
    s3 = s3_client(
        os.environ["MINIO_ENDPOINT"], os.environ["MINIO_ACCESS_KEY"],
        os.environ["MINIO_SECRET_KEY"],
    )
    violations = validate_run(
        s3, cfg.bucket, [t.name for t in cfg.tables], extract_date, run_id
    )
    bad = {table: v for table, v in violations.items() if v}
    if bad:
        raise AirflowException(f"manifest violations: {json.dumps(bad)}")


with DAG(
    dag_id="ingest_oltp_batch",
    default_args=DEFAULT_ARGS,
    schedule=None,
    catchup=False,
    start_date=datetime(2026, 8, 15, tzinfo=timezone.utc),
    description="Extract OLTP tables to MinIO landing with manifests",
) as dag:

    check = PythonOperator(task_id="check_mysql", python_callable=check_mysql)

    begin = PythonOperator(task_id="begin_run", python_callable=begin_run)

    capture = PythonOperator(
        task_id="capture_high_watermarks",
        python_callable=capture_high_watermarks,
    )

    extract = SparkSubmitOperator(
        task_id="extract_tables_to_landing",
        application=SPARK_APP,
        application_args=[
            "--config-path", CONFIG_PATH,
            "--run-id", "{{ ti.xcom_pull(task_ids='begin_run', key='run_id') }}",
            "--extract-date", "{{ ti.xcom_pull(task_ids='begin_run', key='extract_date') }}",
            "--high-watermarks",
            "{{ ti.xcom_pull(task_ids='capture_high_watermarks') | tojson }}",
        ],
    )

    validate = PythonOperator(
        task_id="validate_landing_manifests",
        python_callable=validate_landing_manifests,
    )

    check >> begin >> capture >> extract >> validate