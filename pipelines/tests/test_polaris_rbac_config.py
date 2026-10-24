from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
RBAC = ROOT / "infrastructure/polaris/rbac.yml"


def _config():
    return yaml.safe_load(RBAC.read_text(encoding="utf-8"))


def test_prune_flags_are_enabled():
    config = _config()
    assert config["purge_unmanaged_principals"] is True
    assert config["purge_unmanaged_roles"] is True
    assert config["prune_unmanaged_privileges"] is True


def test_reader_has_only_narrow_read_privileges():
    config = _config()
    privileges = {
        grant["privilege"]
        for grant in config["catalog_roles"]["trino_reader_catalog_role"]["grants"]
    }
    assert privileges == {
        "CATALOG_READ_PROPERTIES",
        "NAMESPACE_LIST",
        "NAMESPACE_READ_PROPERTIES",
        "TABLE_LIST",
        "TABLE_READ_PROPERTIES",
        "TABLE_READ_DATA",
        "VIEW_LIST",
        "VIEW_READ_PROPERTIES",
    }
    assert "TABLE_FULL_METADATA" not in privileges
    assert "NAMESPACE_FULL_METADATA" not in privileges


def test_flink_has_its_own_role():
    config = _config()
    assert "flink_writer_catalog_role" in config["catalog_roles"]
    assert "flink_writer_role" in config["principal_roles"]
    assert config["principals"]["flink_writer"]["principal_roles"] == ["flink_writer_role"]


def test_credential_outputs_match_verified_owners():
    config = _config()
    outputs = {
        (item["principal"], item["directory"], item["uid"], item["gid"])
        for item in config["credential_outputs"]
    }
    assert outputs == {
        ("spark_writer", "/run/polaris-output/spark-client", 185, 185),
        ("spark_writer", "/run/polaris-output/spark-airflow", 50000, 0),
        ("flink_writer", "/run/polaris-output/flink", 9999, 9999),
        ("trino_reader", "/run/polaris-output/trino-reader", 1000, 1000),
        ("trino_admin", "/run/polaris-output/trino-admin", 1000, 1000),
    }
