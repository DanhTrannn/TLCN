"""add index on product_variants.sku for pos search

Revision ID: 0012
Revises: 0011
Create Date: 2026-09-15
"""
from alembic import op

revision = "0012"
down_revision = "0011"


def upgrade() -> None:
    op.create_index("ix_product_variants_sku", "product_variants", ["sku"])


def downgrade() -> None:
    op.drop_index("ix_product_variants_sku", table_name="product_variants")
