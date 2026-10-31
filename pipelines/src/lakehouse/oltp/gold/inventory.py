from __future__ import annotations

from pyspark.sql import DataFrame, functions as F


def build_fact_inventory_daily_snapshot(
    silver_inventory: DataFrame,
    silver_store_inventory: DataFrame,
    silver_product_variants: DataFrame,
    snapshot_date: str,
    run_id: str,
) -> DataFrame:
    wh_reserved = (
        F.col("reserved").alias("reserved_quantity")
        if "reserved" in silver_inventory.columns
        else F.lit(0).cast("int").alias("reserved_quantity")
    )
    store_reserved = (
        F.col("reserved").alias("reserved_quantity")
        if "reserved" in silver_store_inventory.columns
        else F.lit(0).cast("int").alias("reserved_quantity")
    )

    inv = silver_inventory.select(
        F.lit("warehouse").alias("location_type"),
        F.lit(0).cast("bigint").alias("location_id"),
        F.col("variant_id"),
        F.col("on_hand").alias("on_hand_quantity"),
        wh_reserved,
    )
    store_inv = silver_store_inventory.select(
        F.lit("store").alias("location_type"),
        F.col("store_id").cast("bigint").alias("location_id"),
        F.col("variant_id"),
        F.col("on_hand").alias("on_hand_quantity"),
        store_reserved,
    )
    combined = inv.unionByName(store_inv)

    v = silver_product_variants.alias("v")
    c = combined.alias("c")

    joined = c.join(v, F.col("c.variant_id") == F.col("v.variant_id"), "left")
    unit_cost = F.coalesce(F.col("v.cost_price_vnd"), F.lit(0))
    inv_value = F.col("c.on_hand_quantity") * unit_cost

    date_col = F.to_date(F.lit(snapshot_date))
    date_key = F.date_format(date_col, "yyyyMMdd").cast("int")

    return joined.select(
        date_key.alias("snapshot_date_key"),
        date_col.alias("snapshot_date"),
        F.col("c.location_type"),
        F.col("c.location_id"),
        F.col("c.variant_id").alias("variant_key"),
        F.col("v.product_id").alias("product_key"),
        F.col("c.on_hand_quantity"),
        F.col("c.reserved_quantity"),
        unit_cost.alias("unit_cost_vnd"),
        inv_value.alias("inventory_value_cost_vnd"),
        (F.col("c.on_hand_quantity") < 10).alias("is_low_stock"),
        (F.col("c.on_hand_quantity") == 0).alias("is_out_of_stock"),
        F.current_timestamp().alias("_gold_ingested_at"),
        F.lit(run_id).alias("_source_run_id"),
    )


def build_mart_inventory_health(
    fact_inventory_daily_snapshot: DataFrame,
    dim_product: DataFrame,
    run_id: str,
) -> DataFrame:
    fi = fact_inventory_daily_snapshot.alias("fi")
    dp = dim_product.alias("dp")

    joined = fi.join(dp, F.col("fi.product_key") == F.col("dp.product_key"), "left")

    return (
        joined.groupBy(
            F.col("fi.snapshot_date"),
            F.col("fi.location_type"),
            F.col("fi.location_id"),
            F.coalesce(F.col("dp.category_id"), F.lit(0)).alias("category_id"),
            F.coalesce(F.col("dp.category_name"), F.lit("Unknown")).alias("category_name"),
        )
        .agg(
            F.countDistinct("fi.variant_key").alias("total_variants"),
            F.sum(F.when(F.col("fi.is_out_of_stock"), 1).otherwise(0)).alias("out_of_stock_count"),
            F.sum(F.when(F.col("fi.is_low_stock"), 1).otherwise(0)).alias("low_stock_count"),
            F.sum("fi.on_hand_quantity").alias("total_on_hand_units"),
            F.sum("fi.inventory_value_cost_vnd").alias("total_inventory_value_vnd"),
        )
        .withColumn("_gold_ingested_at", F.current_timestamp())
        .withColumn("_source_run_id", F.lit(run_id))
        .select(
            "snapshot_date",
            "location_type",
            "location_id",
            "category_id",
            "category_name",
            "total_variants",
            "out_of_stock_count",
            "low_stock_count",
            "total_on_hand_units",
            "total_inventory_value_vnd",
            "_gold_ingested_at",
            "_source_run_id",
        )
    )
