import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = [
    ROOT / "scripts/verify_rbac_batch.sh",
    ROOT / "scripts/verify_rbac_streaming.sh",
    ROOT / "scripts/verify_rbac_convergence.sh",
]


def test_rbac_scripts_exist_and_are_executable():
    for script in SCRIPTS:
        assert script.is_file(), script
        assert script.stat().st_mode & 0o111, script


def test_rbac_scripts_parse():
    for script in SCRIPTS:
        result = subprocess.run(["bash", "-n", str(script)], capture_output=True, text=True)
        assert result.returncode == 0, (script, result.stderr)


def test_batch_script_covers_reader_writer_minio_and_convergence():
    text = (ROOT / "scripts/verify_rbac_batch.sh").read_text(encoding="utf-8")
    for needle in (
        "system.stack_smoke",
        "api/management/v1/principals",
        "POLARIS_TRINO_CLIENT_ID",
        "MINIO_FLINK_ACCESS_KEY",
        "MINIO_TRINO_ACCESS_KEY",
        "MINIO_AIRFLOW_ACCESS_KEY",
        "anonymous",
        "verify_rbac_convergence.sh",
    ):
        haystack = text.lower() if needle == "anonymous" else text
        assert needle in haystack, needle


def test_streaming_script_covers_flink_isolation_and_minio_boundary():
    text = (ROOT / "scripts/verify_rbac_streaming.sh").read_text(encoding="utf-8")
    for needle in (
        "POLARIS_SPARK_CLIENT_ID",
        "POLARIS_FLINK_CLIENT_ID",
        "MINIO_FLINK_ACCESS_KEY",
        "MINIO_TRINO_ADMIN_ACCESS_KEY",
        "api/management/v1/principals",
    ):
        assert needle in text, needle
