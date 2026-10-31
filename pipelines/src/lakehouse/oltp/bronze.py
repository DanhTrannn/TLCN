from __future__ import annotations

from lakehouse.sql import identifier, render_sql, sql_type

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyspark.sql import SparkSession

try:
    from pyspark.sql.functions import col, current_timestamp, input_file_name, lit
except ImportError:
    col = current_timestamp = input_file_name = lit = None  # type: ignore


def _append_iceberg_with_schema_evolution(spark, df, target_table: str) -> None:
    """Replace one run atomically; preserve other runs and additive source columns."""
    table_exists = spark.catalog.tableExists(target_table)
    run_ids = df.select("_run_id").distinct().collect()
    if len(run_ids) != 1 or not run_ids[0]["_run_id"]:
        raise ValueError("Bronze writes require exactly one non-empty run_id")
    run_id = run_ids[0]["_run_id"]

    if table_exists:
        spark.sql(render_sql("spark/bronze/enable_schema_evolution.sql", target_table=identifier(target_table)))

        target_schema = spark.table(target_table).schema
        target_names = {field.name for field in target_schema.fields}
        for field in df.schema.fields:
            if field.name not in target_names:
                column_name = field.name.replace("`", "``")
                spark.sql(
                    render_sql(
                        "spark/bronze/add_column.sql",
                        target_table=identifier(target_table),
                        column_name=identifier(column_name),
                        field_datatype_simplestring=sql_type(field.dataType.simpleString()),
                    )
                )

        # Iceberg validates physical field ordering even for V2 writes. Align
        # to the evolved table and backfill a typed NULL when a source column
        # has been retired.
        target_schema = spark.table(target_table).schema
        source_names = set(df.columns)
        aligned_df = df.select(
            *[
                col(f"`{field.name.replace('`', '``')}`")
                if field.name in source_names
                else lit(None).cast(field.dataType).alias(field.name)
                for field in target_schema.fields
            ]
        )
        aligned_df.writeTo(target_table).overwrite(col("_run_id") == lit(run_id))
        return

    (
        df.writeTo(target_table)
        .using("iceberg")
        .tableProperty("format-version", "2")
        .tableProperty("write.spark.accept-any-schema", "true")
        .create()
    )


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
    if not 0 < error_threshold <= 1:
        raise ValueError("error_threshold must be in (0, 1]")
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
                raise RuntimeError(f"Error threshold exceeded: {error_count} errors out of {total_count} records.")

            if error_count > 0:
                if _write_format == "iceberg":
                    _append_iceberg_with_schema_evolution(spark, error_df, quarantine_table)
                else:
                    error_df.write.format(_write_format).mode("append").save(quarantine_table)

            valid_df = df.filter(col("_corrupt_record").isNull()).drop("_corrupt_record")
        else:
            valid_df = df

        # Write valid to target
        if _write_format == "iceberg":
            _append_iceberg_with_schema_evolution(spark, valid_df, target_table)
        else:
            valid_df.write.format(_write_format).mode("append").save(target_table)
    finally:
        df.unpersist()
