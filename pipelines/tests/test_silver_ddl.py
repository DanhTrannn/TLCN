from lakehouse.oltp.silver_ddl import (
    SILVER_TABLE_DDL,
    SILVER_QUARANTINE_DDL,
    SILVER_QUARANTINE_TABLE,
    ensure_silver_namespaces,
    ensure_silver_tables,
)


def test_all_tables_have_ddl():
    expected_tables = {
        "silver_customers", "silver_categories", "silver_products",
        "silver_product_variants", "silver_carts", "silver_cart_items",
        "silver_wishlist_items", "silver_orders", "silver_order_items",
        "silver_payments", "silver_order_status_history", "silver_inventory",
        "silver_coupons", "silver_coupon_redemptions", "silver_refunds",
        "silver_product_reviews",
        "silver_cities", "silver_stores", "silver_store_inventory",
        "silver_delivery_staff", "silver_shipments", "silver_return_requests",
        "silver_return_items", "silver_inventory_transactions",
        "silver_inbound_receipts", "silver_inbound_receipt_items",
    }
    assert set(SILVER_TABLE_DDL.keys()) == expected_tables


def test_quarantine_ddl_exists():
    assert SILVER_QUARANTINE_DDL is not None
    assert "CREATE TABLE IF NOT EXISTS" in SILVER_QUARANTINE_DDL
    assert "lakehouse.quarantine.silver_oltp_violations" in SILVER_QUARANTINE_DDL


def test_quarantine_table_constant():
    assert SILVER_QUARANTINE_TABLE == "lakehouse.quarantine.silver_oltp_violations"


def test_all_ddl_use_lakehouse_catalog():
    for name, ddl in SILVER_TABLE_DDL.items():
        assert "lakehouse.silver." in ddl, f"{name} missing lakehouse catalog"
    assert "lakehouse.quarantine." in SILVER_QUARANTINE_DDL


def test_customers_has_pii_columns():
    ddl = SILVER_TABLE_DDL["silver_customers"]
    assert "email_pseudonymized" in ddl
    assert "phone_pseudonymized" in ddl
    assert "full_name_pseudonymized" in ddl
    assert "_pii_pseudonymized_at" in ddl


def test_all_tables_have_updated_at():
    for name, ddl in SILVER_TABLE_DDL.items():
        assert "updated_at" in ddl, f"{name} missing updated_at"


def test_append_only_tables_have_created_at():
    append_only = [
        "silver_order_items", "silver_payments",
        "silver_order_status_history", "silver_refunds",
    ]
    for name in append_only:
        ddl = SILVER_TABLE_DDL[name]
        assert "created_at" in ddl, f"{name} missing created_at"


def test_all_tables_have_metadata_columns():
    for name, ddl in SILVER_TABLE_DDL.items():
        assert "_silver_ingested_at" in ddl, f"{name} missing _silver_ingested_at"
        assert "_source_bronze_run_id" in ddl, f"{name} missing _source_bronze_run_id"


def test_inbound_tables_ddl_columns():
    receipts_ddl = SILVER_TABLE_DDL["silver_inbound_receipts"]
    for col in [
        "receipt_id", "public_id", "receipt_code", "batch_name",
        "status", "total_items_count", "total_cost_vnd", "notes",
        "created_by_customer_id", "created_at", "updated_at",
    ]:
        assert col in receipts_ddl, f"silver_inbound_receipts missing {col}"

    items_ddl = SILVER_TABLE_DDL["silver_inbound_receipt_items"]
    for col in [
        "item_id", "public_id", "receipt_id", "variant_id",
        "quantity", "unit_cost_vnd", "total_cost_vnd",
        "previous_cost_price_vnd", "new_cost_price_vnd", "created_at",
    ]:
        assert col in items_ddl, f"silver_inbound_receipt_items missing {col}"


def test_order_items_has_snapshot_columns():
    ddl = SILVER_TABLE_DDL["silver_order_items"]
    assert "product_public_id_snapshot" in ddl
    assert "category_code_snapshot" in ddl


def test_cart_and_wishlist_time_columns():
    cart_ddl = SILVER_TABLE_DDL["silver_cart_items"]
    assert "first_added_at" in cart_ddl

    wishlist_ddl = SILVER_TABLE_DDL["silver_wishlist_items"]
    assert "first_added_at" in wishlist_ddl
    assert "last_added_at" in wishlist_ddl

