import json
import os
import subprocess
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INIT = ROOT / "infrastructure/minio/init.sh"

EXPECTED = (
    "lakehouse-polaris",
    "lakehouse-spark",
    "lakehouse-flink",
    "lakehouse-airflow",
    "lakehouse-trino",
    "lakehouse-trino-admin",
    "lakehouse-uploader",
)

FAKE_MC = """
#!/usr/bin/env python3
import json
import os
import sys

args = sys.argv[1:]
state_path = os.environ["MC_STATE"]
log_path = os.environ["MC_LOG"]

with open(log_path, "a", encoding="utf-8") as log:
    log.write(" ".join(args) + "\\n")


def load():
    with open(state_path, encoding="utf-8") as handle:
        return json.load(handle)


def save(state):
    with open(state_path, "w", encoding="utf-8") as handle:
        json.dump(state, handle)


state = load()
state.setdefault("users", {})
state.setdefault("policies", [])
state.setdefault("info_calls", 0)
state.setdefault("user_info_calls", {})


def fail(message, code=1):
    print("mc: <ERROR> " + message, file=sys.stderr)
    save(state)
    sys.exit(code)


def emit(payload):
    print(json.dumps(payload, separators=(",", ":")))


if args[:2] == ["alias", "set"]:
    if "--api" not in args or args[args.index("--api") + 1] != "S3v4":
        fail("alias set must pass --api S3v4")
    save(state)
    sys.exit(0)

if args[:3] == ["admin", "info", "local"]:
    state["info_calls"] += 1
    save(state)
    if state["info_calls"] <= int(os.environ.get("MC_FAIL_INFO_ATTEMPTS", "0")):
        sys.exit(1)
    sys.exit(0)

if args[:3] == ["admin", "user", "list"]:
    for user in state["users"]:
        emit({"status": "success", "accessKey": user, "userStatus": "enabled"})
    save(state)
    sys.exit(0)

if args[:3] == ["admin", "policy", "list"]:
    for policy in state["policies"]:
        emit({"status": "success", "policy": policy, "policyInfo": {}})
    save(state)
    sys.exit(0)

if args[:3] == ["admin", "user", "add"]:
    key, secret = args[4], args[5]
    if len(secret) < 8:
        fail("secret must be at least 8 characters")
    state["users"][key] = state["users"].get(key, "")
    save(state)
    sys.exit(0)

if args[:3] == ["admin", "user", "remove"]:
    state["users"].pop(args[4], None)
    save(state)
    sys.exit(0)

if args[:3] == ["admin", "policy", "create"]:
    name = args[4]
    if name.startswith("lakehouse-preflight-") and os.environ.get("MC_FAIL_PREFLIGHT") == "1":
        fail("simulated policy validation failure for " + name)
    if name not in state["policies"]:
        state["policies"].append(name)
    save(state)
    sys.exit(0)

if args[:3] == ["admin", "policy", "info"]:
    if args[4] not in state["policies"]:
        fail("policy " + args[4] + " not found")
    save(state)
    sys.exit(0)

if args[:3] == ["admin", "policy", "remove"]:
    name = args[4]
    if name not in state["policies"]:
        fail("policy " + name + " not found")
    state["policies"].remove(name)
    save(state)
    sys.exit(0)

if args[:3] == ["admin", "policy", "attach"]:
    policy = args[4]
    user = args[args.index("--user") + 1]
    state["users"][user] = policy
    save(state)
    sys.exit(0)

if args[:3] == ["admin", "user", "info"]:
    key = args[4]
    if key not in state["users"]:
        fail("user " + key + " not found")
    calls = state["user_info_calls"].get(key, 0) + 1
    state["user_info_calls"][key] = calls
    attached = state["users"].get(key, "")
    if os.environ.get("MC_WRONG_POLICY_USER") == key:
        attached = "lakehouse-wrong"
    if os.environ.get("MC_WRONG_POLICY_SECOND_CALL") == key and calls >= 2:
        attached = "lakehouse-wrong"
    emit({"status": "success", "accessKey": key, "policyName": attached})
    save(state)
    sys.exit(0)

if args[0] == "mb" or args[:2] == ["anonymous", "set"]:
    save(state)
    sys.exit(0)

fail("unexpected fake mc invocation: " + " ".join(args))
"""


