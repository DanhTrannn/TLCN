import shutil

import pytest

pyspark = pytest.importorskip("pyspark", reason="pyspark not installed")
pytestmark = pytest.mark.skipif(
    shutil.which("java") is None,
    reason="Java not found — Spark tests require a JDK",
)

from pyspark.sql import SparkSession  # noqa: E402
from lakehouse.oltp.bronze import ingest_to_bronze  # noqa: E402


@pytest.fixture(scope="session")
def spark():
    return SparkSession.builder.master("local[1]").appName("test-bronze").getOrCreate()


def test_ingest_to_bronze_ok(spark, tmp_path):
    source_dir = tmp_path / "landing"
    source_dir.mkdir()
    (source_dir / "data.json").write_text('{"id": 1, "name": "A"}\n{"id": 2, "name": "B"}\n')

    target_dir = tmp_path / "target"
    quarantine_dir = tmp_path / "quarantine"

    ingest_to_bronze(
        spark=spark,
        run_id="run-123",
        source_path=str(source_dir),
        source_format="json",
        target_table=str(target_dir),
        quarantine_table=str(quarantine_dir),
        error_threshold=0.01,
        _write_format="parquet",
    )

    df = spark.read.parquet(str(target_dir))
    assert df.count() == 2
    assert "_run_id" in df.columns
    assert "_source_file" in df.columns
    assert "_ingested_at_utc" in df.columns


def test_ingest_to_bronze_threshold_exceeded(spark, tmp_path):
    source_dir = tmp_path / "landing"
    source_dir.mkdir()
    (source_dir / "corrupted.json").write_text('{"id": 1, "name": "A"}\n{"id": 2, "name": BAD_JSON\n')

    target_dir = tmp_path / "target"
    quarantine_dir = tmp_path / "quarantine"

    with pytest.raises(RuntimeError, match="Error threshold exceeded"):
        ingest_to_bronze(
            spark=spark,
            run_id="run-123",
            source_path=str(source_dir),
            source_format="json",
            target_table=str(target_dir),
            quarantine_table=str(quarantine_dir),
            error_threshold=0.01,
            _write_format="parquet",
        )


def test_ingest_to_bronze_quarantine_within_threshold(spark, tmp_path):
    source_dir = tmp_path / "landing"
    source_dir.mkdir()
    (source_dir / "corrupted.json").write_text('{"id": 1, "name": "A"}\n{"id": 2, "name": BAD_JSON\n')

    target_dir = tmp_path / "target"
    quarantine_dir = tmp_path / "quarantine"

    ingest_to_bronze(
        spark=spark,
        run_id="run-123",
        source_path=str(source_dir),
        source_format="json",
        target_table=str(target_dir),
        quarantine_table=str(quarantine_dir),
        error_threshold=0.6,
        _write_format="parquet",
    )

    valid_df = spark.read.parquet(str(target_dir))
    assert valid_df.count() == 1
    assert "_run_id" in valid_df.columns

    quarantine_df = spark.read.parquet(str(quarantine_dir))
    assert quarantine_df.count() == 1
    assert "_corrupt_record" in quarantine_df.columns
