from __future__ import annotations

from pyspark.sql import DataFrame, functions as F


def build_fact_return_exchange(
    silver_return_requests: DataFrame,
    silver_return_items: DataFrame,
    run_id: str,
) -> DataFrame:
    rr = silver_return_requests.alias("rr")
    ri = silver_return_items.alias("ri")

    return_number_col = (
        F.col("rr.return_number") if "return_number" in silver_return_requests.columns else F.col("rr.return_code")
    )
    returned_variant_col = (
        F.col("ri.returned_variant_id")
        if "returned_variant_id" in silver_return_items.columns
        else F.col("ri.variant_id")
    )
    exchanged_variant_col = (
        F.col("ri.exchanged_variant_id")
        if "exchanged_variant_id" in silver_return_items.columns
        else F.col("ri.exchange_variant_id")
    )
    refund_col = (
        F.coalesce(F.col("rr.refund_amount_vnd"), F.lit(0))
        if "refund_amount_vnd" in silver_return_requests.columns
        else F.coalesce(F.col("ri.refund_amount_vnd"), F.lit(0))
    )
    reason_col = F.col("rr.reason") if "reason" in silver_return_requests.columns else F.col("rr.customer_reason")

    return ri.join(rr, F.col("ri.return_id") == F.col("rr.return_id"), "inner").select(
        F.col("ri.return_item_id"),
        F.col("rr.return_id"),
        return_number_col.alias("return_number"),
        F.col("rr.order_id"),
        F.col("ri.order_item_id"),
        F.date_format(F.col("rr.created_at"), "yyyyMMdd").cast("int").alias("return_date_key"),
        F.to_date(F.col("rr.created_at")).alias("return_date"),
        F.col("rr.action_type"),
        F.col("rr.status").alias("return_status"),
        reason_col.alias("reason"),
        returned_variant_col.alias("returned_variant_key"),
        exchanged_variant_col.alias("exchanged_variant_key"),
        F.col("ri.quantity").alias("returned_quantity"),
        refund_col.alias("refund_amount_vnd"),
        F.current_timestamp().alias("_gold_ingested_at"),
        F.lit(run_id).alias("_source_run_id"),
    )


def build_mart_product_returns(
    fact_return_exchange: DataFrame,
    dim_variant: DataFrame,
    run_id: str,
) -> DataFrame:
    fr = fact_return_exchange.alias("fr")
    dv = dim_variant.alias("dv")

    joined = fr.join(dv, F.col("fr.returned_variant_key") == F.col("dv.variant_key"), "left")

    return (
        joined.groupBy(
            F.col("fr.return_date"),
            F.col("fr.returned_variant_key"),
            F.coalesce(F.col("dv.product_id"), F.lit(0)).alias("product_id"),
            F.coalesce(F.col("dv.product_name"), F.lit("Unknown")).alias("product_name"),
            F.coalesce(F.col("dv.sku"), F.lit("Unknown")).alias("sku"),
            F.coalesce(F.col("dv.size"), F.lit("Unknown")).alias("size"),
            F.coalesce(F.col("dv.color"), F.lit("Unknown")).alias("color"),
            F.col("fr.action_type"),
            F.coalesce(F.col("fr.reason"), F.lit("Unknown")).alias("reason"),
        )
        .agg(
            F.count("*").alias("total_return_requests"),
            F.sum(F.col("fr.returned_quantity")).alias("total_returned_quantity"),
            F.sum(F.col("fr.refund_amount_vnd")).alias("total_refund_amount_vnd"),
        )
        .withColumn("_gold_ingested_at", F.current_timestamp())
        .withColumn("_source_run_id", F.lit(run_id))
        .select(
            "return_date",
            "returned_variant_key",
            "product_id",
            "product_name",
            "sku",
            "size",
            "color",
            "action_type",
            "reason",
            "total_return_requests",
            "total_returned_quantity",
            "total_refund_amount_vnd",
            "_gold_ingested_at",
            "_source_run_id",
        )
    )
