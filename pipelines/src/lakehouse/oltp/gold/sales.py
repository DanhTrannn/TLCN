from __future__ import annotations

from pyspark.sql import DataFrame, functions as F


def build_fact_order(
    silver_orders: DataFrame,
    silver_order_items: DataFrame,
    run_id: str,
    silver_product_variants: DataFrame | None = None,
) -> DataFrame:
    oi = silver_order_items.alias("oi")
    if silver_product_variants is not None:
        pv = silver_product_variants.alias("pv")
        oi_joined = oi.join(pv, F.col("oi.variant_id") == F.col("pv.variant_id"), "left")
    else:
        oi_joined = oi

    has_oi_cost = "cost_price_vnd" in silver_order_items.columns
    has_pv_cost = silver_product_variants is not None and "cost_price_vnd" in silver_product_variants.columns

    if has_oi_cost and has_pv_cost:
        unit_cost = F.coalesce(F.col("oi.cost_price_vnd"), F.col("pv.cost_price_vnd"), F.lit(0).cast("bigint"))
    elif has_oi_cost:
        unit_cost = F.coalesce(F.col("oi.cost_price_vnd"), F.lit(0).cast("bigint"))
    elif has_pv_cost:
        unit_cost = F.coalesce(F.col("pv.cost_price_vnd"), F.lit(0).cast("bigint"))
    else:
        unit_cost = F.lit(0).cast("bigint")

    cost_per_item = F.col("oi.quantity") * unit_cost
    items_agg = oi_joined.groupBy("oi.order_id").agg(
        F.sum(cost_per_item).alias("total_cost_vnd"),
        F.sum("oi.quantity").alias("total_quantity"),
    )

    o = silver_orders.alias("o")
    agg = items_agg.alias("agg")
    joined = o.join(agg, F.col("o.order_id") == F.col("agg.order_id"), "left")

    gross_rev = F.col("o.total_vnd")
    tot_cost = F.coalesce(F.col("agg.total_cost_vnd"), F.lit(0))
    gross_prof = gross_rev - tot_cost

    # Revenue recognition: 0 if delivery failed (boom), returned, cancelled, or payment failed
    is_non_revenue = F.col("o.status").isin("failed_delivery", "returned", "cancelled", "payment_failed")
    net_rev = F.when(is_non_revenue, F.lit(0)).otherwise(gross_rev)
    net_prof = F.when(is_non_revenue, F.lit(0)).otherwise(gross_prof)

    discount_col = (
        F.col("o.discount_vnd")
        if "discount_vnd" in silver_orders.columns
        else (
            F.col("o.discount_amount_vnd")
            if "discount_amount_vnd" in silver_orders.columns
            else F.lit(0).cast("bigint")
        )
    )
    payment_status_col = (
        F.col("o.payment_status")
        if "payment_status" in silver_orders.columns
        else (
            F.when(F.col("o.paid_at").isNotNull(), F.lit("succeeded")).otherwise(F.lit("pending"))
            if "paid_at" in silver_orders.columns
            else F.lit("pending")
        )
    )
    payment_method_col = F.col("o.payment_method") if "payment_method" in silver_orders.columns else F.lit("cod")
    coupon_id_col = F.col("o.coupon_id") if "coupon_id" in silver_orders.columns else F.lit(None).cast("bigint")
    subtotal_col = F.col("o.subtotal_vnd") if "subtotal_vnd" in silver_orders.columns else gross_rev
    shipping_fee_col = (
        F.col("o.shipping_fee_vnd") if "shipping_fee_vnd" in silver_orders.columns else F.lit(0).cast("bigint")
    )
    channel_col = (
        F.col("o.channel")
        if "channel" in silver_orders.columns
        else (
            F.when(F.col("o.store_id").isNotNull() & (F.col("o.store_id") > 0), F.lit("pos")).otherwise(F.lit("online"))
        )
    )

    return joined.select(
        F.col("o.order_id"),
        F.col("o.order_number"),
        F.coalesce(F.col("o.customer_id"), F.lit(-1)).alias("customer_key"),
        F.coalesce(F.col("o.store_id"), F.lit(0)).alias("store_key"),
        F.date_format(F.col("o.created_at"), "yyyyMMdd").cast("int").alias("order_date_key"),
        F.to_date(F.col("o.created_at")).alias("order_date"),
        channel_col.alias("channel"),
        F.col("o.status"),
        payment_method_col.alias("payment_method"),
        payment_status_col.alias("payment_status"),
        coupon_id_col.alias("coupon_id"),
        subtotal_col.alias("subtotal_vnd"),
        discount_col.alias("discount_vnd"),
        shipping_fee_col.alias("shipping_fee_vnd"),
        gross_rev.alias("gross_revenue_vnd"),
        tot_cost.alias("total_cost_vnd"),
        gross_prof.alias("gross_profit_vnd"),
        net_rev.alias("net_revenue_vnd"),
        net_prof.alias("net_profit_vnd"),
        (F.col("o.status") == "failed_delivery").alias("is_boom"),
        F.col("o.status").isin("delivered", "completed").alias("is_delivered"),
        F.current_timestamp().alias("_gold_ingested_at"),
        F.lit(run_id).alias("_source_run_id"),
    )


