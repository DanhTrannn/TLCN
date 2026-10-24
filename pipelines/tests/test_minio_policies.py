import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
POLICIES = ROOT / "infrastructure/minio/policies"

READ_WRITE = {
    "s3:GetObject",
    "s3:PutObject",
    "s3:DeleteObject",
    "s3:AbortMultipartUpload",
    "s3:ListMultipartUploadParts",
}


def _policy(name):
    return json.loads((POLICIES / f"{name}.json").read_text(encoding="utf-8"))


def _actions(policy):
    return {
        action
        for statement in policy["Statement"]
        for action in (
            statement["Action"]
            if isinstance(statement["Action"], list)
            else [statement["Action"]]
        )
    }


def _resources(policy):
    return {
        resource
        for statement in policy["Statement"]
        for resource in (
            statement["Resource"]
            if isinstance(statement["Resource"], list)
            else [statement["Resource"]]
        )
    }


def test_all_policies_are_valid_json_with_bucket_placeholder():
    expected = {
        "lakehouse-polaris",
        "lakehouse-spark",
        "lakehouse-flink",
        "lakehouse-airflow",
        "lakehouse-trino",
        "lakehouse-trino-admin",
        "lakehouse-uploader",
    }
    assert {path.stem for path in POLICIES.glob("*.json")} == expected
    for name in expected:
        policy = _policy(name)
        assert policy["Version"] == "2012-10-17"
        assert "__MINIO_BUCKET__" in " ".join(_resources(policy))


def test_reader_policy_is_read_only():
    actions = _actions(_policy("lakehouse-trino"))
    assert "s3:GetObject" in actions
    for forbidden in ("s3:PutObject", "s3:DeleteObject", "s3:AbortMultipartUpload"):
        assert forbidden not in actions


def test_flink_policy_has_no_landing_access():
    resources = " ".join(_resources(_policy("lakehouse-flink")))
    assert "warehouse/*" in resources
    assert "landing/" not in resources
    assert "state/" not in resources


def test_airflow_policy_has_landing_and_state_but_not_warehouse():
    resources = " ".join(_resources(_policy("lakehouse-airflow")))
    assert "landing/*" in resources
    assert "state/*" in resources
    assert "warehouse/" not in resources


def test_uploader_policy_cannot_delete():
    actions = _actions(_policy("lakehouse-uploader"))
    assert "s3:PutObject" in actions
    assert "s3:DeleteObject" not in actions
    assert "landing/logs/*" in " ".join(_resources(_policy("lakehouse-uploader")))


def test_spark_policy_covers_landing_warehouse_and_state():
    resources = " ".join(_resources(_policy("lakehouse-spark")))
    assert "landing/*" in resources
    assert "warehouse/*" in resources
    assert "state/*" in resources
