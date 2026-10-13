"""strengthen inventory ledger and POS invariants

Revision ID: 0020
Revises: 0019
Create Date: 2026-10-13
"""

import sqlalchemy as sa
from alembic import op

revision = "0020"
down_revision = "0019"
branch_labels = None
depends_on = None


def _replace_transition_source_check(*, include_pos: bool) -> None:
    bind = op.get_bind()
    for check in sa.inspect(bind).get_check_constraints("order_status_history"):
        name = check.get("name")
        if name and "transition_source" in name.lower():
            op.execute(f"ALTER TABLE order_status_history DROP CHECK {name}")

    pos_source = ",'pos'" if include_pos else ""
    op.execute(
        "ALTER TABLE order_status_history "
        "ADD CONSTRAINT ck_order_status_history_transition_source CHECK ("
        "transition_source in ("
        "'checkout','internal_endpoint','generator','system','admin','customer'"
        f"{pos_source},'admin_dispatch','admin_deliver','admin_failed_delivery',"
        "'admin_complete','admin_return'))"
    )


def upgrade() -> None:
    _replace_transition_source_check(include_pos=True)
    op.create_check_constraint(
        "ck_inventory_transactions_location_store_consistency",
        "inventory_transactions",
        "(location_type = 'central_warehouse' and store_id is null) or "
        "(location_type = 'store' and store_id is not null)",
    )
    op.create_check_constraint(
        "ck_inventory_transactions_quantity_non_zero",
        "inventory_transactions",
        "quantity_delta != 0",
    )
    op.create_check_constraint(
        "ck_inventory_transactions_movement_direction",
        "inventory_transactions",
        "(movement_type in ('inbound','transfer_received','return_boom','return_customer','order_cancellation') "
        "and quantity_delta > 0) or "
        "(movement_type in ('outbound_order','outbound_pos','transfer_to_store','exchange_out') "
        "and quantity_delta < 0) or movement_type = 'adjustment'",
    )
    op.create_check_constraint(
        "ck_orders_online_customer",
        "orders",
        "channel != 'online' or customer_id is not null",
    )
    op.create_check_constraint(
        "ck_orders_pos_completion",
        "orders",
        "channel != 'pos' or (status = 'completed' and paid_at is not null and completed_at is not null)",
    )


def downgrade() -> None:
    op.drop_constraint("ck_orders_pos_completion", "orders", type_="check")
    op.drop_constraint("ck_orders_online_customer", "orders", type_="check")
    op.drop_constraint(
        "ck_inventory_transactions_movement_direction",
        "inventory_transactions",
        type_="check",
    )
    op.drop_constraint(
        "ck_inventory_transactions_quantity_non_zero",
        "inventory_transactions",
        type_="check",
    )
    op.drop_constraint(
        "ck_inventory_transactions_location_store_consistency",
        "inventory_transactions",
        type_="check",
    )
    _replace_transition_source_check(include_pos=False)
