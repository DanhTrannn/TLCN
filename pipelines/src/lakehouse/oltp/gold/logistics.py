from __future__ import annotations

from pyspark.sql import DataFrame, functions as F


def build_fact_shipment(
    silver_shipments: DataFrame,
    run_id: str,
) -> DataFrame:
    s = silver_shipments
    duration_expr = (
        F.when(
            F.col("delivered_at").isNotNull() & F.col("dispatched_at").isNotNull(),
            F.round((F.col("delivered_at").cast("long") - F.col("dispatched_at").cast("long")) / 60.0, 2),
        )
        .when(
            F.col("failed_at").isNotNull() & F.col("dispatched_at").isNotNull(),
            F.round((F.col("failed_at").cast("long") - F.col("dispatched_at").cast("long")) / 60.0, 2),
        )
        .otherwise(None)
    )

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

    return s.select(
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


def build_mart_logistics_performance(
    fact_shipment: DataFrame,
    dim_delivery_staff: DataFrame,
    run_id: str,
) -> DataFrame:
    fs = fact_shipment.alias("fs")
    ds = dim_delivery_staff.alias("ds")

    joined = fs.join(ds, F.col("fs.staff_key") == F.col("ds.staff_key"), "left")

    grouped = joined.groupBy(
        F.col("fs.shipment_date"),
        F.col("fs.staff_key"),
        F.coalesce(F.col("ds.staff_code"), F.lit("Unknown")).alias("staff_code"),
        F.coalesce(F.col("ds.assigned_city_id"), F.lit(0)).alias("assigned_city_id"),
        F.coalesce(F.col("ds.assigned_city_name"), F.lit("Unknown")).alias("assigned_city_name"),
    ).agg(
        F.count("*").alias("total_shipments"),
        F.sum(F.when(F.col("fs.status") == "delivered", 1).otherwise(0)).alias("delivered_count"),
        F.sum(F.when(F.col("fs.is_boom"), 1).otherwise(0)).alias("boom_count"),
        F.sum(F.when(F.col("fs.is_on_time") == True, 1).otherwise(0)).alias("on_time_count"),
        F.round(F.avg("fs.delivery_duration_minutes"), 2).alias("avg_duration_minutes"),
        F.sum(F.coalesce(F.col("fs.cod_amount_collected_vnd"), F.lit(0))).alias("total_cod_collected_vnd"),
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
