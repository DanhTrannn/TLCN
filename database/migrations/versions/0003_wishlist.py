"""add customer wishlist items

Revision ID: 0003_wishlist
Revises: 0002_admin_console
Create Date: 2026-07-27
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision = "0003_wishlist"
down_revision = "0002_admin_console"
branch_labels = None
depends_on = None

TS = sa.text("CURRENT_TIMESTAMP(6)")
TS_ONUPDATE = sa.text("CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)")


def upgrade() -> None:
    op.create_table(
        "wishlist_items",
        sa.Column(
            "wishlist_item_id",
            mysql.BIGINT(unsigned=True),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column("customer_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("product_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("is_present", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("first_added_at", mysql.DATETIME(fsp=6), nullable=False, server_default=TS),
        sa.Column("last_added_at", mysql.DATETIME(fsp=6), nullable=False, server_default=TS),
        sa.Column("removed_at", mysql.DATETIME(fsp=6), nullable=True),
        sa.Column("updated_at", mysql.DATETIME(fsp=6), nullable=False, server_default=TS_ONUPDATE),
        sa.PrimaryKeyConstraint("wishlist_item_id"),
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["customers.customer_id"],
            name="fk_wishlist_items_customer_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.product_id"],
            name="fk_wishlist_items_product_id",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "(is_present = 1 and removed_at is null) "
            "or (is_present = 0 and removed_at is not null)",
            name="ck_wishlist_items_presence_removed_consistency",
        ),
        sa.CheckConstraint(
            "last_added_at >= first_added_at",
            name="ck_wishlist_items_last_added_after_first",
        ),
        sa.CheckConstraint(
            "removed_at is null or removed_at >= last_added_at",
            name="ck_wishlist_items_removed_after_last_added",
        ),
        mysql_engine="InnoDB",
    )
    op.create_index(
        "uq_wishlist_items_customer_id_product_id",
        "wishlist_items",
        ["customer_id", "product_id"],
        unique=True,
    )
    op.create_index(
        "ix_wishlist_items_customer_present_last_added_id",
        "wishlist_items",
        ["customer_id", "is_present", "last_added_at", "wishlist_item_id"],
    )
    op.create_index(
        "ix_wishlist_items_product_id_wishlist_item_id",
        "wishlist_items",
        ["product_id", "wishlist_item_id"],
    )
    op.create_index(
        "ix_wishlist_items_updated_at_wishlist_item_id",
        "wishlist_items",
        ["updated_at", "wishlist_item_id"],
    )


def downgrade() -> None:
    op.drop_table("wishlist_items")
