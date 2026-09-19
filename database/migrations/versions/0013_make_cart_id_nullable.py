"""make orders.cart_id nullable for POS orders

Revision ID: 0013
Revises: 0012
Create Date: 2026-09-16
"""
from alembic import op
from sqlalchemy.dialects import mysql

revision = "0013"
down_revision = "0012"


def upgrade() -> None:
    op.alter_column("orders", "cart_id", existing_type=mysql.BIGINT(unsigned=True), nullable=True)


def downgrade() -> None:
    op.alter_column("orders", "cart_id", existing_type=mysql.BIGINT(unsigned=True), nullable=False)