def build_fact_order_item(
    silver_order_items: DataFrame,
    silver_orders: DataFrame,
    run_id: str,
    silver_product_variants: DataFrame | None = None,
) -> DataFrame:
    oi = silver_order_items.alias("oi")
    o = silver_orders.alias("o")

    base_df = oi.join(o, F.col("oi.order_id") == F.col("o.order_id"), "left")

    if silver_product_variants is not None:
        pv = silver_product_variants.alias("pv")
        base_df = base_df.join(pv, F.col("oi.variant_id") == F.col("pv.variant_id"), "left")

    if "product_id" in silver_order_items.columns:
        product_key_col = F.col("oi.product_id")
    elif silver_product_variants is not None and "product_id" in silver_product_variants.columns:
        product_key_col = F.coalesce(F.col("pv.product_id"), F.lit(0).cast("bigint"))
    else:
        product_key_col = F.lit(0).cast("bigint")

    has_oi_cost = "cost_price_vnd" in silver_order_items.columns
    has_pv_cost = silver_product_variants is not None and "cost_price_vnd" in silver_product_variants.columns

    if has_oi_cost and has_pv_cost:
        unit_cost = F.coalesce(F.col("oi.cost_price_vnd"), F.col("pv.cost_price_vnd"), F.lit(0).cast("bigint"))
    elif has_oi_cost:
        unit_cost = F.coalesce(F.col("oi.cost_price_vnd"), F.lit(0).cast("bigint"))
    elif has_pv_cost:
        unit_cost = F.coalesce(F.col("pv.cost_price_vnd"), F.lit(0).cast("bigint"))
    else:
        unit_cost = F.lit(0).cast("bigint")

    item_total = F.col("oi.quantity") * F.col("oi.unit_price_vnd")
    item_cost = F.col("oi.quantity") * unit_cost
    item_profit = item_total - item_cost

    channel_col = (
        F.col("o.channel")
        if "channel" in silver_orders.columns
        else (
            F.when(F.col("o.store_id").isNotNull() & (F.col("o.store_id") > 0), F.lit("pos")).otherwise(F.lit("online"))
        )
    )

    return base_df.select(
        F.col("oi.order_item_id"),
        F.col("oi.order_id"),
        F.date_format(F.col("o.created_at"), "yyyyMMdd").cast("int").alias("order_date_key"),
        F.to_date(F.col("o.created_at")).alias("order_date"),
        F.coalesce(F.col("o.customer_id"), F.lit(-1)).alias("customer_key"),
        product_key_col.alias("product_key"),
        F.col("oi.variant_id").alias("variant_key"),
        F.coalesce(F.col("o.store_id"), F.lit(0)).alias("store_key"),
        channel_col.alias("channel"),
        F.col("o.status").alias("order_status"),
        F.col("oi.quantity"),
        F.col("oi.unit_price_vnd"),
        unit_cost.alias("unit_cost_vnd"),
        item_total.alias("item_total_vnd"),
        item_cost.alias("item_cost_vnd"),
        item_profit.alias("item_profit_vnd"),
        F.current_timestamp().alias("_gold_ingested_at"),
        F.lit(run_id).alias("_source_run_id"),
    )


def build_mart_sales_daily(
    fact_order: DataFrame,
    fact_order_item: DataFrame,
    dim_product: DataFrame,
    run_id: str,
) -> DataFrame:
    fo = fact_order.alias("fo")
    foi = fact_order_item.alias("foi")
    dp = dim_product.alias("dp")

    orders_enriched = foi.join(fo, F.col("foi.order_id") == F.col("fo.order_id"), "inner").join(
        dp, F.col("foi.product_key") == F.col("dp.product_key"), "left"
    )

    delivered_qty = F.when(F.col("fo.is_delivered"), F.col("foi.quantity")).otherwise(0)
    delivered_rev = F.when(F.col("fo.is_delivered"), F.col("foi.item_total_vnd")).otherwise(0)
    delivered_cost = F.when(F.col("fo.is_delivered"), F.col("foi.item_cost_vnd")).otherwise(0)
    delivered_profit = F.when(F.col("fo.is_delivered"), F.col("foi.item_profit_vnd")).otherwise(0)

    delivered_order_expr = F.when(F.col("fo.is_delivered"), F.col("fo.order_id"))
    boom_order_expr = F.when(F.col("fo.is_boom"), F.col("fo.order_id"))

    grouped = orders_enriched.groupBy(
        F.col("fo.order_date"),
        F.col("fo.channel"),
        F.col("fo.store_key"),
        F.coalesce(F.col("dp.category_id"), F.lit(0)).alias("category_id"),
        F.coalesce(F.col("dp.category_name"), F.lit("Unknown")).alias("category_name"),
    ).agg(
        F.countDistinct("fo.order_id").alias("total_orders"),
        F.countDistinct(delivered_order_expr).alias("successful_orders"),
        F.countDistinct(boom_order_expr).alias("boom_orders"),
        F.sum(delivered_qty).alias("items_sold"),
        F.sum(delivered_rev).alias("gross_revenue_vnd"),
        F.sum(delivered_cost).alias("cogs_vnd"),
        F.sum(delivered_profit).alias("gross_profit_vnd"),
    )

    margin_expr = F.when(
        F.col("gross_revenue_vnd") > 0,
        F.round((F.col("gross_profit_vnd") / F.col("gross_revenue_vnd")) * 100.0, 2),
    ).otherwise(0.0)

    return (
        grouped.withColumn("gross_profit_margin_pct", margin_expr)
        .withColumn("_gold_ingested_at", F.current_timestamp())
        .withColumn("_source_run_id", F.lit(run_id))
        .select(
            "order_date",
            "channel",
            "store_key",
            "category_id",
            "category_name",
            "total_orders",
            "successful_orders",
            "boom_orders",
            "items_sold",
            "gross_revenue_vnd",
            "cogs_vnd",
            "gross_profit_vnd",
            "gross_profit_margin_pct",
            "_gold_ingested_at",
            "_source_run_id",
        )
    )
