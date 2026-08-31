import json
from pathlib import Path

from lakehouse.logs.bronze import (
    BRONZE_EVENTS_DDL,
    BRONZE_EVENTS_TABLE,
    BRONZE_QUARANTINE_DDL,
    BRONZE_QUARANTINE_TABLE,
    OTEL_LOG_SCHEMA,
    SOURCE_SYSTEM,
)


def test_constants_and_table_names():
    assert BRONZE_EVENTS_TABLE == "lakehouse.bronze.web_events"
    assert BRONZE_QUARANTINE_TABLE == "lakehouse.quarantine.bronze_corrupt_logs"
    assert SOURCE_SYSTEM == "ecommerce-api-access-log"


def test_bronze_events_ddl_structure():
    assert "CREATE TABLE IF NOT EXISTS lakehouse.bronze.web_events" in BRONZE_EVENTS_DDL
    assert "PARTITIONED BY (days(event_ts))" in BRONZE_EVENTS_DDL
    assert "event_id            STRING" in BRONZE_EVENTS_DDL
    assert "event_ts            TIMESTAMP" in BRONZE_EVENTS_DDL
    assert "observed_timestamp  TIMESTAMP" in BRONZE_EVENTS_DDL
    assert "_run_id             STRING" in BRONZE_EVENTS_DDL
    assert "_source_system      STRING" in BRONZE_EVENTS_DDL
    assert "_source_file        STRING" in BRONZE_EVENTS_DDL
    assert "_ingested_at        TIMESTAMP" in BRONZE_EVENTS_DDL


def test_bronze_quarantine_ddl_structure():
    assert "CREATE TABLE IF NOT EXISTS lakehouse.quarantine.bronze_corrupt_logs" in BRONZE_QUARANTINE_DDL
    assert "PARTITIONED BY (days(_quarantined_at))" in BRONZE_QUARANTINE_DDL
    assert "raw_corrupt_record    STRING" in BRONZE_QUARANTINE_DDL
    assert "error_message         STRING" in BRONZE_QUARANTINE_DDL
    assert "quarantine_stage      STRING" in BRONZE_QUARANTINE_DDL
    assert "_run_id               STRING" in BRONZE_QUARANTINE_DDL
    assert "_source_system        STRING" in BRONZE_QUARANTINE_DDL
    assert "_source_file          STRING" in BRONZE_QUARANTINE_DDL
    assert "_quarantined_at       TIMESTAMP" in BRONZE_QUARANTINE_DDL


def test_otel_schema_when_pyspark_present():
    if OTEL_LOG_SCHEMA is not None:
        top_level_fields = [f.name for f in OTEL_LOG_SCHEMA.fields]
        assert "schema" in top_level_fields
        assert "timestamp" in top_level_fields
        assert "observed_timestamp" in top_level_fields
        assert "request" in top_level_fields
        assert "event" in top_level_fields
        assert "http" in top_level_fields
        assert "actor" in top_level_fields
        assert "ecommerce" in top_level_fields
        assert "error" in top_level_fields
        assert "_corrupt_record" in top_level_fields


def test_contract_schema_json_file_exists():
    contract_path = Path(__file__).parent.parent.parent / "docs/contracts/ecommerce-access-v1.schema.json"
    assert contract_path.is_file()
    contract = json.loads(contract_path.read_text())
    assert contract["title"] == "D&K ecommerce completed HTTP request"
    assert "properties" in contract
