"""Regression tests for POS payment and initial completed-order constraints."""

from sqlalchemy import CheckConstraint

import app.models  # noqa: F401
from app.db.base import Base


def _check_sql(table_name: str, constraint_name: str) -> str:
    table = Base.metadata.tables[table_name]
    constraint = next(
        item
        for item in table.constraints
        if isinstance(item, CheckConstraint) and item.name.endswith(constraint_name)
    )
    return str(constraint.sqltext)


def test_orders_accepts_pos_payment_methods() -> None:
    sql = _check_sql("orders", "payment_method")
    assert "'cash'" in sql
    assert "'card'" in sql


def test_pos_order_can_start_completed() -> None:
    sql = _check_sql("order_status_history", "valid_transition")
    assert "from_status is null" in sql
    assert "'completed'" in sql
