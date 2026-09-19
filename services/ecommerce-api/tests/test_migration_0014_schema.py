"""Test that migration 0014 and SQLAlchemy models define the expected schema."""

from sqlalchemy import CheckConstraint

from app.db.base import Base


def _table_names() -> set[str]:
    return set(Base.metadata.tables.keys())


def _column_names(table_name: str) -> list[str]:
    table = Base.metadata.tables[table_name]
    return [col.name for col in table.columns]


def _check_constraint_names(table_name: str) -> set[str]:
    table = Base.metadata.tables[table_name]
    return {
        constraint.name
        for constraint in table.constraints
        if isinstance(constraint, CheckConstraint) and constraint.name is not None
    }


def test_delivery_staff_table_exists() -> None:
    assert "delivery_staff" in _table_names()
    cols = _column_names("delivery_staff")
    assert "staff_id" in cols
    assert "public_id" in cols
    assert "full_name" in cols
    assert "phone" in cols
    assert "vehicle_plate" in cols
    assert "is_active" in cols


def test_shipments_table_exists() -> None:
    assert "shipments" in _table_names()
    cols = _column_names("shipments")
    assert "shipment_id" in cols
    assert "public_id" in cols
    assert "shipment_code" in cols
    assert "order_id" in cols
    assert "delivery_staff_id" in cols
    assert "status" in cols
    assert "attempt_count" in cols
    assert "cod_amount_vnd" in cols
    assert "cod_collected_vnd" in cols
    assert "dispatched_at" in cols
    assert "delivered_at" in cols
    assert "failed_at" in cols
    assert "failure_reason" in cols


def test_return_requests_table_exists() -> None:
    assert "return_requests" in _table_names()
    cols = _column_names("return_requests")
    assert "return_id" in cols
    assert "public_id" in cols
    assert "return_code" in cols
    assert "order_id" in cols
    assert "customer_id" in cols
    assert "action_type" in cols
    assert "status" in cols
    assert "customer_reason" in cols


def test_return_items_table_exists() -> None:
    assert "return_items" in _table_names()
    cols = _column_names("return_items")
    assert "return_item_id" in cols
    assert "public_id" in cols
    assert "return_id" in cols
    assert "order_item_id" in cols
    assert "variant_id" in cols
    assert "quantity" in cols
    assert "exchange_variant_id" in cols
    assert "refund_amount_vnd" in cols
    assert "inspection_status" in cols


def test_inventory_transactions_table_exists() -> None:
    assert "inventory_transactions" in _table_names()
    cols = _column_names("inventory_transactions")
    assert "transaction_id" in cols
    assert "public_id" in cols
    assert "variant_id" in cols
    assert "location_type" in cols
    assert "store_id" in cols
    assert "movement_type" in cols
    assert "quantity_delta" in cols
    assert "reference_code" in cols
    assert "notes" in cols


def test_existing_tables_extended_columns() -> None:
    assert "cost_price_vnd" in _column_names("product_variants")
    assert "cost_price_vnd" in _column_names("order_items")
    assert "payment_method" in _column_names("orders")
    assert "is_cod_blocked" in _column_names("customers")
    assert "boom_count" in _column_names("customers")
