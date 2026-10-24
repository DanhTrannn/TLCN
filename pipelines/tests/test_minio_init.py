import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INIT = ROOT / "infrastructure/minio/init.sh"


def test_init_script_has_valid_shell_syntax():
    result = subprocess.run(["sh", "-n", str(INIT)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_init_script_manages_every_service_identity():
    text = INIT.read_text(encoding="utf-8")
    for user in (
        "lakehouse-polaris",
        "lakehouse-spark",
        "lakehouse-flink",
        "lakehouse-airflow",
        "lakehouse-trino",
        "lakehouse-trino-admin",
        "lakehouse-uploader",
    ):
        assert user in text
    for policy in (
        "lakehouse-polaris",
        "lakehouse-spark",
        "lakehouse-flink",
        "lakehouse-airflow",
        "lakehouse-trino",
        "lakehouse-trino-admin",
        "lakehouse-uploader",
    ):
        assert policy in text
    assert "POLICY_DIR" in text
    assert ".json" in text


def test_init_script_is_convergent_and_never_touches_non_managed_principals():
    text = INIT.read_text(encoding="utf-8")
    assert "mc admin user remove" in text
    assert "mc admin policy remove" in text
    assert "lakehouse-*" in text
    assert "mc anonymous set none" in text
    assert "mc mb --ignore-existing" in text
    assert "MINIO_ROOT_USER" in text
    assert "__MINIO_BUCKET__" in text
