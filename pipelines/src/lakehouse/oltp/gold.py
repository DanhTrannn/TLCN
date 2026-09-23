from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyspark.sql import DataFrame, SparkSession

try:
    from pyspark.sql import functions as F
except ImportError:
    F = None  # type: ignore


# ==========================================
# 1. CONFORMED DIMENSIONS BUILDERS
# ==========================================

def build_dim_date(
    spark: SparkSession,
    start_date: str = "2025-01-01",
    end_date: str = "2027-12-31",
) -> DataFrame:
    df = spark.sql(f"SELECT sequence(to_date('{start_date}'), to_date('{end_date}')) as dates")
    df = df.select(F.explode(F.col("dates")).alias("full_date"))
    return (
        df.withColumn("date_key", F.date_format(F.col("full_date"), "yyyyMMdd").cast("int"))
        .withColumn("day_of_week", F.dayofweek(F.col("full_date")))
        .withColumn("day_name", F.date_format(F.col("full_date"), "EEEE"))
        .withColumn("day_of_month", F.dayofmonth(F.col("full_date")))
        .withColumn("day_of_year", F.dayofyear(F.col("full_date")))
        .withColumn("week_of_year", F.weekofyear(F.col("full_date")))
        .withColumn("month", F.month(F.col("full_date")))
        .withColumn("month_name", F.date_format(F.col("full_date"), "MMMM"))
        .withColumn("quarter", F.quarter(F.col("full_date")))
        .withColumn("year", F.year(F.col("full_date")))
        .withColumn("is_weekend", F.col("day_of_week").isin(1, 7))
        .withColumn("is_holiday", F.lit(False))
        .withColumn("_gold_ingested_at", F.current_timestamp())
        .select(
            "date_key",
            "full_date",
            "day_of_week",
            "day_name",
            "day_of_month",
            "day_of_year",
            "week_of_year",
            "month",
            "month_name",
            "quarter",
            "year",
            "is_weekend",
            "is_holiday",
            "_gold_ingested_at",
        )
    )


def build_dim_product(
    silver_products: DataFrame,
    silver_categories: DataFrame,
    run_id: str,
) -> DataFrame:
    p = silver_products.alias("p")
    c = silver_categories.alias("c")
    base_price_col = (
        F.col("p.base_price_vnd")
        if "base_price_vnd" in silver_products.columns
        else F.lit(0).cast("bigint")
    )
    return (
        p.join(c, F.col("p.category_id") == F.col("c.category_id"), "left")
        .select(
            F.col("p.product_id").alias("product_key"),
            F.col("p.product_id"),
            F.col("p.name").alias("product_name"),
            F.col("p.slug"),
            F.col("p.category_id"),
            F.coalesce(F.col("c.name"), F.lit("Unknown")).alias("category_name"),
            base_price_col.alias("base_price_vnd"),
            F.col("p.is_active"),
            F.col("p.created_at"),
            F.current_timestamp().alias("_gold_ingested_at"),
            F.lit(run_id).alias("_source_run_id"),
        )
    )


def build_dim_variant(
    silver_product_variants: DataFrame,
    silver_products: DataFrame,
    run_id: str,
) -> DataFrame:
    v = silver_product_variants.alias("v")
    p = silver_products.alias("p")
    margin_expr = F.when(
        F.col("v.price_vnd") > 0,
        F.round(
            ((F.col("v.price_vnd") - F.coalesce(F.col("v.cost_price_vnd"), F.lit(0))) / F.col("v.price_vnd")) * 100.0,
            2,
        ),
    ).otherwise(0.0)
    color_col = (
        F.col("v.color")
        if "color" in silver_product_variants.columns
        else F.col("v.color_code")
    )
    size_col = (
        F.col("v.size")
        if "size" in silver_product_variants.columns
        else F.col("v.size_code")
    )
    return (
        v.join(p, F.col("v.product_id") == F.col("p.product_id"), "left")
        .select(
            F.col("v.variant_id").alias("variant_key"),
            F.col("v.variant_id"),
            F.col("v.product_id"),
            F.coalesce(F.col("p.name"), F.lit("Unknown")).alias("product_name"),
            F.col("v.sku"),
            color_col.alias("color"),
            size_col.alias("size"),
            F.col("v.price_vnd"),
            F.coalesce(F.col("v.cost_price_vnd"), F.lit(0)).alias("cost_price_vnd"),
            margin_expr.alias("margin_pct"),
            F.col("v.is_active"),
            F.current_timestamp().alias("_gold_ingested_at"),
            F.lit(run_id).alias("_source_run_id"),
        )
    )


