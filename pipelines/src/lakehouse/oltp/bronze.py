from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyspark.sql import SparkSession

try:
    from pyspark.sql.functions import col, current_timestamp, input_file_name, lit
except ImportError:
    col = current_timestamp = input_file_name = lit = None  # type: ignore


def ingest_to_bronze(
    spark: SparkSession,
    run_id: str,
    source_path: str,
    source_format: str,
    target_table: str,
    quarantine_table: str,
    error_threshold: float = 0.01,
    _write_format: str = "iceberg",
) -> None:
    # Read permissive mode
    df = (
        spark.read.option("mode", "PERMISSIVE")
        .option("columnNameOfCorruptRecord", "_corrupt_record")
        .format(source_format)
        .load(source_path)
    )

    # Add lineage columns
    df = (
        df.withColumn("_run_id", lit(run_id))
        .withColumn("_source_file", input_file_name())
        .withColumn("_ingested_at_utc", current_timestamp())
    )

    df.cache()
    try:
        total_count = df.count()
        if total_count == 0:
            return

        # Check for errors
        if "_corrupt_record" in df.columns:
            error_df = df.filter(col("_corrupt_record").isNotNull())
            error_count = error_df.count()

            if error_count / total_count >= error_threshold:
                raise RuntimeError(
                    f"Error threshold exceeded: {error_count} errors out of {total_count} records."
                )

            if error_count > 0:
                if _write_format == "iceberg":
                    error_df.write.format("iceberg").mode("append").saveAsTable(quarantine_table)
                else:
                    error_df.write.format(_write_format).mode("append").save(quarantine_table)

            valid_df = df.filter(col("_corrupt_record").isNull()).drop("_corrupt_record")
        else:
            valid_df = df

        # Write valid to target
        if _write_format == "iceberg":
            valid_df.write.format("iceberg").mode("append").saveAsTable(target_table)
        else:
            valid_df.write.format(_write_format).mode("append").save(target_table)
    finally:
        df.unpersist()
