from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
COMPOSE = yaml.safe_load((ROOT / "docker-compose.yml").read_text(encoding="utf-8"))


def _env(service):
    return COMPOSE["services"][service].get("environment", {}) or {}


def _volumes(service):
    return "\n".join(COMPOSE["services"][service].get("volumes", []) or [])


def test_only_minio_and_minio_init_get_root_credentials():
    services_with_root = {
        name
        for name, service in COMPOSE["services"].items()
        if any(
            key in (service.get("environment", {}) or {})
            for key in ("MINIO_ROOT_USER", "MINIO_ROOT_PASSWORD")
        )
    }
    assert services_with_root == {"minio", "minio-init"}


def test_workloads_do_not_use_generic_root_minio_variables():
    for name in (
        "airflow-webserver", "airflow-scheduler", "flink-jobmanager",
        "flink-taskmanager", "flink-submit", "flink-cdc-submit",
        "polaris", "spark-client", "trino", "trino-admin",
    ):
        env = _env(name)
        assert "MINIO_ROOT_USER" not in env
        assert "MINIO_ROOT_PASSWORD" not in env
        assert "MINIO_ACCESS_KEY" not in env
        assert "MINIO_SECRET_KEY" not in env


def test_sensitive_ports_bind_localhost_by_default():
    expected = {
        "minio": ["${MINIO_BIND_ADDRESS:-127.0.0.1}"],
        "polaris": ["${POLARIS_BIND_ADDRESS:-127.0.0.1}"],
        "polaris-console": ["${POLARIS_BIND_ADDRESS:-127.0.0.1}"],
        "trino": ["${TRINO_BIND_ADDRESS:-127.0.0.1}"],
        "trino-admin": ["${TRINO_BIND_ADDRESS:-127.0.0.1}"],
    }
    for service, prefixes in expected.items():
        ports = COMPOSE["services"][service]["ports"]
        assert ports, service
        for prefix in prefixes:
            assert any(port.startswith(prefix + ":") for port in ports), (service, ports)


def test_workloads_mount_only_their_consumer_volume():
    expected = {
        "spark-client": "polaris-spark-client-credentials:/run/polaris:ro",
        "airflow-webserver": "polaris-spark-airflow-credentials:/run/polaris:ro",
        "airflow-scheduler": "polaris-spark-airflow-credentials:/run/polaris:ro",
        "flink-jobmanager": "polaris-flink-credentials:/run/polaris:ro",
        "flink-taskmanager": "polaris-flink-credentials:/run/polaris:ro",
        "flink-submit": "polaris-flink-credentials:/run/polaris:ro",
        "flink-cdc-submit": "polaris-flink-credentials:/run/polaris:ro",
        "trino": "polaris-trino-reader-credentials:/run/polaris:ro",
        "trino-admin": "polaris-trino-admin-credentials:/run/polaris:ro",
    }
    for service, mount in expected.items():
        text = _volumes(service)
        assert mount in text, (service, text)
        assert "polaris-client-credentials" not in text, service


def test_polaris_init_mounts_all_outputs_and_private_state():
    text = _volumes("polaris-init")
    for mount in (
        "polaris-credential-state:/run/polaris-state",
        "polaris-spark-client-credentials:/run/polaris-output/spark-client",
        "polaris-spark-airflow-credentials:/run/polaris-output/spark-airflow",
        "polaris-flink-credentials:/run/polaris-output/flink",
        "polaris-trino-reader-credentials:/run/polaris-output/trino-reader",
        "polaris-trino-admin-credentials:/run/polaris-output/trino-admin",
    ):
        assert mount in text, (mount, text)


def test_minio_init_mounts_policies_and_has_all_service_secrets():
    text = _volumes("minio-init")
    assert "./infrastructure/minio:/bootstrap:ro" in text
    env = _env("minio-init")
    for name in (
        "POLARIS", "SPARK", "FLINK", "AIRFLOW", "TRINO",
        "TRINO_ADMIN", "UPLOADER",
    ):
        assert f"MINIO_{name}_ACCESS_KEY" in env
        assert f"MINIO_{name}_SECRET_KEY" in env


def test_no_workload_mounts_the_old_shared_volume():
    for name, service in COMPOSE["services"].items():
        text = "\n".join(service.get("volumes", []) or [])
        assert "polaris-client-credentials" not in text, name
    assert "polaris-client-credentials" not in COMPOSE["volumes"]


def test_trino_admin_is_optional():
    assert COMPOSE["services"]["trino-admin"]["profiles"] == ["trino-admin"]


def test_example_does_not_use_password_defaults():
    text = (ROOT / ".env.example").read_text(encoding="utf-8")
    assert "MINIO_ROOT_PASSWORD=password" not in text
    for name in (
        "MINIO_POLARIS_SECRET_KEY",
        "MINIO_SPARK_SECRET_KEY",
        "MINIO_FLINK_SECRET_KEY",
        "MINIO_AIRFLOW_SECRET_KEY",
        "MINIO_TRINO_SECRET_KEY",
        "MINIO_TRINO_ADMIN_SECRET_KEY",
        "MINIO_UPLOADER_SECRET_KEY",
    ):
        line = next(line for line in text.splitlines() if line.startswith(name + "="))
        assert line.split("=", 1)[1] != "password"
