import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FLINK_HELPERS = ROOT / "pipelines/src/lakehouse/flink.py"
CDC_JOB = ROOT / "pipelines/src/jobs/cdc/mysql_cdc_to_bronze.py"
COMPOSE_FILE = ROOT / "docker-compose.yml"
CONNECTOR_SCRIPT = ROOT / "infrastructure/debezium/register-connector.sh"


def _assignment(path: Path, name: str):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name
            for target in node.targets
        ):
            return ast.literal_eval(node.value)
    raise AssertionError(f"{name} is not defined in {path}")


def test_cdc_iceberg_table_preserves_replay_coordinates_and_images():
    ddl = "\n".join(_assignment(FLINK_HELPERS, "CDC_TABLE_DDLS"))

    assert "lakehouse.bronze.oltp_cdc_events" in ddl
    for column in (
        "operation STRING",
        "before_payload STRING",
        "after_payload STRING",
        "binlog_file STRING",
        "binlog_position BIGINT",
        "kafka_partition INT",
        "kafka_offset BIGINT",
        "raw_payload STRING",
    ):
        assert column in ddl
    assert "PARTITIONED BY (event_date)" in ddl


def test_cdc_job_handles_snapshot_changes_deletes_and_tombstones():
    insert_sql = _assignment(CDC_JOB, "CDC_INSERT_SQL")
    source = CDC_JOB.read_text(encoding="utf-8")

    assert "WHEN payload IS NULL THEN 't'" in insert_sql
    assert "JSON_VALUE(payload, '$.op')" in insert_sql
    assert "JSON_QUERY(payload, '$.before')" in insert_sql
    assert "JSON_QUERY(payload, '$.after')" in insert_sql
    assert "topic, ':', CAST(kafka_partition" in insert_sql
    assert "'scan.startup.mode' = 'group-offsets'" in source
    assert "'properties.auto.offset.reset' = 'earliest'" in source


def test_debezium_connector_is_log_based_and_scoped_to_analytical_tables():
    compose = COMPOSE_FILE.read_text(encoding="utf-8")
    connector = CONNECTOR_SCRIPT.read_text(encoding="utf-8")

    assert "--binlog-format=ROW" in compose
    assert "--binlog-row-image=FULL" in compose
    assert "lakehouse-debezium-connect:3.0.8" in compose
    assert "infrastructure/debezium/Dockerfile" in compose
    assert '"snapshot.mode": "initial"' in connector
    assert '"tombstones.on.delete": "true"' in connector
    assert "customer_credentials" not in connector
    assert "table.include.list" in connector
    assert "kafka-init:" in compose
    assert "ecommerce.access_logs" in compose
