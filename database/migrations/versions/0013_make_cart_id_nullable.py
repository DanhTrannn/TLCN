"""make orders.cart_id nullable for POS orders

Revision ID: 0013
Revises: 0012
Create Date: 2026-09-16
"""
from alembic import op
import sqlalchemy as sa

revision = "0013"
down_revision = "0012"


def upgrade() -> None:
    op.alter_column("orders", "cart_id", existing_type=sa.BigInteger(), nullable=True)


def downgrade() -> None:
    op.alter_column("orders", "cart_id", existing_type=sa.BigInteger(), nullable=False)
