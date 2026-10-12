"""align POS payments and order lifecycle constraints

Revision ID: 0018
Revises: 0017
Create Date: 2026-10-12
"""

import sqlalchemy as sa
from alembic import op

revision = "0018"
down_revision = "0017"
branch_labels = None
depends_on = None


def _drop_matching_checks(table: str, fragments: tuple[str, ...]) -> None:
    bind = op.get_bind()
    checks = sa.inspect(bind).get_check_constraints(table)
    for check in checks:
        name = check.get("name")
        normalized = (name or "").lower()
        if name and any(fragment in normalized for fragment in fragments):
            op.execute(f"ALTER TABLE {table} DROP CHECK {name}")


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "mysql":
        return

    _drop_matching_checks("orders", ("payment_method",))
    op.execute(
        "ALTER TABLE orders ADD CONSTRAINT ck_orders_payment_method "
        "CHECK (payment_method in ('vietqr','cod','cash','card'))"
    )

    _drop_matching_checks("order_status_history", ("valid_transition",))
    op.execute(
        "ALTER TABLE order_status_history ADD CONSTRAINT ck_order_status_history_valid_transition CHECK ("
        "(from_status is null and to_status in "
        "('pending_payment','paid','payment_failed','confirmed','completed')) "
        "or (from_status = 'pending_payment' and to_status in ('paid','payment_failed','cancelled')) "
        "or (from_status = 'paid' and to_status in ('confirmed','cancelled','shipping')) "
        "or (from_status = 'confirmed' and to_status in ('shipping','completed','cancelled','failed_delivery')) "
        "or (from_status = 'shipping' and to_status in ('delivered','failed_delivery','returned')) "
        "or (from_status = 'delivered' and to_status in ('completed','returned')) "
        "or (from_status = 'completed' and to_status = 'returned'))"
    )

    op.add_column("shipments", sa.Column("failed_attempt_1_key", sa.String(64), nullable=True))
    op.add_column("shipments", sa.Column("failed_attempt_2_key", sa.String(64), nullable=True))
    op.add_column("shipments", sa.Column("failed_attempt_3_key", sa.String(64), nullable=True))
    op.create_index(
        "uq_shipments_failed_attempt_1_key", "shipments", ["failed_attempt_1_key"], unique=True
    )
    op.create_index(
        "uq_shipments_failed_attempt_2_key", "shipments", ["failed_attempt_2_key"], unique=True
    )
    op.create_index(
        "uq_shipments_failed_attempt_3_key", "shipments", ["failed_attempt_3_key"], unique=True
    )
    op.create_check_constraint(
        "ck_shipments_attempt_count", "shipments", "attempt_count between 1 and 3"
    )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "mysql":
        return

    op.drop_constraint("ck_shipments_attempt_count", "shipments", type_="check")
    op.drop_index("uq_shipments_failed_attempt_3_key", table_name="shipments")
    op.drop_index("uq_shipments_failed_attempt_2_key", table_name="shipments")
    op.drop_index("uq_shipments_failed_attempt_1_key", table_name="shipments")
    op.drop_column("shipments", "failed_attempt_3_key")
    op.drop_column("shipments", "failed_attempt_2_key")
    op.drop_column("shipments", "failed_attempt_1_key")

    op.execute("UPDATE orders SET payment_method = 'vietqr' WHERE payment_method IN ('cash','card')")
    _drop_matching_checks("orders", ("payment_method",))
    op.execute(
        "ALTER TABLE orders ADD CONSTRAINT ck_orders_payment_method "
        "CHECK (payment_method in ('vietqr','cod'))"
    )

    _drop_matching_checks("order_status_history", ("valid_transition",))
    op.execute(
        "ALTER TABLE order_status_history ADD CONSTRAINT ck_order_status_history_valid_transition CHECK ("
        "(from_status is null and to_status in ('pending_payment','paid','payment_failed','confirmed')) "
        "or (from_status = 'pending_payment' and to_status in ('paid','payment_failed','cancelled')) "
        "or (from_status = 'paid' and to_status in ('confirmed','cancelled','shipping')) "
        "or (from_status = 'confirmed' and to_status in ('shipping','completed','cancelled','failed_delivery')) "
        "or (from_status = 'shipping' and to_status in ('delivered','failed_delivery','returned')) "
        "or (from_status = 'delivered' and to_status in ('completed','returned')) "
        "or (from_status = 'completed' and to_status = 'returned'))"
    )
