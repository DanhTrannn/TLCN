"""Add POS fields to orders table.

Revision ID: 0011
Revises: 0010
Create Date: 2026-09-15
"""
from alembic import op
import sqlalchemy as sa

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("orders", sa.Column("store_id", sa.BigInteger(), nullable=True))
    op.add_column("orders", sa.Column("channel", sa.String(16), nullable=False, server_default="online"))
    op.add_column("orders", sa.Column("staff_id", sa.BigInteger(), nullable=True))
    op.create_index("ix_orders_channel", "orders", ["channel"])
    op.create_index("ix_orders_store_id", "orders", ["store_id"])
    op.create_foreign_key("fk_orders_store", "orders", "stores", ["store_id"], ["store_id"])

def downgrade() -> None:
    op.drop_constraint("fk_orders_store", "orders", type_="foreignkey")
    op.drop_index("ix_orders_store_id")
    op.drop_index("ix_orders_channel")
    op.drop_column("orders", "staff_id")
    op.drop_column("orders", "channel")
    op.drop_column("orders", "store_id")
