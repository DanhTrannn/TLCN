from pathlib import Path

import pytest

from lakehouse.config import (
    APPEND_ONLY_TABLES,
    APPEND_ONLY_CURSOR,
    EXPECTED_CURSOR,
    KNOWN_TABLES,
    MUTABLE_CURSOR,
    SILVER_PREFIX,
    ConfigError,
    load_config,
)

CONFIG_FILE = Path(__file__).resolve().parents[1] / "config" / "default.yml"


@pytest.fixture(scope="module")
def config():
    return load_config(CONFIG_FILE)


def test_catalogue_coverage(config):
    names = {table.name for table in config.tables}
    assert names == KNOWN_TABLES


def test_no_customer_credentials_in_catalogue(config):
    names = {table.name for table in config.tables}
    assert "customer_credentials" not in names


def test_mutability_matches_contract(config):
    for table in config.tables:
        if table.name in APPEND_ONLY_TABLES:
            assert table.mutability == "append_only"
            assert table.cursor_field == APPEND_ONLY_CURSOR
        else:
            assert table.mutability == "mutable"
            assert table.cursor_field == MUTABLE_CURSOR


def test_silver_names_prefixed_and_unique(config):
    silver_names = [table.silver_table for table in config.tables]
    assert all(name.startswith(SILVER_PREFIX) for name in silver_names)
    assert len(silver_names) == len(set(silver_names))


def test_every_table_has_pk(config):
    for table in config.tables:
        assert table.pk


def test_pseudonymize_only_customers(config):
    for table in config.tables:
        if table.name == "customers":
            assert table.pseudonymize == ("email_normalized", "phone", "full_name")
        else:
            assert table.pseudonymize == ()


def test_table_lookup(config):
    orders = config.table("orders")
    assert orders is not None
    assert orders.pk == "order_id"
    assert config.table("does_not_exist") is None


def test_round_trip_run_and_landing(config):
    assert config.run.data_interval_minutes == 15
    assert config.run.retries == 2
    assert config.landing.oltp_prefix == "landing/oltp"
    assert config.landing.manifest_version == "1.0.0"


def _write(tmp_path, yaml_text):
    path = tmp_path / "config.yml"
    path.write_text(yaml_text, encoding="utf-8")
    return path


VALID_BLOCK = """
run:
  data_interval_minutes: 15
  retries: 2
  quarantine_max_rows: 100000
landing:
  oltp_prefix: landing/oltp
  log_prefix: landing/logs
  manifest_version: "1.0.0"
tables:
"""


def _tables_yaml(*entries):
    return "\n".join(f"  - {entry}" for entry in entries)


def _valid_table(name, cursor, pk, mutability, silver):
    return (
        f"name: {name}\n"
        f"    cursor_field: {cursor}\n"
        f"    pk: {pk}\n"
        f"    mutability: {mutability}\n"
        f"    silver_table: {silver}"
    )


def test_missing_table_raises(tmp_path):
    entries = [
        _valid_table(name, EXPECTED_CURSOR[name], "pk_x", "mutable" if name not in APPEND_ONLY_TABLES else "append_only", f"silver_{name}")
        for name in sorted(KNOWN_TABLES - {"orders"})
    ]
    path = _write(tmp_path, VALID_BLOCK + _tables_yaml(*entries))
    with pytest.raises(ConfigError, match="thiếu"):
        load_config(path)


def test_unknown_table_raises(tmp_path):
    entries = [
        _valid_table(name, EXPECTED_CURSOR[name], "pk_x", "mutable" if name not in APPEND_ONLY_TABLES else "append_only", f"silver_{name}")
        for name in sorted(KNOWN_TABLES)
    ] + [_valid_table("secret_table", "updated_at", "id", "mutable", "silver_secret")]
    path = _write(tmp_path, VALID_BLOCK + _tables_yaml(*entries))
    with pytest.raises(ConfigError, match="unknown table"):
        load_config(path)


def test_wrong_cursor_raises(tmp_path):
    entries = [
        _valid_table(name, EXPECTED_CURSOR[name], "pk_x", "mutable" if name not in APPEND_ONLY_TABLES else "append_only", f"silver_{name}")
        for name in sorted(KNOWN_TABLES)
    ]
    entries[0] = entries[0].replace(EXPECTED_CURSOR[sorted(KNOWN_TABLES)[0]], "created_at" if EXPECTED_CURSOR[sorted(KNOWN_TABLES)[0]] == "updated_at" else "updated_at")
    path = _write(tmp_path, VALID_BLOCK + _tables_yaml(*entries))
    with pytest.raises(ConfigError, match="cursor_field"):
        load_config(path)


def test_missing_pk_raises(tmp_path):
    entries = [
        _valid_table(name, EXPECTED_CURSOR[name], "pk_x", "mutable" if name not in APPEND_ONLY_TABLES else "append_only", f"silver_{name}")
        for name in sorted(KNOWN_TABLES)
    ]
    entries[0] = entries[0].replace("pk: pk_x", "pk: ''")
    path = _write(tmp_path, VALID_BLOCK + _tables_yaml(*entries))
    with pytest.raises(ConfigError, match="pk"):
        load_config(path)


def test_bad_silver_prefix_raises(tmp_path):
    entries = [
        _valid_table(name, EXPECTED_CURSOR[name], "pk_x", "mutable" if name not in APPEND_ONLY_TABLES else "append_only", "gold_" + name)
        for name in sorted(KNOWN_TABLES)
    ]
    path = _write(tmp_path, VALID_BLOCK + _tables_yaml(*entries))
    with pytest.raises(ConfigError, match="silver_table"):
        load_config(path)


def test_missing_file_raises(tmp_path):
    with pytest.raises(ConfigError, match="not found"):
        load_config(tmp_path / "nope.yml")
