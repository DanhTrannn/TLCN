"""add admin role and admin transition source

Revision ID: 0002_admin_console
Revises: 0001_initial_schema
Create Date: 2026-07-24
"""

from alembic import op
import sqlalchemy as sa

revision = "0002_admin_console"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "customers",
        sa.Column("role", sa.String(16), nullable=False, server_default=sa.text("'customer'")),
    )
    op.create_check_constraint(
        "ck_customers_role",
        "customers",
        "role in ('customer','admin')",
    )
    op.create_index("ix_customers_role_status_id", "customers", ["role", "status", "customer_id"])

    op.drop_constraint(
        "ck_order_status_history_transition_source",
        "order_status_history",
        type_="check",
    )
    op.create_check_constraint(
        "ck_order_status_history_transition_source",
        "order_status_history",
        "transition_source in ('checkout','internal_endpoint','generator','system','admin')",
    )


def downgrade() -> None:
    op.execute(
        "UPDATE order_status_history "
        "SET transition_source = 'internal_endpoint' "
        "WHERE transition_source = 'admin'"
    )
    op.drop_constraint(
        "ck_order_status_history_transition_source",
        "order_status_history",
        type_="check",
    )
    op.create_check_constraint(
        "ck_order_status_history_transition_source",
        "order_status_history",
        "transition_source in ('checkout','internal_endpoint','generator','system')",
    )
    op.drop_index("ix_customers_role_status_id", table_name="customers")
    op.drop_constraint("ck_customers_role", "customers", type_="check")
    op.drop_column("customers", "role")
