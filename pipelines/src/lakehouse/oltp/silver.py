from __future__ import annotations

import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pyspark.sql import DataFrame, SparkSession

try:
    from pyspark.sql import functions as F
    from pyspark.sql.window import Window
except ImportError:
    F = Window = None  # type: ignore


@dataclass
class MergeResult:
    inserted: int = 0
    updated: int = 0
    quarantined: int = 0


def _get_salt() -> str:
    return os.environ.get("SILVER_PSEUDONYMIZE_SALT", "")


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
    return (
        df.withColumn("_silver_ingested_at", F.current_timestamp())
        .withColumn("_source_bronze_run_id", F.lit(run_id))
    )


def _validate_rows(df: DataFrame, table_name: str) -> tuple[DataFrame, DataFrame]:
    violations = []

    if table_name == "product_variants":
        violations.append(F.when(F.col("price_vnd") < 0, F.lit("negative_price")))
    if table_name == "orders":
        valid_statuses = {
            "pending_payment", "paid", "payment_failed", "confirmed",
            "shipping", "delivered", "completed", "cancelled",
            "failed_delivery", "returned",
        }
        violations.append(F.when(~F.col("status").isin(*valid_statuses), F.lit("invalid_order_status")))
    if table_name in ("cart_items", "order_items"):
        violations.append(F.when(F.col("quantity") <= 0, F.lit("invalid_quantity")))
    if table_name == "payments":
        valid_payment_statuses = {"succeeded", "failed"}
        violations.append(F.when(~F.col("status").isin(*valid_payment_statuses), F.lit("invalid_payment_status")))
    if table_name == "refunds":
        violations.append(F.when(F.col("amount_vnd") < 0, F.lit("negative_refund")))
    if table_name == "coupons":
        violations.append(
            F.when(
                (F.col("discount_type") == "percentage") & ((F.col("discount_value") < 1) | (F.col("discount_value") > 100)),
                F.lit("invalid_discount_percentage"),
            )
        )
    if table_name == "product_reviews":
        violations.append(F.when((F.col("rating") < 1) | (F.col("rating") > 5), F.lit("invalid_rating")))
    if table_name in ("inventory", "store_inventory"):
        violations.append(F.when(F.col("on_hand") < 0, F.lit("negative_inventory")))
    if table_name == "shipments":
        valid_shipment_statuses = {
            "assigned", "picked_up", "in_transit", "delivered", "failed", "returned_to_warehouse"
        }
        violations.append(F.when(~F.col("status").isin(*valid_shipment_statuses), F.lit("invalid_shipment_status")))
    if table_name == "return_requests":
        valid_return_actions = {"exchange", "refund"}
        violations.append(F.when(~F.col("action_type").isin(*valid_return_actions), F.lit("invalid_return_action")))
    if table_name == "inventory_transactions":
        valid_movement_types = {
            "inbound", "outbound_order", "outbound_pos", "transfer_to_store",
            "transfer_received", "return_boom", "return_customer", "exchange_out", "adjustment"
        }
        violations.append(F.when(~F.col("movement_type").isin(*valid_movement_types), F.lit("invalid_movement_type")))

    if not violations:
        return df, df.limit(0)

    violation_expr = F.coalesce(*violations)

    df_with_violation = df.withColumn("_violation_type", violation_expr)
    violating = df_with_violation.filter(F.col("_violation_type").isNotNull())
    valid = df_with_violation.filter(F.col("_violation_type").isNull()).drop("_violation_type")

    return valid, violating


def write_quarantine(
    spark: SparkSession,
    violations_df: DataFrame,
    source_table: str,
    run_id: str,
    target_path: str | None = None,
    _write_format: str = "iceberg",
) -> int:
    quarantined = violations_df.select(
        F.to_json(F.struct("*")).alias("record_data"),
        F.col("_violation_type").alias("violation_type"),
        F.lit(f"Business rule violation in {source_table}").alias("violation_detail"),
        F.lit(source_table).alias("source_table"),
        F.lit(run_id).alias("_run_id"),
        F.current_timestamp().alias("_quarantined_at"),
    )

    count = quarantined.count()
    if count == 0:
        return 0

    if _write_format == "iceberg":
        quarantined.write.format("iceberg").mode("append").saveAsTable(
            "lakehouse.quarantine.silver_oltp_violations"
        )
    else:
        quarantined.write.format(_write_format).mode("append").save(target_path)

    return count


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

    valid_df, violations_df = _validate_rows(deduped, table.name)

    if violations_df.head(1):
        quarantine_count = write_quarantine(
            spark, violations_df, table.name, run_id,
            target_path=f"{target_path}_quarantine",
            _write_format=_write_format,
        )
        result.quarantined = quarantine_count

    if table.pseudonymize:
        for col_name in table.pseudonymize:
            if col_name in valid_df.columns:
                valid_df = valid_df.withColumn(
                    f"{col_name}_pseudonymized",
                    F.sha2(F.concat(F.col(col_name).cast("string"), F.lit(_get_salt())), 256),
                )
                valid_df = valid_df.drop(col_name)
            else:
                valid_df = valid_df.withColumn(
                    f"{col_name}_pseudonymized",
                    F.lit(None).cast("string"),
                )
        valid_df = valid_df.withColumn("_pii_pseudonymized_at", F.current_timestamp())
    else:
        valid_df = valid_df.withColumn("_pii_pseudonymized_at", F.lit(None).cast("timestamp"))

    valid_df = _add_silver_metadata(valid_df, run_id)

    target_exists = False
    existing_df = None
    try:
        if _write_format == "iceberg":
            existing_df = spark.read.format("iceberg").load(target_path)
        else:
            existing_df = spark.read.format(_write_format).load(target_path)
        target_exists = True
    except Exception:
        pass

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
            valid_df.writeTo(target_path).createOrReplace()
        else:
            valid_df.write.format(_write_format).mode("overwrite").save(target_path)

    return result
