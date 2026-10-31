from __future__ import annotations

from pyspark.sql import DataFrame, functions as F


def _validate_rows(df: DataFrame, table_name: str) -> tuple[DataFrame, DataFrame]:
    violations = []

    if "_missing_primary_key" in df.columns:
        violations.append(F.when(F.col("_missing_primary_key").isNotNull(), F.lit("missing_primary_key")))

    required_columns = {
        "customers": ("role", "status"),
        "categories": ("code", "name"),
        "products": ("category_id", "name"),
        "product_variants": ("product_id", "sku", "price_vnd"),
        "orders": ("status", "subtotal_vnd", "total_vnd", "created_at"),
        "order_items": ("order_id", "variant_id", "quantity", "unit_price_vnd", "line_total_vnd"),
        "payments": ("order_id", "status", "amount_vnd"),
        "refunds": ("payment_id", "status", "amount_vnd"),
        "inventory": ("variant_id", "on_hand"),
        "store_inventory": ("store_id", "variant_id", "on_hand"),
        "shipments": ("order_id", "status"),
        "return_requests": ("order_id", "customer_id", "action_type", "status"),
        "return_items": ("return_id", "order_item_id", "variant_id", "quantity"),
        "inbound_receipts": ("status", "total_items_count", "total_cost_vnd"),
        "inbound_receipt_items": ("receipt_id", "variant_id", "quantity", "unit_cost_vnd", "total_cost_vnd"),
    }
    for column_name in required_columns.get(table_name, ()):
        if column_name in df.columns:
            violations.append(F.when(F.col(column_name).isNull(), F.lit(f"missing_required_{column_name}")))

    if table_name == "product_variants":
        violations.append(F.when(F.col("price_vnd") < 0, F.lit("negative_price")))
    if table_name == "orders":
        valid_statuses = {
            "pending_payment",
            "paid",
            "payment_failed",
            "confirmed",
            "shipping",
            "delivered",
            "completed",
            "cancelled",
            "failed_delivery",
            "returned",
        }
        violations.append(F.when(~F.col("status").isin(*valid_statuses), F.lit("invalid_order_status")))
        for amount_col in ("subtotal_vnd", "discount_amount_vnd", "shipping_fee_vnd", "total_vnd"):
            if amount_col in df.columns:
                violations.append(F.when(F.col(amount_col) < 0, F.lit(f"negative_{amount_col}")))
        order_total_columns = {"subtotal_vnd", "discount_amount_vnd", "shipping_fee_vnd", "total_vnd"}
        if order_total_columns.issubset(df.columns):
            violations.append(
                F.when(
                    F.col("subtotal_vnd") - F.col("discount_amount_vnd") + F.col("shipping_fee_vnd")
                    != F.col("total_vnd"),
                    F.lit("order_total_mismatch"),
                )
            )
    if table_name in ("cart_items", "order_items"):
        violations.append(F.when(F.col("quantity") <= 0, F.lit("invalid_quantity")))
    if table_name == "order_items":
        for amount_col in ("unit_price_vnd", "cost_price_vnd", "line_total_vnd"):
            if amount_col in df.columns:
                violations.append(F.when(F.col(amount_col) < 0, F.lit(f"negative_{amount_col}")))
        if {"quantity", "unit_price_vnd", "line_total_vnd"}.issubset(df.columns):
            violations.append(
                F.when(
                    F.col("quantity") * F.col("unit_price_vnd") != F.col("line_total_vnd"),
                    F.lit("order_item_total_mismatch"),
                )
            )
    if table_name == "payments":
        valid_payment_statuses = {"succeeded", "failed", "pending"}
        violations.append(F.when(~F.col("status").isin(*valid_payment_statuses), F.lit("invalid_payment_status")))
        if "amount_vnd" in df.columns:
            violations.append(F.when(F.col("amount_vnd") < 0, F.lit("negative_payment")))
    if table_name == "refunds":
        violations.append(F.when(F.col("amount_vnd") < 0, F.lit("negative_refund")))
        if "status" in df.columns:
            violations.append(F.when(~F.col("status").isin("succeeded", "failed"), F.lit("invalid_refund_status")))
    if table_name == "coupons":
        violations.append(
            F.when(
                (F.col("discount_type") == "percentage")
                & ((F.col("discount_value") < 1) | (F.col("discount_value") > 100)),
                F.lit("invalid_discount_percentage"),
            )
        )
    if table_name == "product_reviews":
        violations.append(F.when((F.col("rating") < 1) | (F.col("rating") > 5), F.lit("invalid_rating")))
    if table_name in ("inventory", "store_inventory"):
        violations.append(F.when(F.col("on_hand") < 0, F.lit("negative_inventory")))
    if table_name == "shipments":
        valid_shipment_statuses = {
            "assigned",
            "picked_up",
            "in_transit",
            "delivered",
            "failed",
            "returned_to_warehouse",
        }
        violations.append(F.when(~F.col("status").isin(*valid_shipment_statuses), F.lit("invalid_shipment_status")))
    if table_name == "return_requests":
        valid_return_actions = {"exchange", "refund"}
        violations.append(F.when(~F.col("action_type").isin(*valid_return_actions), F.lit("invalid_return_action")))
    if table_name == "inventory_transactions":
        valid_movement_types = {
            "inbound",
            "outbound_order",
            "outbound_pos",
            "transfer_to_store",
            "transfer_received",
            "return_boom",
            "return_customer",
            "exchange_out",
            "adjustment",
        }
        violations.append(F.when(~F.col("movement_type").isin(*valid_movement_types), F.lit("invalid_movement_type")))
    if table_name == "inbound_receipts":
        violations.append(F.when(F.col("total_cost_vnd") < 0, F.lit("negative_total_cost")))
        violations.append(F.when(F.col("total_items_count") < 0, F.lit("negative_items_count")))
    if table_name == "inbound_receipt_items":
        violations.append(F.when(F.col("quantity") <= 0, F.lit("invalid_quantity")))
        violations.append(F.when(F.col("unit_cost_vnd") < 0, F.lit("negative_unit_cost")))
        violations.append(F.when(F.col("total_cost_vnd") < 0, F.lit("negative_total_cost")))
        if {"quantity", "unit_cost_vnd", "total_cost_vnd"}.issubset(df.columns):
            violations.append(
                F.when(
                    F.col("quantity") * F.col("unit_cost_vnd") != F.col("total_cost_vnd"),
                    F.lit("inbound_item_total_mismatch"),
                )
            )

    if not violations:
        return df, df.limit(0)

    violation_array = F.array_compact(F.array(*violations))
    df_with_violation = df.withColumn("_violation_types", violation_array).withColumn(
        "_violation_type", F.concat_ws("|", F.col("_violation_types"))
    )
    violating = df_with_violation.filter(F.size(F.col("_violation_types")) > 0)
    valid = df_with_violation.filter(F.size(F.col("_violation_types")) == 0).drop("_violation_type", "_violation_types")

    return valid, violating
