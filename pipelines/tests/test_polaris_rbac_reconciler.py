"""Tests for the Polaris RBAC reconciler in infrastructure/polaris/sync_polaris_rbac.py."""

import importlib.util
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


def make_reconciler(client, config, tmp_path):
    # Temporary Task 1 compatibility helper. Task 2 makes `state_file` keyword-only.
    try:
        return rbac.PolarisRbacReconciler(client, config, state_file=tmp_path / "state.env")
    except TypeError:
        return rbac.PolarisRbacReconciler(client, config, tmp_path / "state.env")


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
    reconciler = make_reconciler(client, config, tmp_path)
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
    reconciler = make_reconciler(client, config, tmp_path)
    reconciler.reconcile_catalog_roles()

    revoke = next(
        call for call in client.calls
        if call["method"] == "POST" and call["path"] == role_path + "/grants"
    )
    assert revoke["payload"] == {
        "grant": {"type": "catalog", "privilege": "CATALOG_MANAGE_ACCESS"}
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
    reconciler = make_reconciler(client, config, tmp_path)
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
