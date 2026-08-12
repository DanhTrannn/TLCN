"""add archive metadata to products and coupons

Revision ID: 0008_archive_catalog_promotions
Revises: 0007_standardize_product_image
Create Date: 2026-08-12
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


revision = "0008_archive_catalog_promotions"
down_revision = "0007_standardize_product_image"
branch_labels = None
depends_on = None


def _add_archive_columns(table_name: str, entity_name: str) -> None:
    op.add_column(
        table_name,
        sa.Column("archived_at", mysql.DATETIME(fsp=6), nullable=True),
    )
    op.add_column(
        table_name,
        sa.Column(
            "archived_by_customer_id",
            mysql.BIGINT(unsigned=True),
            nullable=True,
        ),
    )
    op.add_column(
        table_name,
        sa.Column("archive_reason", sa.String(length=500), nullable=True),
    )
    op.create_foreign_key(
        f"fk_{table_name}_archived_by_customers",
        table_name,
        "customers",
        ["archived_by_customer_id"],
        ["customer_id"],
        ondelete="RESTRICT",
    )
    op.create_check_constraint(
        "archive_metadata_consistency",
        table_name,
        "(archived_at is null and archived_by_customer_id is null and archive_reason is null) "
        "or (archived_at is not null and archived_by_customer_id is not null "
        "and archive_reason is not null and char_length(trim(archive_reason)) >= 3)",
    )
    op.create_check_constraint(
        "archived_not_active",
        table_name,
        "archived_at is null or is_active = 0",
    )
    op.create_index(
        f"ix_{table_name}_archived_at_{entity_name}_id",
        table_name,
        ["archived_at", f"{entity_name}_id"],
    )


def _drop_archive_columns(table_name: str, entity_name: str) -> None:
    op.drop_index(
        f"ix_{table_name}_archived_at_{entity_name}_id",
        table_name=table_name,
    )
    op.drop_constraint(
        f"ck_{table_name}_archived_not_active",
        table_name,
        type_="check",
    )
    op.drop_constraint(
        f"ck_{table_name}_archive_metadata_consistency",
        table_name,
        type_="check",
    )
    op.drop_constraint(
        f"fk_{table_name}_archived_by_customers",
        table_name,
        type_="foreignkey",
    )
    op.drop_column(table_name, "archive_reason")
    op.drop_column(table_name, "archived_by_customer_id")
    op.drop_column(table_name, "archived_at")


def upgrade() -> None:
    _add_archive_columns("products", "product")
    _add_archive_columns("coupons", "coupon")


def downgrade() -> None:
    _drop_archive_columns("coupons", "coupon")
    _drop_archive_columns("products", "product")
