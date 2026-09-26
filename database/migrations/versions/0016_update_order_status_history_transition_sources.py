"""update order_status_history transition_source check constraint

Revision ID: 0016
Revises: 0015
Create Date: 2026-09-26
"""

from alembic import op
import sqlalchemy as sa

revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None

ALLOWED_SOURCES = (
    "'checkout','internal_endpoint','generator','system','admin','customer',"
    "'admin_dispatch','admin_deliver','admin_failed_delivery','admin_complete','admin_return'"
)


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "mysql":
        inspector = sa.inspect(bind)
        check_names = {c["name"] for c in inspector.get_check_constraints("order_status_history") if c.get("name")}
        for ck in check_names:
            if "transition_source" in ck or "transiti" in ck:
                op.execute(f"ALTER TABLE order_status_history DROP CHECK {ck}")

        op.execute(
            f"ALTER TABLE order_status_history ADD CONSTRAINT ck_order_status_history_transition_source "
            f"CHECK (transition_source in ({ALLOWED_SOURCES}))"
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "mysql":
        inspector = sa.inspect(bind)
        check_names = {c["name"] for c in inspector.get_check_constraints("order_status_history") if c.get("name")}
        for ck in check_names:
            if "transition_source" in ck:
                op.execute(f"ALTER TABLE order_status_history DROP CHECK {ck}")

        op.execute(
            "ALTER TABLE order_status_history ADD CONSTRAINT ck_order_status_history_transition_source "
            "CHECK (transition_source in ('checkout','internal_endpoint','generator','system','admin','customer'))"
        )
