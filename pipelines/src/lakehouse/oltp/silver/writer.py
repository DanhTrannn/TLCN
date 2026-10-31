from __future__ import annotations

from typing import Any
from pyspark.sql import DataFrame, SparkSession, functions as F
from dataclasses import dataclass
from .dedup import _dedup_by_pk, _add_silver_metadata
from .pii import _pseudonymize, _pseudonymized_column_name
from .validation import _validate_rows
from .quarantine import write_quarantine


@dataclass
class MergeResult:
    inserted: int = 0
    updated: int = 0
    quarantined: int = 0


def merge_oltp_table(
    spark: SparkSession,
    table: Any,
    bronze_df: DataFrame,
    run_id: str,
    target_path: str,
    _write_format: str = "iceberg",
) -> MergeResult:
    result = MergeResult()

    deduped = _dedup_by_pk(bronze_df, table.pk, table.cursor_field)

    # Treat a missing primary key as a quarantinable row-level violation.
    if table.pk in deduped.columns:
        deduped = deduped.withColumn(
            "_missing_primary_key",
            F.when(F.col(table.pk).isNull(), F.lit("missing_primary_key")),
        )

    valid_df, violations_df = _validate_rows(deduped, table.name)
    valid_df = valid_df.drop("_missing_primary_key")
    violations_df = violations_df.drop("_missing_primary_key")

    if violations_df.head(1):
        quarantine_count = write_quarantine(
            spark,
            violations_df,
            table.name,
            run_id,
            target_path=f"{target_path}_quarantine",
            _write_format=_write_format,
        )
        result.quarantined = quarantine_count

    if table.pseudonymize:
        for col_name in table.pseudonymize:
            if col_name in valid_df.columns:
                valid_df = valid_df.withColumn(
                    _pseudonymized_column_name(col_name),
                    _pseudonymize(F.col(col_name)),
                )
                valid_df = valid_df.drop(col_name)
            else:
                valid_df = valid_df.withColumn(
                    _pseudonymized_column_name(col_name),
                    F.lit(None).cast("string"),
                )
        valid_df = valid_df.withColumn("_pii_pseudonymized_at", F.current_timestamp())
    else:
        valid_df = valid_df.withColumn("_pii_pseudonymized_at", F.lit(None).cast("timestamp"))

    valid_df = _add_silver_metadata(valid_df, run_id)

    if _write_format == "iceberg":
        target_exists = spark.catalog.tableExists(target_path)
        existing_df = spark.read.format("iceberg").load(target_path) if target_exists else None
    else:
        from pyspark.errors import AnalysisException

        try:
            existing_df = spark.read.format(_write_format).load(target_path)
            target_exists = True
        except AnalysisException as exc:
            if exc.getErrorClass() != "PATH_NOT_FOUND":
                raise
            existing_df, target_exists = None, False

    if target_exists:
        existing_deduped = _dedup_by_pk(existing_df, table.pk, table.cursor_field)

        existing_pks = existing_deduped.select(table.pk).distinct()
        batch_pks = valid_df.select(table.pk).distinct()
        new_pks_count = batch_pks.join(existing_pks, table.pk, "left_anti").count()
        updated_pks_count = batch_pks.join(existing_pks, table.pk, "inner").count()

        result.inserted = new_pks_count
        result.updated = updated_pks_count

        combined = valid_df.unionByName(existing_deduped, allowMissingColumns=True)
        merged = _dedup_by_pk(combined, table.pk, table.cursor_field)

        # Ensure schema alignment with target table
        target_cols = existing_df.columns
        for c in target_cols:
            if c not in merged.columns:
                merged = merged.withColumn(c, F.lit(None))
        merged = merged.select(*target_cols)

        if _write_format == "iceberg":
            merged.writeTo(target_path).overwrite(F.lit(True))
        else:
            merged.write.format(_write_format).mode("overwrite").save(target_path)
    else:
        result.inserted = valid_df.count()
        result.updated = 0
        if _write_format == "iceberg":
            valid_df.writeTo(target_path).using("iceberg").create()
        else:
            valid_df.write.format(_write_format).mode("overwrite").save(target_path)

    return result
