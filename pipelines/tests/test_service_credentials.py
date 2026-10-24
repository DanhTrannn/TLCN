from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def test_spark_uses_dedicated_minio_key_and_no_vended_credentials():
    text = _read("pipelines/src/lakehouse/spark.py")
    assert "MINIO_SPARK_ACCESS_KEY" in text
    assert "MINIO_SPARK_SECRET_KEY" in text
    assert "MINIO_ACCESS_KEY" not in text
    assert "MINIO_SECRET_KEY" not in text
    assert "X-Iceberg-Access-Delegation" not in text


def test_spark_catalog_sets_static_s3_properties():
    text = _read("pipelines/src/lakehouse/spark.py")
    for prop in (
        "spark.sql.catalog.lakehouse.s3.endpoint",
        "spark.sql.catalog.lakehouse.s3.access-key-id",
        "spark.sql.catalog.lakehouse.s3.secret-access-key",
        "spark.sql.catalog.lakehouse.s3.path-style-access",
    ):
        assert prop in text


def test_flink_uses_dedicated_minio_key_and_no_root_fallback():
    text = _read("pipelines/src/lakehouse/flink.py")
    assert "MINIO_FLINK_ACCESS_KEY" in text
    assert "MINIO_FLINK_SECRET_KEY" in text
    assert "minioadmin" not in text
    assert 'os.environ.get("AWS_ACCESS_KEY_ID"' not in text


def test_flink_config_has_no_static_secret():
    text = _read("infrastructure/flink/conf/flink-conf.yaml")
    assert "s3.access-key" not in text
    assert "s3.secret-key" not in text
    assert "minioadmin" not in text


def test_flink_wrapper_has_no_spark_principal_fallback():
    text = _read("infrastructure/flink/bin/with-polaris-credentials.sh")
    assert "POLARIS_SPARK_CLIENT_ID" not in text
    assert "POLARIS_SPARK_CLIENT_SECRET" not in text


def test_airflow_uses_airflow_minio_key():
    text = _read("airflow/dags/lakehouse_oltp_pipeline.py")
    assert "MINIO_AIRFLOW_ACCESS_KEY" in text
    assert "MINIO_AIRFLOW_SECRET_KEY" in text
    assert "minioadmin" not in text
    assert 'os.environ.get("MINIO_ACCESS_KEY"' not in text


def test_trino_disables_vended_credentials_and_uses_reader_storage_key():
    text = _read("infrastructure/trino/catalog/lakehouse.properties")
    assert "iceberg.rest-catalog.vended-credentials-enabled=false" in text
    assert "s3.aws-access-key=${ENV:MINIO_TRINO_ACCESS_KEY}" in text
    assert "s3.aws-secret-key=${ENV:MINIO_TRINO_SECRET_KEY}" in text


def test_trino_start_has_no_role_switch():
    text = _read("infrastructure/trino/start.sh")
    assert "TRINO_POLARIS_ROLE" not in text
    assert "POLARIS_TRINO_ADMIN_CLIENT_ID" in text
    assert "POLARIS_TRINO_CLIENT_ID" in text


def test_upload_script_uses_uploader_identity():
    text = _read("scripts/upload_generated_logs.sh")
    assert "MINIO_UPLOADER_ACCESS_KEY" in text
    assert "MINIO_UPLOADER_SECRET_KEY" in text
    assert "MINIO_ROOT_USER" not in text
    assert "MINIO_ROOT_PASSWORD" not in text
