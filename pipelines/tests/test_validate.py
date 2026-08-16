import io

import pyarrow as pa
import pyarrow.parquet as pq

from lakehouse.landing import RunPaths
from lakehouse.validate import parquet_row_count, validate_manifest_on_s3


def _make_parquet_bytes(rows: int) -> bytes:
    buf = io.BytesIO()
    pq.write_table(pa.table({"id": list(range(rows))}), buf)
    return buf.getvalue()


def test_parquet_row_count_from_footer():
    assert parquet_row_count(_make_parquet_bytes(7)) == 7


class _FakeS3:
    def __init__(self, objects: dict[str, bytes]):
        self.objects = objects

    def get_object(self, Bucket, Key):
        return {"Body": io.BytesIO(self.objects[Key]), "ContentLength": len(self.objects[Key])}


def test_validate_manifest_on_s3_ok():
    data = _make_parquet_bytes(2)
    s3 = _FakeS3({"p1.parquet": data, "p2.parquet": data})
    raw = {
        "manifest_version": "1.0.0", "run_id": "r1", "table": "orders",
        "source": {"system": "mysql_ecommerce", "schema": "ecommerce"},
        "cursor": {"field": "updated_at", "committed_at": None, "committed_pk": None,
                   "high_watermark_at": "2026-08-15T10:00:00", "high_watermark_pk": 5,
                   "min_at": None, "max_at": None},
        "rows": 4, "empty": False,
        "files": [{"path": "p1.parquet", "rows": 2, "md5": "a"},
                  {"path": "p2.parquet", "rows": 2, "md5": "b"}],
        "generated_at_utc": "2026-08-15T10:05:00Z",
    }
    s3.objects["manifest.json"] = __import__("json").dumps(raw).encode()
    paths = RunPaths(bucket="b", table="orders", extract_date="2026-08-15", run_id="r1")
    violations = validate_manifest_on_s3(
        s3, "b", paths,
        load_stats=lambda key: (
            (len(s3.objects[key]), parquet_row_count(s3.objects[key]))
            if key in s3.objects else None
        ),
    )
    assert violations == []


def test_validate_manifest_on_s3_reports_missing_and_row_mismatch():
    data = _make_parquet_bytes(2)
    s3 = _FakeS3({"p1.parquet": data})
    raw = {
        "manifest_version": "1.0.0", "run_id": "r1", "table": "orders",
        "source": {"system": "mysql_ecommerce", "schema": "ecommerce"},
        "cursor": {"field": "updated_at", "committed_at": None, "committed_pk": None,
                   "high_watermark_at": "2026-08-15T10:00:00", "high_watermark_pk": 5,
                   "min_at": None, "max_at": None},
        "rows": 4, "empty": False,
        "files": [{"path": "p1.parquet", "rows": 3, "md5": "a"},
                  {"path": "p2.parquet", "rows": 3, "md5": "b"}],
        "generated_at_utc": "2026-08-15T10:05:00Z",
    }
    s3.objects["manifest.json"] = __import__("json").dumps(raw).encode()
    paths = RunPaths(bucket="b", table="orders", extract_date="2026-08-15", run_id="r1")
    violations = validate_manifest_on_s3(
        s3, "b", paths,
        load_stats=lambda key: (
            (len(s3.objects[key]), parquet_row_count(s3.objects[key]))
            if key in s3.objects else None
        ),
    )
    assert any("missing" in v for v in violations)
    assert any("row mismatch" in v for v in violations)