from lakehouse.silver_ddl import (
    SILVER_TABLE_DDL,
    SILVER_QUARANTINE_DDL,
    SILVER_QUARANTINE_TABLE,
    ensure_silver_namespaces,
    ensure_silver_tables,
)


def test_all_sixteen_tables_have_ddl():
    expected_tables = {
        "silver_customers", "silver_categories", "silver_products",
        "silver_product_variants", "silver_carts", "silver_cart_items",
        "silver_wishlist_items", "silver_orders", "silver_order_items",
        "silver_payments", "silver_order_status_history", "silver_inventory",
        "silver_coupons", "silver_coupon_redemptions", "silver_refunds",
        "silver_product_reviews",
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
