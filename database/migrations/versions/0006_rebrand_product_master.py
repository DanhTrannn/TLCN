"""rebrand mutable product master copy to D&K

Revision ID: 0006_rebrand_product_master
Revises: 0005_order_lifecycle
Create Date: 2026-08-02
"""

from alembic import op


revision = "0006_rebrand_product_master"
down_revision = "0005_order_lifecycle"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "UPDATE products SET name = REPLACE(name, ' - NS-', ' - DK-') "
        "WHERE name LIKE '% - NS-%'"
    )
    op.execute(
        "UPDATE products SET description = REPLACE(description, 'NÉT Studio', 'D&K') "
        "WHERE description LIKE '%NÉT Studio%'"
    )


def downgrade() -> None:
    pass
