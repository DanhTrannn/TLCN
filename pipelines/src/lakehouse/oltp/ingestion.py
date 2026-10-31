"""Batch orchestration: manifests select input; failures propagate to the scheduler."""

import hashlib
import logging

from lakehouse.landing import FileStats, RunPaths, manifest_from_dict, validate_manifest
from lakehouse.oltp.bronze import ingest_to_bronze
from lakehouse.oltp.silver import merge_oltp_table
from lakehouse.oltp.silver_ddl import ensure_silver_tables
from lakehouse.oltp.storage import read_json, write_json

log = logging.getLogger(__name__)


def read_run_manifest(spark, paths: RunPaths):
    manifest = manifest_from_dict(read_json(spark, f"s3a://{paths.bucket}/{paths.manifest_key()}"))
    if manifest.table != paths.table or manifest.run_id != paths.run_id:
        raise ValueError("Landing manifest table/run identity mismatch")
    if any(not f.path.startswith(paths.data_prefix() + "/") or ".." in f.path.split("/") for f in manifest.files):
        raise ValueError("Landing manifest contains a file outside this run")

    def stats(key):
        uri = f"s3a://{paths.bucket}/{key}"
        data = bytes(spark.read.format("binaryFile").load(uri).first()["content"])
        return FileStats(len(data), spark.read.parquet(uri).count(), hashlib.md5(data).hexdigest())

    violations = validate_manifest(manifest, stats)
    if violations:
        raise ValueError(f"Invalid Landing manifest: {violations}")
    return manifest


def ingest_bronze_tables(spark, cfg, run_id, extract_date, tables=None, error_threshold=0.01):
    for name in tables or [table.name for table in cfg.tables]:
        if cfg.table(name) is None:
            raise ValueError(f"Unknown source table: {name}")
        paths = RunPaths(cfg.bucket, name, extract_date, run_id)
        manifest = read_run_manifest(spark, paths)
        if not manifest.empty:
            ingest_to_bronze(
                spark,
                run_id,
                [f"s3a://{cfg.bucket}/{f.path}" for f in manifest.files],
                "parquet",
                f"lakehouse.bronze.{name}",
                f"lakehouse.quarantine.{name}_errors",
                error_threshold,
            )
        # Written only after all data for this table is safely committed, including
        # verified empty runs. Cursor publication checks this marker against the watermark.
        write_json(
            spark,
            f"s3a://{cfg.bucket}/{paths.run_prefix()}/bronze_complete.json",
            {
                "run_id": run_id,
                "table": name,
                "rows": manifest.rows,
                "high_watermark_at": manifest.high_watermark_at,
                "high_watermark_pk": manifest.high_watermark_pk,
            },
        )
        log.info("Bronze complete: table=%s run=%s rows=%s", name, run_id, manifest.rows)


def ingest_silver_tables(spark, cfg, run_id, bronze_date):
    ensure_silver_tables(spark)
    for table in cfg.tables:
        source = f"lakehouse.bronze.{table.name}"
        if not spark.catalog.tableExists(source):
            paths = RunPaths(cfg.bucket, table.name, bronze_date, run_id)
            manifest = read_run_manifest(spark, paths)
            if manifest.empty and manifest.high_watermark_at is None:
                continue  # first-ever extract of a genuinely empty source table
            raise RuntimeError(f"Required Bronze table is missing: {source}")
        bronze_df = spark.read.format("iceberg").load(source)
        result = merge_oltp_table(spark, table, bronze_df, run_id, f"lakehouse.silver.{table.silver_table}")
        log.info("Silver complete: table=%s run=%s result=%s", table.name, run_id, result)
