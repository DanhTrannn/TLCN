import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
POLICIES = ROOT / "infrastructure/minio/policies"
BUCKET_ARN = "arn:aws:s3:::__MINIO_BUCKET__"

EXPECTED_POLICIES = {
    "lakehouse-polaris",
    "lakehouse-spark",
    "lakehouse-flink",
    "lakehouse-airflow",
    "lakehouse-trino",
    "lakehouse-trino-admin",
    "lakehouse-uploader",
}

READ_WRITE = {
    "s3:GetObject",
    "s3:PutObject",
    "s3:DeleteObject",
    "s3:AbortMultipartUpload",
    "s3:ListMultipartUploadParts",
}

WRITE_ACTIONS = {
    "s3:PutObject",
    "s3:DeleteObject",
    "s3:AbortMultipartUpload",
    "s3:ListMultipartUploadParts",
}


def _policy(name):
    return json.loads((POLICIES / f"{name}.json").read_text(encoding="utf-8"))


def _statements(policy):
    return policy["Statement"]


def _statement_actions(statement):
    action = statement["Action"]
    return set(action if isinstance(action, list) else [action])


def _statement_resources(statement):
    resource = statement["Resource"]
    return resource if isinstance(resource, list) else [resource]


def _actions(policy):
    return {action for statement in _statements(policy) for action in _statement_actions(statement)}


def _resources(policy):
    return {resource for statement in _statements(policy) for resource in _statement_resources(statement)}


def _object_resources(policy):
    return {resource for resource in _resources(policy) if resource != BUCKET_ARN}


def test_all_policies_are_valid_json_with_bucket_placeholder():
    assert {path.stem for path in POLICIES.glob("*.json")} == EXPECTED_POLICIES
    for name in EXPECTED_POLICIES:
        policy = _policy(name)
        assert policy["Version"] == "2012-10-17"
        assert "__MINIO_BUCKET__" in " ".join(_resources(policy))


def test_no_policy_grants_multipart_upload_listing():
    for name in EXPECTED_POLICIES:
        actions = _actions(_policy(name))
        assert "s3:ListBucketMultipartUploads" not in actions, name


def test_s3_prefix_condition_is_only_used_on_list_bucket():
    for name in EXPECTED_POLICIES:
        policy = _policy(name)
        for statement in _statements(policy):
            condition = statement.get("Condition")
            if condition is None:
                continue
            assert _statement_actions(statement) == {"s3:ListBucket"}, (
                f"{name}: s3:prefix condition attached to {sorted(_statement_actions(statement))}"
            )
            assert set(condition) == {"StringLike"}, name
            assert set(condition["StringLike"]) == {"s3:prefix"}, name
        list_bucket = [
            statement
            for statement in _statements(policy)
            if "s3:ListBucket" in _statement_actions(statement)
        ]
        assert list_bucket, name
        for statement in list_bucket:
            prefixes = statement["Condition"]["StringLike"]["s3:prefix"]
            assert prefixes, name
            assert all(prefix.endswith("/*") for prefix in prefixes), name


def test_bucket_prefix_conditions_are_scoped_to_service_prefixes():
    expected = {
        "lakehouse-polaris": {"warehouse/*"},
        "lakehouse-spark": {"landing/*", "warehouse/*", "state/*"},
        "lakehouse-flink": {"warehouse/*"},
        "lakehouse-airflow": {"landing/*", "state/*"},
        "lakehouse-trino": {"warehouse/*"},
        "lakehouse-trino-admin": {"warehouse/*"},
        "lakehouse-uploader": {"landing/logs/*"},
    }
    for name, prefixes in expected.items():
        policy = _policy(name)
        list_bucket = [
            statement
            for statement in _statements(policy)
            if "s3:ListBucket" in _statement_actions(statement)
        ]
        assert len(list_bucket) == 1, name
        assert set(list_bucket[0]["Condition"]["StringLike"]["s3:prefix"]) == prefixes, name


def test_reader_policy_is_read_only():
    policy = _policy("lakehouse-trino")
    assert _actions(policy) == {"s3:GetBucketLocation", "s3:ListBucket", "s3:GetObject"}
    assert _resources(policy) == {BUCKET_ARN, f"{BUCKET_ARN}/warehouse/*"}
    for forbidden in ("s3:PutObject", "s3:DeleteObject", "s3:AbortMultipartUpload"):
        assert forbidden not in _actions(policy)


def test_flink_policy_has_no_landing_access():
    policy = _policy("lakehouse-flink")
    resources = " ".join(_resources(policy))
    assert "warehouse/*" in resources
    assert "landing/" not in resources
    assert "state/" not in resources
    assert _object_resources(policy) == {f"{BUCKET_ARN}/warehouse/*"}
    assert _actions(policy) <= {"s3:GetBucketLocation", "s3:ListBucket"} | READ_WRITE
    for statement in _statements(policy):
        statement_resources = _statement_resources(statement)
        if any(resource.startswith(f"{BUCKET_ARN}/") for resource in statement_resources):
            assert all(resource.endswith("/warehouse/*") for resource in statement_resources)


def test_airflow_policy_has_landing_and_state_but_not_warehouse():
    policy = _policy("lakehouse-airflow")
    resources = " ".join(_resources(policy))
    assert "landing/*" in resources
    assert "state/*" in resources
    assert "warehouse/" not in resources
    assert f"{BUCKET_ARN}/warehouse/*" not in _resources(policy)
    for statement in _statements(policy):
        actions = _statement_actions(statement)
        statement_resources = _statement_resources(statement)
        assert "s3:DeleteObject" not in actions
        if any("/landing/" in resource for resource in statement_resources):
            assert actions == {"s3:GetObject"}
        writes = actions & WRITE_ACTIONS
        if writes:
            assert actions == {"s3:PutObject", "s3:AbortMultipartUpload", "s3:ListMultipartUploadParts"}
            assert all(resource.endswith("/state/*") for resource in statement_resources)
    landing_statement = [
        statement
        for statement in _statements(policy)
        if any(resource.endswith("/landing/*") for resource in _statement_resources(statement))
    ]
    assert landing_statement
    assert _statement_actions(landing_statement[0]) == {"s3:GetObject"}


def test_uploader_policy_cannot_delete():
    policy = _policy("lakehouse-uploader")
    actions = _actions(policy)
    assert "s3:PutObject" in actions
    assert "s3:DeleteObject" not in actions
    assert "landing/logs/*" in " ".join(_resources(policy))
    assert _object_resources(policy) == {f"{BUCKET_ARN}/landing/logs/*"}
    for statement in _statements(policy):
        assert "s3:DeleteObject" not in _statement_actions(statement)
        statement_resources = _statement_resources(statement)
        if any(resource.startswith(f"{BUCKET_ARN}/") for resource in statement_resources):
            assert statement_resources == [f"{BUCKET_ARN}/landing/logs/*"]


def test_spark_policy_covers_landing_warehouse_and_state():
    resources = " ".join(_resources(_policy("lakehouse-spark")))
    assert "landing/*" in resources
    assert "warehouse/*" in resources
    assert "state/*" in resources
