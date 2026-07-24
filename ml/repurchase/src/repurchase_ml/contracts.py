NUMERICAL_FEATURES = (
    "days_since_last_paid_order",
    "paid_order_count_30d",
    "paid_order_count_90d",
    "paid_order_count_180d",
    "paid_revenue_30d",
    "paid_revenue_90d",
    "paid_revenue_180d",
    "avg_order_value_180d",
    "paid_units_180d",
    "distinct_category_count_180d",
    "days_between_last_two_paid_orders",
    "session_count_30d",
    "product_view_count_30d",
    "add_to_cart_count_30d",
    "begin_checkout_count_30d",
    "days_since_last_session",
    "view_to_cart_ratio_30d",
    "payment_failed_count_90d",
    "checkout_to_paid_ratio_90d",
    "days_since_first_paid_order",
)

TARGET_COLUMN = "repurchased_30d"
GRAIN_COLUMNS = ("customer_key", "as_of_date", "feature_schema_version")

