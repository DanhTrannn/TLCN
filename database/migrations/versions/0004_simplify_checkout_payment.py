"""remove checkout payment scenario

Revision ID: 0004_simplify_checkout_payment
Revises: 0003_wishlist
Create Date: 2026-07-28
"""

from alembic import op
import sqlalchemy as sa

revision = "0004_simplify_checkout_payment"
down_revision = "0003_wishlist"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("payments", "simulator_scenario")


def downgrade() -> None:
    op.add_column(
        "payments",
        sa.Column(
            "simulator_scenario",
            sa.String(length=32),
            nullable=False,
            server_default=sa.text("'automatic_success'"),
        ),
    )
