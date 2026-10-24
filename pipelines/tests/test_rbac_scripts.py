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


def test_scripts_assert_exact_403_without_non_2xx_weakening():
    for script in (
        ROOT / "scripts/verify_rbac_batch.sh",
        ROOT / "scripts/verify_rbac_streaming.sh",
    ):
        text = script.read_text(encoding="utf-8")
        assert '"403"' in text, script
        assert '!= "403"' in text, script
        assert "2xx" not in text.lower(), script
        assert "-ge 200" not in text, script
        assert "-lt 300" not in text, script


def test_minio_denials_require_an_explicit_access_denied_signal():
    expected_calls = {
        "verify_rbac_batch.sh": (
            "Flink PutObject landing/rbac-probe",
            "Trino reader PutObject warehouse/rbac-probe",
            "Airflow PutObject warehouse/rbac-probe",
        ),
        "verify_rbac_streaming.sh": (
            "Flink PutObject landing/rbac-probe",
        ),
    }
    for name, labels in expected_calls.items():
        text = (ROOT / "scripts" / name).read_text(encoding="utf-8")
        assert "expect_minio_denied()" in text, name
        assert "AccessDenied|Access Denied" in text, name
        assert "Insufficient permissions" in text, name
        for label in labels:
            assert f'expect_minio_denied "{label}"' in text, (name, label)
            assert f'expect_failure "{label}"' not in text, (name, label)


def test_uploader_rotation_restore_path_is_present():
    text = (ROOT / "scripts/verify_rbac_batch.sh").read_text(encoding="utf-8")
    assert "ROTATION_ACTIVE=1" in text
    assert "ROTATION_ACTIVE=0" in text
    assert "restore_uploader_secret" in text
    assert "MINIO_UPLOADER_SECRET_KEY" in text
    assert "minio-init" in text


def test_convergence_script_probes_and_prunes_rbac():
    text = (ROOT / "scripts/verify_rbac_convergence.sh").read_text(encoding="utf-8")
    assert "POLARIS_RBAC_CONFIG" in text
    assert "CATALOG_MANAGE_ACCESS" in text
    assert "PROBE_APPLIED" in text
    assert "rbac_probe" in text


def _extract_function(text, name):
    start = text.index(f"{name}() {{")
    end = text.index("\n}\n", start) + len("\n}\n")
    return text[start:end]


def test_minio_put_embedded_script_parses():
    for script in (
        ROOT / "scripts/verify_rbac_batch.sh",
        ROOT / "scripts/verify_rbac_streaming.sh",
    ):
        function = _extract_function(script.read_text(encoding="utf-8"), "minio_put")
        wrapper = (
            "set -euo pipefail\n"
            "compose() {\n"
            "  local take_payload=0\n"
            "  local arg\n"
            '  for arg in "$@"; do\n'
            "    if (( take_payload )); then\n"
            "      printf '%s' \"$arg\"\n"
            "      return 0\n"
            "    fi\n"
            '    if [[ "$arg" == -c ]]; then take_payload=1; fi\n'
            "  done\n"
            "  return 1\n"
            "}\n"
            f"{function}\n"
            "minio_put KEY SECRET object\n"
        )
        captured = subprocess.run(
            ["bash", "-c", wrapper], capture_output=True, text=True
        )
        assert captured.returncode == 0, (script, captured.stderr)
        parsed = subprocess.run(
            ["sh", "-n"], input=captured.stdout, capture_output=True, text=True
        )
        assert parsed.returncode == 0, (script, parsed.stderr, captured.stdout)


def test_streaming_exec_checks_source_credential_file():
    text = (ROOT / "scripts/verify_rbac_streaming.sh").read_text(encoding="utf-8")

    def exec_check(service):
        marker = f"compose exec -T {service} sh -c '"
        start = text.index(marker)
        end = text.index("\n'", start)
        return text[start:end]

    flink_check = exec_check("flink-jobmanager")
    assert ". /run/polaris/clients.env" in flink_check
    assert 'test -z "${POLARIS_SPARK_CLIENT_ID:-}"' in flink_check
    assert 'test -n "${POLARIS_FLINK_CLIENT_ID:-}"' in flink_check

    trino_check = exec_check("trino")
    assert ". /run/polaris/clients.env" in trino_check
    assert 'test -z "${POLARIS_TRINO_ADMIN_CLIENT_ID:-}"' in trino_check
    assert 'test -n "${POLARIS_TRINO_CLIENT_ID:-}"' in trino_check
