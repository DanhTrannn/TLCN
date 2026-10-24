"""Tests for the Polaris RBAC reconciler in infrastructure/polaris/sync_polaris_rbac.py."""

import importlib.util
import os
import stat
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "infrastructure/polaris/sync_polaris_rbac.py"

spec = importlib.util.spec_from_file_location("sync_polaris_rbac", MODULE_PATH)
assert spec and spec.loader
rbac = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rbac)


class FakePolarisClient:
    def __init__(self, responses=None):
        self.responses = responses or {}
        self.calls = []

    def request(self, method, path, payload=None, expected_statuses=(200, 201, 204)):
        self.calls.append({"method": method, "path": path, "payload": payload})
        return self.responses.get((method, path), (200, {}))


def _credential_config(tmp_path):
    return {
        "catalog": {"name": "lakehouse"},
        "principals": {
            "spark_writer": {
                "credentials_export": {
                    "client_id_var": "POLARIS_SPARK_CLIENT_ID",
                    "client_secret_var": "POLARIS_SPARK_CLIENT_SECRET",
                }
            },
            "flink_writer": {
                "credentials_export": {
                    "client_id_var": "POLARIS_FLINK_CLIENT_ID",
                    "client_secret_var": "POLARIS_FLINK_CLIENT_SECRET",
                }
            },
        },
        "credential_outputs": [
            {
                "principal": "spark_writer",
                "directory": str(tmp_path / "spark"),
                "uid": os.getuid(),
                "gid": os.getgid(),
            },
            {
                "principal": "flink_writer",
                "directory": str(tmp_path / "flink"),
                "uid": os.getuid(),
                "gid": os.getgid(),
            },
        ],
    }


def test_credential_outputs_are_private_and_isolated(tmp_path):
    config = _credential_config(tmp_path)
    reconciler = rbac.PolarisRbacReconciler(
        FakePolarisClient(), config, state_file=tmp_path / "state.env"
    )
    reconciler.output_creds = {
        "POLARIS_SPARK_CLIENT_ID": "spark-id",
        "POLARIS_SPARK_CLIENT_SECRET": "spark-secret",
        "POLARIS_FLINK_CLIENT_ID": "flink-id",
        "POLARIS_FLINK_CLIENT_SECRET": "flink-secret",
    }

    reconciler.write_credentials()

    spark_file = tmp_path / "spark" / "clients.env"
    flink_file = tmp_path / "flink" / "clients.env"
    assert stat.S_IMODE(spark_file.stat().st_mode) == 0o600
    assert stat.S_IMODE(flink_file.stat().st_mode) == 0o600
    assert stat.S_IMODE(spark_file.parent.stat().st_mode) == 0o700
    assert stat.S_IMODE(flink_file.parent.stat().st_mode) == 0o700

    spark_text = spark_file.read_text()
    flink_text = flink_file.read_text()
    assert "POLARIS_SPARK_CLIENT_ID='spark-id'" in spark_text
    assert "POLARIS_SPARK_CLIENT_SECRET='spark-secret'" in spark_text
    assert "POLARIS_FLINK" not in spark_text
    assert "POLARIS_FLINK_CLIENT_ID='flink-id'" in flink_text
    assert "POLARIS_FLINK_CLIENT_SECRET='flink-secret'" in flink_text
    assert "POLARIS_SPARK" not in flink_text


def test_state_file_is_private_and_contains_all_managed_credentials(tmp_path):
    config = _credential_config(tmp_path)
    reconciler = rbac.PolarisRbacReconciler(
        FakePolarisClient(), config, state_file=tmp_path / "state" / "credentials.env"
    )
    reconciler.output_creds = {
        "POLARIS_SPARK_CLIENT_ID": "spark-id",
        "POLARIS_SPARK_CLIENT_SECRET": "spark-secret",
        "POLARIS_FLINK_CLIENT_ID": "flink-id",
        "POLARIS_FLINK_CLIENT_SECRET": "flink-secret",
    }

    reconciler.write_credential_state()

    state_file = tmp_path / "state" / "credentials.env"
    assert stat.S_IMODE(state_file.stat().st_mode) == 0o600
    assert stat.S_IMODE(state_file.parent.stat().st_mode) == 0o700
    text = state_file.read_text()
    for value in ("spark-id", "spark-secret", "flink-id", "flink-secret"):
        assert value in text


def test_missing_principal_credential_fails_fast(tmp_path):
    config = _credential_config(tmp_path)
    reconciler = rbac.PolarisRbacReconciler(
        FakePolarisClient(), config, state_file=tmp_path / "state.env"
    )
    reconciler.output_creds = {"POLARIS_SPARK_CLIENT_ID": "spark-id"}

    try:
        reconciler.write_credential_outputs()
    except RuntimeError as exc:
        assert "POLARIS_SPARK_CLIENT_SECRET" in str(exc)
    else:
        raise AssertionError("missing credential secret did not fail")


