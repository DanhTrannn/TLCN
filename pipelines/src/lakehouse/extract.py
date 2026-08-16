import concurrent.futures
import hashlib
import json
from datetime import datetime, timezone

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, lit, max, min

from lakehouse.config import Config, TableSpec
from lakehouse.cursor import CursorState
from lakehouse.landing import MANIFEST_VERSION, RunPaths


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _hadoop_fs(spark, path: str):
    return spark._jvm.org.apache.hadoop.fs.FileSystem.get(
        spark._jvm.org.apache.hadoop.fs.Path(path).toUri(),
        spark._jsc.hadoopConfiguration(),
    )


def read_committed_cursor(spark, bucket: str, table: str) -> CursorState | None:
    path = f"s3a://{bucket}/state/cursor/{table}.json"
    fs = _hadoop_fs(spark, path)
    if not fs.exists(spark._jvm.org.apache.hadoop.fs.Path(path)):
        return None
    row = spark.read.text(path).first()
    return CursorState.from_json(row["value"])


def _write_manifest(spark, bucket: str, manifest_key: str, manifest: dict) -> None:
    fs = _hadoop_fs(spark, f"s3a://{bucket}/{manifest_key}")
    path = spark._jvm.org.apache.hadoop.fs.Path(f"s3a://{bucket}/{manifest_key}")
    fs.mkdirs(path.getParent())
    out = fs.create(path, True)
    out.write(json.dumps(manifest).encode("utf-8"))
    out.close()


def _file_stats(spark, paths: RunPaths) -> list[dict]:
    fs = _hadoop_fs(spark, f"s3a://{paths.bucket}/{paths.data_prefix()}/*.parquet")
    glob = f"s3a://{paths.bucket}/{paths.data_prefix()}/*.parquet"
    statuses = sorted(
        fs.globStatus(spark._jvm.org.apache.hadoop.fs.Path(glob)),
        key=lambda s: str(s.getPath()),
    )
    files = []
    for status in statuses:
        key = str(status.getPath()).replace(f"s3a://{paths.bucket}/", "")
        content = spark.read.format("binaryFile").load(
            f"s3a://{paths.bucket}/{key}"
        ).first()["content"]
        md5 = hashlib.md5(bytes(content)).hexdigest()
        rows = int(spark.read.parquet(f"s3a://{paths.bucket}/{key}").count())
        files.append({"path": key, "rows": rows, "md5": md5})
    return files


def extract_one_table(
    spark: SparkSession,
    cfg: Config,
    table: TableSpec,
    run_id: str,
    extract_date: str,
    high_watermark_at: str,
    high_watermark_pk: int | None,
    committed: CursorState | None,
) -> dict:
    paths = RunPaths(bucket=cfg.bucket, table=table.name,
                     extract_date=extract_date, run_id=run_id)
    now_utc = _utc_now()

    range_pred = ""
    if committed is not None:
        range_pred = (
            f" WHERE (`{table.cursor_field}` > '{committed.cursor_at}' OR "
            f"(`{table.cursor_field}` = '{committed.cursor_at}' AND "
            f"`{table.pk}` > {committed.cursor_pk or 0}))"
        )

    bounds = spark.read.format("jdbc").options(
        url=cfg.jdbc_url,
        query=(
            f"SELECT MIN(`{table.pk}`) AS lo, MAX(`{table.pk}`) AS hi "
            f"FROM `{table.name}`{range_pred}"
        ),
    ).load().first()

    cursor_brief = {
        "field": table.cursor_field,
        "committed_at": committed.cursor_at if committed else None,
        "committed_pk": committed.cursor_pk if committed else None,
        "high_watermark_at": high_watermark_at,
        "high_watermark_pk": high_watermark_pk,
        "min_at": None,
        "max_at": None,
    }
    if bounds["lo"] is None:
        manifest = {
            "manifest_version": MANIFEST_VERSION, "run_id": run_id,
            "table": table.name,
            "source": {"system": "mysql_ecommerce", "schema": "ecommerce"},
            "cursor": cursor_brief,
            "rows": 0, "empty": True, "files": [],
            "generated_at_utc": now_utc,
        }
        _write_manifest(spark, paths.bucket, paths.manifest_key(), manifest)
        return manifest

    df = (
        spark.read.format("jdbc")
        .option("url", cfg.jdbc_url)
        .option("dbtable", f"(SELECT * FROM `{table.name}`{range_pred}) AS extract_src")
        .option("partitionColumn", table.pk)
        .option("lowerBound", str(bounds["lo"]))
        .option("upperBound", str(bounds["hi"] + 1))
        .option("numPartitions", 4)
        .load()
        .orderBy(table.cursor_field, table.pk)
        .withColumn("_run_id", lit(run_id))
        .withColumn("_source_system", lit("mysql_ecommerce"))
        .withColumn("_source_schema", lit("ecommerce"))
        .withColumn("_source_table", lit(table.name))
        .withColumn("_source_primary_key", col(table.pk).cast("string"))
        .withColumn("_source_cursor_at", col(table.cursor_field))
        .withColumn("_source_high_watermark", lit(high_watermark_at))
        .withColumn("_ingested_at_utc", lit(now_utc))
    )

    df.write.mode("overwrite").parquet(
        f"s3a://{paths.bucket}/{paths.data_prefix()}"
    )
    files = _file_stats(spark, paths)

    cursor_df = df.agg(
        min(col(table.cursor_field)).alias("min_at"),
        max(col(table.cursor_field)).alias("max_at"),
        count("*").alias("row_count"),
    ).first()
    cursor_brief["min_at"] = str(cursor_df["min_at"])
    cursor_brief["max_at"] = str(cursor_df["max_at"])

    manifest = {
        "manifest_version": MANIFEST_VERSION, "run_id": run_id,
        "table": table.name,
        "source": {"system": "mysql_ecommerce", "schema": "ecommerce"},
        "cursor": cursor_brief,
        "rows": int(cursor_df["row_count"]),
        "empty": False, "files": files,
        "generated_at_utc": now_utc,
    }
    _write_manifest(spark, paths.bucket, paths.manifest_key(), manifest)
    return manifest


def run_extract(
    spark: SparkSession,
    cfg: Config,
    high_watermarks: dict[str, dict],
    run_id: str,
    extract_date: str,
    max_workers: int,
) -> list[dict]:
    def worker(table: TableSpec) -> dict:
        hw = high_watermarks.get(table.name)
        if hw is None:
            raise RuntimeError(f"no high watermark captured for {table.name}")
        committed = read_committed_cursor(spark, cfg.bucket, table.name)
        return extract_one_table(
            spark, cfg, table, run_id, extract_date,
            high_watermark_at=hw["at"], high_watermark_pk=hw.get("pk"),
            committed=committed,
        )

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(worker, table): table.name for table in cfg.tables}
        manifests = []
        for future in concurrent.futures.as_completed(futures):
            try:
                manifests.append(future.result())
            except Exception:
                for other in futures:
                    other.cancel()
                raise
    return manifests