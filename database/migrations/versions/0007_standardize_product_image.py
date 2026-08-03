"""standardize product image URL

Revision ID: 0007_standardize_product_image
Revises: 0006_rebrand_product_master
Create Date: 2026-08-03
"""

from alembic import op


revision = "0007_standardize_product_image"
down_revision = "0006_rebrand_product_master"
branch_labels = None
depends_on = None


PRODUCT_IMAGE_URL = "https://sixdo.vn/modules/uniform/assets/image/aotruoc.webp"


def upgrade() -> None:
    escaped_url = PRODUCT_IMAGE_URL.replace("'", "''")
    op.execute(f"UPDATE products SET image_url = '{escaped_url}'")


def downgrade() -> None:
    pass