def build_dim_store(
    silver_stores: DataFrame,
    silver_cities: DataFrame,
    run_id: str,
) -> DataFrame:
    s = silver_stores.alias("s")
    c = silver_cities.alias("c")
    return (
        s.join(c, F.col("s.city_id") == F.col("c.city_id"), "left")
        .select(
            F.col("s.store_id").alias("store_key"),
            F.col("s.store_id"),
            F.col("s.code").alias("store_code"),
            F.col("s.name").alias("store_name"),
            F.col("s.city_id"),
            F.coalesce(F.col("c.name"), F.lit("Unknown")).alias("city_name"),
            F.col("s.address"),
            F.col("s.phone"),
            F.col("s.is_active"),
            F.current_timestamp().alias("_gold_ingested_at"),
            F.lit(run_id).alias("_source_run_id"),
        )
    )


def build_dim_delivery_staff(
    silver_delivery_staff: DataFrame,
    silver_cities: DataFrame,
    run_id: str,
) -> DataFrame:
    d = silver_delivery_staff.alias("d")
    c = silver_cities.alias("c")

    if "full_name_pseudonymized" in silver_delivery_staff.columns:
        full_name_col = F.col("d.full_name_pseudonymized")
    elif "full_name" in silver_delivery_staff.columns:
        full_name_col = F.col("d.full_name")
    else:
        full_name_col = F.lit("Unknown")

    if "phone_pseudonymized" in silver_delivery_staff.columns:
        phone_col = F.col("d.phone_pseudonymized")
    elif "phone" in silver_delivery_staff.columns:
        phone_col = F.col("d.phone")
    else:
        phone_col = F.lit("Unknown")

    staff_code_col = (
        F.col("d.staff_code")
        if "staff_code" in silver_delivery_staff.columns
        else F.concat(F.lit("DK-SHIP-"), F.col("d.staff_id").cast("string"))
    )
    assigned_city_col = (
        F.col("d.assigned_city_id")
        if "assigned_city_id" in silver_delivery_staff.columns
        else F.lit(None).cast("bigint")
    )
    vehicle_col = (
        F.col("d.vehicle_type")
        if "vehicle_type" in silver_delivery_staff.columns
        else (
            F.col("d.vehicle_plate")
            if "vehicle_plate" in silver_delivery_staff.columns
            else F.lit("motorbike")
        )
    )

    return (
        d.join(c, assigned_city_col == F.col("c.city_id"), "left")
        .select(
            F.col("d.staff_id").alias("staff_key"),
            F.col("d.staff_id"),
            staff_code_col.alias("staff_code"),
            full_name_col.alias("full_name"),
            phone_col.alias("phone"),
            assigned_city_col.alias("assigned_city_id"),
            F.coalesce(F.col("c.name"), F.lit("Toàn quốc")).alias("assigned_city_name"),
            vehicle_col.alias("vehicle_type"),
            F.col("d.is_active"),
            F.current_timestamp().alias("_gold_ingested_at"),
            F.lit(run_id).alias("_source_run_id"),
        )
    )


def build_dim_customer(
    silver_customers: DataFrame,
    silver_cities: DataFrame,
    run_id: str,
) -> DataFrame:
    cu = silver_customers.alias("cu")
    ci = silver_cities.alias("ci")

    email_col = (
        F.col("cu.email_pseudonymized")
        if "email_pseudonymized" in silver_customers.columns
        else (
            F.col("cu.email_normalized")
            if "email_normalized" in silver_customers.columns
            else F.lit(None).cast("string")
        )
    )
    phone_col = (
        F.col("cu.phone_pseudonymized")
        if "phone_pseudonymized" in silver_customers.columns
        else (
            F.col("cu.phone")
            if "phone" in silver_customers.columns
            else F.lit(None).cast("string")
        )
    )
    name_col = (
        F.col("cu.display_name_pseudonymized")
        if "display_name_pseudonymized" in silver_customers.columns
        else (
            F.col("cu.full_name_pseudonymized")
            if "full_name_pseudonymized" in silver_customers.columns
            else (
                F.col("cu.display_name")
                if "display_name" in silver_customers.columns
                else (
                    F.col("cu.full_name")
                    if "full_name" in silver_customers.columns
                    else F.lit("Unknown")
                )
            )
        )
    )

    return (
        cu.join(ci, F.col("cu.city_id") == F.col("ci.city_id"), "left")
        .select(
            F.col("cu.customer_id").alias("customer_key"),
            F.col("cu.customer_id"),
            email_col.alias("email"),
            phone_col.alias("phone"),
            name_col.alias("full_name"),
            F.col("cu.role"),
            F.col("cu.status"),
            F.col("cu.city_id"),
            F.coalesce(F.col("ci.name"), F.lit("Unknown")).alias("city_name"),
            F.col("cu.store_id"),
            F.coalesce(F.col("cu.is_cod_blocked"), F.lit(False)).alias("is_cod_blocked"),
            F.coalesce(F.col("cu.boom_count"), F.lit(0)).alias("boom_count"),
            F.col("cu.created_at"),
            F.current_timestamp().alias("_gold_ingested_at"),
            F.lit(run_id).alias("_source_run_id"),
        )
    )