def test_add_grant_uses_grant_wrapper(tmp_path):
    client = FakePolarisClient({
        ("GET", "/api/management/v1/catalogs/lakehouse/catalog-roles/spark_writer_catalog_role"): (200, {}),
        ("GET", "/api/management/v1/catalogs/lakehouse/catalog-roles/spark_writer_catalog_role/grants"): (200, {"grants": []}),
    })
    config = {
        "catalog": {"name": "lakehouse"},
        "catalog_roles": {
            "spark_writer_catalog_role": {
                "grants": [{"type": "catalog", "privilege": "CATALOG_MANAGE_CONTENT"}]
            }
        },
    }
    reconciler = rbac.PolarisRbacReconciler(
        client, config, state_file=tmp_path / "state.env"
    )
    reconciler.reconcile_catalog_roles()

    put = next(call for call in client.calls if call["method"] == "PUT")
    assert put["payload"] == {
        "grant": {"type": "catalog", "privilege": "CATALOG_MANAGE_CONTENT"}
    }


def test_prune_revokes_extra_privilege_with_post_and_wrapper(tmp_path):
    role_path = "/api/management/v1/catalogs/lakehouse/catalog-roles/spark_writer_catalog_role"
    client = FakePolarisClient({
        ("GET", role_path): (200, {}),
        ("GET", role_path + "/grants"): (200, {
            "grants": [
                {"type": "catalog", "privilege": "CATALOG_MANAGE_CONTENT"},
                {"type": "catalog", "privilege": "CATALOG_MANAGE_ACCESS"},
            ]
        }),
    })
    config = {
        "catalog": {"name": "lakehouse"},
        "prune_unmanaged_privileges": True,
        "catalog_roles": {
            "spark_writer_catalog_role": {
                "grants": [{"type": "catalog", "privilege": "CATALOG_MANAGE_CONTENT"}]
            }
        },
    }
    reconciler = rbac.PolarisRbacReconciler(
        client, config, state_file=tmp_path / "state.env"
    )
    reconciler.reconcile_catalog_roles()

    revoke = next(
        call for call in client.calls
        if call["method"] == "POST" and call["path"] == role_path + "/grants"
    )
    assert revoke["payload"] == {
        "grant": {"type": "catalog", "privilege": "CATALOG_MANAGE_ACCESS"}
    }


def test_prune_revokes_privilege_absent_from_old_top_level_set(tmp_path):
    """Regression guard: CATALOG_WRITE_PROPERTIES is only covered by the completed TOP_LEVEL_PRIVILEGES set."""
    role_path = "/api/management/v1/catalogs/lakehouse/catalog-roles/spark_writer_catalog_role"
    client = FakePolarisClient({
        ("GET", role_path): (200, {}),
        ("GET", role_path + "/grants"): (200, {
            "grants": [
                {"type": "catalog", "privilege": "CATALOG_MANAGE_CONTENT"},
                {"type": "catalog", "privilege": "CATALOG_WRITE_PROPERTIES"},
            ]
        }),
    })
    config = {
        "catalog": {"name": "lakehouse"},
        "prune_unmanaged_privileges": True,
        "catalog_roles": {
            "spark_writer_catalog_role": {
                "grants": [{"type": "catalog", "privilege": "CATALOG_MANAGE_CONTENT"}]
            }
        },
    }
    reconciler = rbac.PolarisRbacReconciler(
        client, config, state_file=tmp_path / "state.env"
    )
    reconciler.reconcile_catalog_roles()

    revoke = next(
        call for call in client.calls
        if call["method"] == "POST" and call["path"] == role_path + "/grants"
    )
    assert revoke["payload"] == {
        "grant": {"type": "catalog", "privilege": "CATALOG_WRITE_PROPERTIES"}
    }


def test_purge_keeps_system_roles_and_removes_unmanaged_roles(tmp_path):
    client = FakePolarisClient({
        ("GET", "/api/management/v1/principal-roles"): (200, {
            "roles": [
                {"name": "keep_principal_role"},
                {"name": "stale_principal_role"},
                {"name": "service_admin"},
            ]
        }),
        ("GET", "/api/management/v1/catalogs/lakehouse/catalog-roles"): (200, {
            "roles": [
                {"name": "keep_catalog_role"},
                {"name": "stale_catalog_role"},
                {"name": "catalog_admin"},
            ]
        }),
    })
    config = {
        "catalog": {"name": "lakehouse"},
        "purge_unmanaged_roles": True,
        "principal_roles": {"keep_principal_role": {}},
        "catalog_roles": {"keep_catalog_role": {}},
    }
    reconciler = rbac.PolarisRbacReconciler(
        client, config, state_file=tmp_path / "state.env"
    )
    reconciler.purge_unmanaged_entities()

    deleted = {
        (call["method"], call["path"])
        for call in client.calls
        if call["method"] == "DELETE"
    }
    assert deleted == {
        ("DELETE", "/api/management/v1/principal-roles/stale_principal_role"),
        ("DELETE", "/api/management/v1/catalogs/lakehouse/catalog-roles/stale_catalog_role"),
    }