def setup(tmp_path, **overrides):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    mc_path = bin_dir / "mc"
    mc_path.write_text(textwrap.dedent(FAKE_MC).lstrip("\n"), encoding="utf-8")
    mc_path.chmod(0o755)
    sleep_path = bin_dir / "sleep"
    sleep_path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    sleep_path.chmod(0o755)

    policy_dir = tmp_path / "policies"
    policy_dir.mkdir()
    policy_body = json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": ["s3:GetObject"],
                    "Resource": ["arn:aws:s3:::__MINIO_BUCKET__/*"],
                }
            ],
        }
    )
    for policy in EXPECTED:
        (policy_dir / f"{policy}.json").write_text(policy_body, encoding="utf-8")

    state = tmp_path / "mc-state.json"
    state.write_text(
        json.dumps(
            {"users": {}, "policies": [], "info_calls": 0, "user_info_calls": {}}
        ),
        encoding="utf-8",
    )
    log = tmp_path / "mc.log"

    env = dict(os.environ)
    env.update(
        {
            "PATH": f"{bin_dir}{os.pathsep}{env['PATH']}",
            "MC_STATE": str(state),
            "MC_LOG": str(log),
            "POLICY_DIR": str(policy_dir),
            "POLICY_TMP": str(tmp_path / "rendered-policies"),
            "MINIO_ENDPOINT": "http://minio:9000",
            "MINIO_ROOT_USER": "rootuser",
            "MINIO_ROOT_PASSWORD": "rootpassword",
            "MINIO_LAKEHOUSE_BUCKET": "lakehouse",
            "MINIO_POLARIS_ACCESS_KEY": "lakehouse-polaris",
            "MINIO_POLARIS_SECRET_KEY": "polaris-secret",
            "MINIO_SPARK_ACCESS_KEY": "lakehouse-spark",
            "MINIO_SPARK_SECRET_KEY": "spark-secret",
            "MINIO_FLINK_ACCESS_KEY": "lakehouse-flink",
            "MINIO_FLINK_SECRET_KEY": "flink-secret",
            "MINIO_AIRFLOW_ACCESS_KEY": "lakehouse-airflow",
            "MINIO_AIRFLOW_SECRET_KEY": "airflow-secret",
            "MINIO_TRINO_ACCESS_KEY": "lakehouse-trino",
            "MINIO_TRINO_SECRET_KEY": "trino-secret",
            "MINIO_TRINO_ADMIN_ACCESS_KEY": "lakehouse-trino-admin",
            "MINIO_TRINO_ADMIN_SECRET_KEY": "trino-admin-secret",
            "MINIO_UPLOADER_ACCESS_KEY": "lakehouse-uploader",
            "MINIO_UPLOADER_SECRET_KEY": "uploader-secret",
        }
    )
    env.update(overrides)
    return env, state, log


def run_init(env):
    return subprocess.run(
        ["sh", str(INIT)], env=env, capture_output=True, text=True
    )


def log_lines(log):
    if not log.exists():
        return []
    return log.read_text(encoding="utf-8").splitlines()


def test_init_script_has_valid_shell_syntax():
    result = subprocess.run(["sh", "-n", str(INIT)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_init_script_manages_every_service_identity():
    text = INIT.read_text(encoding="utf-8")
    for user in EXPECTED:
        assert user in text
    for policy in EXPECTED:
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


def test_alias_set_skips_probe_and_readiness_retries(tmp_path):
    env, state, log = setup(tmp_path, MC_FAIL_INFO_ATTEMPTS="2")

    result = run_init(env)

    assert result.returncode == 0, result.stderr
    lines = log_lines(log)
    alias_lines = [line for line in lines if line.startswith("alias set")]
    assert len(alias_lines) == 1
    assert "--api S3v4" in alias_lines[0]
    info_lines = [line for line in lines if line.startswith("admin info local")]
    assert len(info_lines) == 3
    assert lines.index(alias_lines[0]) < lines.index(info_lines[0])
    assert json.loads(state.read_text(encoding="utf-8"))["info_calls"] == 3


def test_empty_user_and_policy_lists_converge(tmp_path):
    env, state, log = setup(tmp_path)

    result = run_init(env)

    assert result.returncode == 0, result.stderr
    converged = json.loads(state.read_text(encoding="utf-8"))
    assert set(converged["users"]) == set(EXPECTED)
    assert set(converged["policies"]) == set(EXPECTED)
    assert all(converged["users"][user] == user for user in EXPECTED)
    lines = log_lines(log)
    assert not any(line.startswith("admin user remove") for line in lines)
    # The only policy removals are the preflight copies, before any deletion.
    removals = [line for line in lines if line.startswith("admin policy remove")]
    assert removals
    assert all("lakehouse-preflight-" in line for line in removals)


def test_wrong_managed_access_key_fails_before_mutation(tmp_path):
    env, _, log = setup(tmp_path, MINIO_UPLOADER_ACCESS_KEY="lakehouse-uploadr")

    result = run_init(env)

    assert result.returncode != 0
    assert "lakehouse-uploadr" in result.stderr
    assert "lakehouse-uploader" in result.stderr
    assert log_lines(log) == []


def test_short_secret_fails_before_mutation(tmp_path):
    env, _, log = setup(tmp_path, MINIO_SPARK_SECRET_KEY="short")

    result = run_init(env)

    assert result.returncode != 0
    assert "at least 8 characters" in result.stderr
    assert log_lines(log) == []


def test_policy_preflight_failure_aborts_before_deletion(tmp_path):
    env, _, log = setup(tmp_path, MC_FAIL_PREFLIGHT="1")

    result = run_init(env)

    assert result.returncode != 0
    assert "Policy preflight failed" in result.stderr
    lines = log_lines(log)
    assert not any(line.startswith("admin user remove") for line in lines)
    assert not any(line.startswith("admin policy remove") for line in lines)
    assert not any(line.startswith("admin user add") for line in lines)
    assert not any(line.startswith("mb ") for line in lines)


def test_wrong_final_policy_mapping_fails(tmp_path):
    env, _, _ = setup(tmp_path, MC_WRONG_POLICY_SECOND_CALL="lakehouse-spark")

    result = run_init(env)

    assert result.returncode != 0
    assert "found 'lakehouse-wrong'" in result.stderr
