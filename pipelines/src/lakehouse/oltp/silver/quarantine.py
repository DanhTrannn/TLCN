from __future__ import annotations

from pyspark.sql import DataFrame, SparkSession, functions as F
from .pii import _redact_quarantine_pii


def write_quarantine(
    spark: SparkSession,
    violations_df: DataFrame,
    source_table: str,
    run_id: str,
    target_path: str | None = None,
    _write_format: str = "iceberg",
) -> int:
    safe_violations_df = _redact_quarantine_pii(violations_df)
    quarantined = safe_violations_df.select(
        F.to_json(F.struct("*")).alias("record_data"),
        F.col("_violation_type").alias("violation_type"),
        F.col("_violation_types").alias("violation_types"),
        F.lit(f"Business rule violation in {source_table}").alias("violation_detail"),
        F.lit(source_table).alias("source_table"),
        F.lit(run_id).alias("_run_id"),
        F.current_timestamp().alias("_quarantined_at"),
    )

    count = quarantined.count()
    if count == 0:
        return 0

    if _write_format == "iceberg":
        quarantined.write.format("iceberg").mode("append").saveAsTable("lakehouse.quarantine.silver_oltp_violations")
    else:
        quarantined.write.format(_write_format).mode("append").save(target_path)

    return count
