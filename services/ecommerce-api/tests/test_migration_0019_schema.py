"""Regression tests for Migration 0019 schema, constraints, and audit fields."""

from sqlalchemy import CheckConstraint

import app.models  # noqa: F401
from app.db.base import Base


def _column_names(table_name: str) -> set[str]:
    table = Base.metadata.tables[table_name]
    return {col.name for col in table.columns}


def _check_sql(table_name: str, constraint_name: str) -> str:
    table = Base.metadata.tables[table_name]
    constraint = next(
        item
        for item in table.constraints
        if isinstance(item, CheckConstraint) and item.name.endswith(constraint_name)
    )
    return str(constraint.sqltext)


def test_shipment_attempts_table_in_metadata() -> None:
    assert "shipment_attempts" in Base.metadata.tables
    cols = _column_names("shipment_attempts")
    expected = {
        "attempt_id",
        "public_id",
        "shipment_id",
        "attempt_number",
        "delivery_staff_id",
        "status",
        "failure_reason",
        "is_buyer_fault",
        "idempotency_key",
        "attempted_at",
        "created_at",
        "updated_at",
    }
    assert expected.issubset(cols)


def test_orders_customer_id_is_nullable() -> None:
    table = Base.metadata.tables["orders"]
    customer_id_col = table.columns["customer_id"]
    assert customer_id_col.nullable is True


def test_orders_pos_channel_constraint() -> None:
    sql = _check_sql("orders", "pos_channel")
    assert "channel != 'pos'" in sql
    assert "store_id is not null" in sql
    assert "staff_id is not null" in sql


def test_orders_channel_payment_constraint() -> None:
    sql = _check_sql("orders", "channel_payment")
    assert "'pos'" in sql
    assert "'cash'" in sql
    assert "'card'" in sql
    assert "'vietqr'" in sql
    assert "'online'" in sql
    assert "'cod'" in sql


def test_orders_cod_pending_no_paid_at_constraint() -> None:
    sql = _check_sql("orders", "cod_pending_no_paid_at")
    assert "payment_method = 'cod'" in sql
    assert "paid_at is not null" in sql


def test_shipments_cod_collected_limit_constraint() -> None:
    sql = _check_sql("shipments", "cod_collected_limit")
    assert "cod_collected_vnd <= cod_amount_vnd" in sql


def test_customers_has_cod_reinstatement_audit_fields() -> None:
    cols = _column_names("customers")
    assert "cod_reinstated_at" in cols
    assert "cod_reinstated_by" in cols
    assert "cod_reinstatement_reason" in cols


def test_inventory_transactions_movement_type_includes_order_cancellation() -> None:
    sql = _check_sql("inventory_transactions", "ck_inv_tx_movement_type")
    assert "'order_cancellation'" in sql
