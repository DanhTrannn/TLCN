from __future__ import annotations

from pyspark.sql import DataFrame, functions as F
from pyspark.sql.window import Window


def _dedup_by_pk(df: DataFrame, pk: str, cursor: str) -> DataFrame:
    order_cols = []
    if cursor in df.columns:
        order_cols.append(F.col(cursor).desc())
    if "_silver_ingested_at" in df.columns:
        order_cols.append(F.col("_silver_ingested_at").desc())
    if "_ingested_at_utc" in df.columns:
        order_cols.append(F.col("_ingested_at_utc").desc())
    if not order_cols:
        order_cols.append(F.lit(1))
    window = Window.partitionBy(pk).orderBy(*order_cols)
    return df.withColumn("_rn", F.row_number().over(window)).filter(F.col("_rn") == 1).drop("_rn")


def _add_silver_metadata(df: DataFrame, run_id: str) -> DataFrame:
    return df.withColumn("_silver_ingested_at", F.current_timestamp()).withColumn(
        "_source_bronze_run_id", F.lit(run_id)
    )
