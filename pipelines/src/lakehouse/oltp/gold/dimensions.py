from __future__ import annotations

from pyspark.sql import DataFrame, SparkSession, functions as F
from lakehouse.sql import literal, render_sql


def build_dim_date(
    spark: SparkSession,
    start_date: str = "2025-01-01",
    end_date: str = "2027-12-31",
) -> DataFrame:
    df = spark.sql(
        render_sql("spark/gold/date_sequence.sql", start_date=literal(start_date), end_date=literal(end_date))
    )
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
        F.col("p.base_price_vnd") if "base_price_vnd" in silver_products.columns else F.lit(0).cast("bigint")
    )
    return p.join(c, F.col("p.category_id") == F.col("c.category_id"), "left").select(
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
    color_col = F.col("v.color") if "color" in silver_product_variants.columns else F.col("v.color_code")
    size_col = F.col("v.size") if "size" in silver_product_variants.columns else F.col("v.size_code")
    return v.join(p, F.col("v.product_id") == F.col("p.product_id"), "left").select(
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


def build_dim_store(
    silver_stores: DataFrame,
    silver_cities: DataFrame,
    run_id: str,
) -> DataFrame:
    s = silver_stores.alias("s")
    c = silver_cities.alias("c")
    return s.join(c, F.col("s.city_id") == F.col("c.city_id"), "left").select(
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
        else (F.col("d.vehicle_plate") if "vehicle_plate" in silver_delivery_staff.columns else F.lit("motorbike"))
    )

    return d.join(c, assigned_city_col == F.col("c.city_id"), "left").select(
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
            F.col("cu.email_normalized_pseudonymized")
            if "email_normalized_pseudonymized" in silver_customers.columns
            else F.lit(None).cast("string")
        )
    )
    phone_col = (
        F.col("cu.phone_pseudonymized")
        if "phone_pseudonymized" in silver_customers.columns
        else (F.col("cu.phone") if "phone" in silver_customers.columns else F.lit(None).cast("string"))
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
                else (F.col("cu.full_name") if "full_name" in silver_customers.columns else F.lit("Unknown"))
            )
        )
    )

    return cu.join(ci, F.col("cu.city_id") == F.col("ci.city_id"), "left").select(
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
