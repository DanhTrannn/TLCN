import pytest

from lakehouse.landing import RunPaths, manifest_from_dict, validate_manifest

RUN = RunPaths(bucket="lakehouse", table="orders",
               extract_date="2026-08-15", run_id="run123")


def test_run_prefix():
    assert RUN.run_prefix() == "landing/oltp/orders/extract_date=2026-08-15/run_id=run123"


def test_manifest_key_and_data_prefix():
    assert RUN.manifest_key() == "landing/oltp/orders/extract_date=2026-08-15/run_id=run123/manifest.json"
    assert RUN.data_prefix() == "landing/oltp/orders/extract_date=2026-08-15/run_id=run123/data"


def test_manifest_from_dict_round_trip():
    raw = {
        "manifest_version": "1.0.0", "run_id": "run123", "table": "orders",
        "source": {"system": "mysql_ecommerce", "schema": "ecommerce"},
        "cursor": {"field": "updated_at", "committed_at": "2026-08-15T09:00:00",
                   "committed_pk": 1, "high_watermark_at": "2026-08-15T10:00:00",
                   "high_watermark_pk": 5, "min_at": "2026-08-15T09:01:00",
                   "max_at": "2026-08-15T10:00:00"},
        "rows": 4, "empty": False,
        "files": [{"path": "s3://x/data/p1.parquet", "rows": 2, "md5": "a"},
                  {"path": "s3://x/data/p2.parquet", "rows": 2, "md5": "b"}],
        "generated_at_utc": "2026-08-15T10:05:00Z",
    }
    manifest = manifest_from_dict(raw)
    assert manifest.rows == 4
    assert manifest.files[1].md5 == "b"
    assert manifest.cursor_field == "updated_at"


def test_manifest_from_dict_missing_required_key_raises():
    with pytest.raises(ValueError, match="source"):
        manifest_from_dict({"run_id": "r"})


def test_validate_manifest_ok():
    raw = {
        "manifest_version": "1.0.0", "run_id": "run123", "table": "orders",
        "source": {"system": "mysql_ecommerce", "schema": "ecommerce"},
        "cursor": {"field": "updated_at", "committed_at": "2026-08-15T09:00:00",
                   "committed_pk": 1, "high_watermark_at": "2026-08-15T10:00:00",
                   "high_watermark_pk": 5, "min_at": "2026-08-15T09:01:00",
                   "max_at": "2026-08-15T10:00:00"},
        "rows": 4, "empty": False,
        "files": [{"path": "p1", "rows": 2, "md5": "a"},
                  {"path": "p2", "rows": 2, "md5": "b"}],
        "generated_at_utc": "2026-08-15T10:05:00Z",
    }
    manifest = manifest_from_dict(raw)
    stats = {"p1": (100, 2), "p2": (100, 2)}
    assert validate_manifest(manifest, lambda p: stats.get(p)) == []


def test_validate_manifest_row_mismatch_reported():
    raw = {
        "manifest_version": "1.0.0", "run_id": "run123", "table": "orders",
        "source": {"system": "mysql_ecommerce", "schema": "ecommerce"},
        "cursor": {"field": "updated_at", "committed_at": None, "committed_pk": None,
                   "high_watermark_at": "2026-08-15T10:00:00", "high_watermark_pk": 5,
                   "min_at": None, "max_at": None},
        "rows": 4, "empty": False,
        "files": [{"path": "p1", "rows": 2, "md5": "a"}],
        "generated_at_utc": "2026-08-15T10:05:00Z",
    }
    manifest = manifest_from_dict(raw)
    stats = {"p1": (100, 1)}
    violations = validate_manifest(manifest, lambda p: stats.get(p))
    assert any("p1" in v and "row" in v for v in violations)
    assert any("rows" in v for v in violations)


def test_validate_manifest_missing_file_reported():
    raw = {
        "manifest_version": "1.0.0", "run_id": "run123", "table": "orders",
        "source": {"system": "mysql_ecommerce", "schema": "ecommerce"},
        "cursor": {"field": "updated_at", "committed_at": None, "committed_pk": None,
                   "high_watermark_at": "2026-08-15T10:00:00", "high_watermark_pk": 5,
                   "min_at": None, "max_at": None},
        "rows": 2, "empty": False,
        "files": [{"path": "p1", "rows": 2, "md5": "a"}],
        "generated_at_utc": "2026-08-15T10:05:00Z",
    }
    manifest = manifest_from_dict(raw)
    violations = validate_manifest(manifest, lambda p: None)
    assert any("missing" in v for v in violations)


def test_validate_manifest_empty_requires_no_files():
    raw = {
        "manifest_version": "1.0.0", "run_id": "run123", "table": "orders",
        "source": {"system": "mysql_ecommerce", "schema": "ecommerce"},
        "cursor": {"field": "updated_at", "committed_at": "2026-08-15T09:00:00",
                   "committed_pk": 1, "high_watermark_at": "2026-08-15T10:00:00",
                   "high_watermark_pk": 5, "min_at": None, "max_at": None},
        "rows": 0, "empty": True, "files": [],
        "generated_at_utc": "2026-08-15T10:05:00Z",
    }
    manifest = manifest_from_dict(raw)
    assert validate_manifest(manifest, lambda p: None) == []


def test_validate_manifest_cursor_range_ok_skipped_when_committed_null():
    raw = {
        "manifest_version": "1.0.0", "run_id": "run123", "table": "orders",
        "source": {"system": "mysql_ecommerce", "schema": "ecommerce"},
        "cursor": {"field": "updated_at", "committed_at": None, "committed_pk": None,
                   "high_watermark_at": "2026-08-15T10:00:00", "high_watermark_pk": 5,
                   "min_at": "2026-08-15T09:01:00", "max_at": "2026-08-15T10:00:00"},
        "rows": 2, "empty": False,
        "files": [{"path": "p1", "rows": 2, "md5": "a"}],
        "generated_at_utc": "2026-08-15T10:05:00Z",
    }
    manifest = manifest_from_dict(raw)
    assert validate_manifest(manifest, lambda p: (100, 2)) == []