# ==========================================
# 2. CORE FACTS BUILDERS
# ==========================================

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
    items_agg = (
        oi_joined.groupBy("oi.order_id")
        .agg(
            F.sum(cost_per_item).alias("total_cost_vnd"),
            F.sum("oi.quantity").alias("total_quantity"),
        )
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
    payment_method_col = (
        F.col("o.payment_method")
        if "payment_method" in silver_orders.columns
        else F.lit("cod")
    )
    coupon_id_col = (
        F.col("o.coupon_id")
        if "coupon_id" in silver_orders.columns
        else F.lit(None).cast("bigint")
    )
    subtotal_col = (
        F.col("o.subtotal_vnd")
        if "subtotal_vnd" in silver_orders.columns
        else gross_rev
    )
    shipping_fee_col = (
        F.col("o.shipping_fee_vnd")
        if "shipping_fee_vnd" in silver_orders.columns
        else F.lit(0).cast("bigint")
    )
    channel_col = (
        F.col("o.channel")
        if "channel" in silver_orders.columns
        else (
            F.when(F.col("o.store_id").isNotNull() & (F.col("o.store_id") > 0), F.lit("pos")).otherwise(F.lit("online"))
        )
    )

    return (
        joined.select(
            F.col("o.order_id"),
            F.col("o.order_number"),
            F.col("o.customer_id").alias("customer_key"),
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

    return (
        base_df.select(
            F.col("oi.order_item_id"),
            F.col("oi.order_id"),
            F.date_format(F.col("o.created_at"), "yyyyMMdd").cast("int").alias("order_date_key"),
            F.col("o.customer_id").alias("customer_key"),
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
    )


def build_fact_shipment(
    silver_shipments: DataFrame,
    run_id: str,
) -> DataFrame:
    s = silver_shipments
    duration_expr = F.when(
        F.col("delivered_at").isNotNull() & F.col("dispatched_at").isNotNull(),
        F.round((F.col("delivered_at").cast("long") - F.col("dispatched_at").cast("long")) / 60.0, 2),
    ).when(
        F.col("failed_at").isNotNull() & F.col("dispatched_at").isNotNull(),
        F.round((F.col("failed_at").cast("long") - F.col("dispatched_at").cast("long")) / 60.0, 2),
    ).otherwise(None)

    on_time_expr = (
        F.when(
            F.col("delivered_at").isNotNull() & F.col("estimated_delivery_at").isNotNull(),
            F.col("delivered_at") <= F.col("estimated_delivery_at"),
        ).otherwise(None)
        if "estimated_delivery_at" in silver_shipments.columns
        else F.lit(True)
    )

    cod_expected_col = (
        F.col("cod_amount_expected_vnd")
        if "cod_amount_expected_vnd" in silver_shipments.columns
        else F.col("cod_amount_vnd")
    )
    cod_collected_col = (
        F.col("cod_amount_collected_vnd")
        if "cod_amount_collected_vnd" in silver_shipments.columns
        else F.col("cod_collected_vnd")
    )

    return (
        s.select(
            F.col("shipment_id"),
            F.col("shipment_code"),
            F.col("order_id"),
            F.col("delivery_staff_id").alias("staff_key"),
            F.date_format(F.col("created_at"), "yyyyMMdd").cast("int").alias("shipment_date_key"),
            F.to_date(F.col("created_at")).alias("shipment_date"),
            F.col("status"),
            F.col("attempt_count"),
            (F.col("status") == "failed").alias("is_boom"),
            (F.col("status") == "delivered").alias("is_delivered"),
            cod_expected_col.alias("cod_amount_expected_vnd"),
            F.coalesce(cod_collected_col, F.lit(0)).alias("cod_amount_collected_vnd"),
            duration_expr.alias("delivery_duration_minutes"),
            on_time_expr.alias("is_on_time"),
            F.current_timestamp().alias("_gold_ingested_at"),
            F.lit(run_id).alias("_source_run_id"),
        )
    )


def build_fact_return_exchange(
    silver_return_requests: DataFrame,
    silver_return_items: DataFrame,
    run_id: str,
) -> DataFrame:
    rr = silver_return_requests.alias("rr")
    ri = silver_return_items.alias("ri")

    return_number_col = (
        F.col("rr.return_number")
        if "return_number" in silver_return_requests.columns
        else F.col("rr.return_code")
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
    reason_col = (
        F.col("rr.reason")
        if "reason" in silver_return_requests.columns
        else F.col("rr.customer_reason")
    )

    return (
        ri.join(rr, F.col("ri.return_id") == F.col("rr.return_id"), "inner")
        .select(
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
    )


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

    return (
        joined.select(
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
    )


# ==========================================
# 3. DATA MARTS BUILDERS
# ==========================================

def build_mart_sales_daily(
    fact_order: DataFrame,
    fact_order_item: DataFrame,
    dim_product: DataFrame,
    run_id: str,
) -> DataFrame:
    fo = fact_order.alias("fo")
    foi = fact_order_item.alias("foi")
    dp = dim_product.alias("dp")

    orders_enriched = (
        foi.join(fo, F.col("foi.order_id") == F.col("fo.order_id"), "inner")
        .join(dp, F.col("foi.product_key") == F.col("dp.product_key"), "left")
    )

    delivered_qty = F.when(F.col("fo.is_delivered"), F.col("foi.quantity")).otherwise(0)
    delivered_rev = F.when(F.col("fo.is_delivered"), F.col("foi.item_total_vnd")).otherwise(0)
    delivered_cost = F.when(F.col("fo.is_delivered"), F.col("foi.item_cost_vnd")).otherwise(0)
    delivered_profit = F.when(F.col("fo.is_delivered"), F.col("foi.item_profit_vnd")).otherwise(0)

    delivered_order_expr = F.when(F.col("fo.is_delivered"), F.col("fo.order_id"))
    boom_order_expr = F.when(F.col("fo.is_boom"), F.col("fo.order_id"))

    grouped = (
        orders_enriched.groupBy(
            F.col("fo.order_date"),
            F.col("fo.channel"),
            F.col("fo.store_key"),
            F.coalesce(F.col("dp.category_id"), F.lit(0)).alias("category_id"),
            F.coalesce(F.col("dp.category_name"), F.lit("Unknown")).alias("category_name"),
        )
        .agg(
            F.countDistinct("fo.order_id").alias("total_orders"),
            F.countDistinct(delivered_order_expr).alias("successful_orders"),
            F.countDistinct(boom_order_expr).alias("boom_orders"),
            F.sum(delivered_qty).alias("items_sold"),
            F.sum(delivered_rev).alias("gross_revenue_vnd"),
            F.sum(delivered_cost).alias("cogs_vnd"),
            F.sum(delivered_profit).alias("gross_profit_vnd"),
        )
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


def build_mart_logistics_performance(
    fact_shipment: DataFrame,
    dim_delivery_staff: DataFrame,
    run_id: str,
) -> DataFrame:
    fs = fact_shipment.alias("fs")
    ds = dim_delivery_staff.alias("ds")

    joined = fs.join(ds, F.col("fs.staff_key") == F.col("ds.staff_key"), "left")

    grouped = (
        joined.groupBy(
            F.col("fs.shipment_date"),
            F.col("fs.staff_key"),
            F.coalesce(F.col("ds.staff_code"), F.lit("Unknown")).alias("staff_code"),
            F.coalesce(F.col("ds.assigned_city_id"), F.lit(0)).alias("assigned_city_id"),
            F.coalesce(F.col("ds.assigned_city_name"), F.lit("Unknown")).alias("assigned_city_name"),
        )
        .agg(
            F.count("*").alias("total_shipments"),
            F.sum(F.when(F.col("fs.status") == "delivered", 1).otherwise(0)).alias("delivered_count"),
            F.sum(F.when(F.col("fs.is_boom"), 1).otherwise(0)).alias("boom_count"),
            F.sum(F.when(F.col("fs.is_on_time") == True, 1).otherwise(0)).alias("on_time_count"),
            F.round(F.avg("fs.delivery_duration_minutes"), 2).alias("avg_duration_minutes"),
            F.sum(F.coalesce(F.col("fs.cod_amount_collected_vnd"), F.lit(0))).alias("total_cod_collected_vnd"),
        )
    )

    boom_rate_expr = F.when(
        F.col("total_shipments") > 0,
        F.round((F.col("boom_count") / F.col("total_shipments")) * 100.0, 2),
    ).otherwise(0.0)

    on_time_rate_expr = F.when(
        F.col("delivered_count") > 0,
        F.round((F.col("on_time_count") / F.col("delivered_count")) * 100.0, 2),
    ).otherwise(0.0)

    return (
        grouped.withColumn("boom_rate_pct", boom_rate_expr)
        .withColumn("on_time_rate_pct", on_time_rate_expr)
        .withColumn("_gold_ingested_at", F.current_timestamp())
        .withColumn("_source_run_id", F.lit(run_id))
        .select(
            "shipment_date",
            "staff_key",
            "staff_code",
            "assigned_city_id",
            "assigned_city_name",
            "total_shipments",
            "delivered_count",
            "boom_count",
            "boom_rate_pct",
            "on_time_count",
            "on_time_rate_pct",
            "avg_duration_minutes",
            "total_cod_collected_vnd",
            "_gold_ingested_at",
            "_source_run_id",
        )
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
