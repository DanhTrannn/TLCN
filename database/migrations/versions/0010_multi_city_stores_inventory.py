"""add cities, stores, store_inventory tables; extend customer roles

Revision ID: 0010_multi_city_stores_inventory
Revises: 0009_reviews_publish_immediately
Create Date: 2026-09-09
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


revision = "0010_multi_city_stores_inventory"
down_revision = "0009_reviews_publish_immediately"
branch_labels = None
depends_on = None

TS = sa.text("CURRENT_TIMESTAMP(6)")
TS_ONUPDATE = sa.text("CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)")


def upgrade() -> None:
    # 1. cities
    op.create_table(
        "cities",
        sa.Column("city_id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", mysql.DATETIME(fsp=6), nullable=False, server_default=TS),
        sa.Column("updated_at", mysql.DATETIME(fsp=6), nullable=False, server_default=TS_ONUPDATE),
        sa.PrimaryKeyConstraint("city_id"),
        mysql_engine="InnoDB",
    )
    op.create_index("uq_cities_code", "cities", ["code"], unique=True)
    op.create_index("ix_cities_updated_at_city_id", "cities", ["updated_at", "city_id"])

    # 2. stores
    op.create_table(
        "stores",
        sa.Column("store_id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column(
            "city_id", mysql.BIGINT(unsigned=True), nullable=False,
        ),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("address", sa.String(500), nullable=False),
        sa.Column("phone", sa.String(32), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", mysql.DATETIME(fsp=6), nullable=False, server_default=TS),
        sa.Column("updated_at", mysql.DATETIME(fsp=6), nullable=False, server_default=TS_ONUPDATE),
        sa.PrimaryKeyConstraint("store_id"),
        sa.ForeignKeyConstraint(
            ["city_id"], ["cities.city_id"],
            name="fk_stores_city_id", ondelete="RESTRICT",
        ),
        mysql_engine="InnoDB",
    )
    op.create_index("uq_stores_code", "stores", ["code"], unique=True)
    op.create_index("ix_stores_city_id_store_id", "stores", ["city_id", "store_id"])
    op.create_index("ix_stores_updated_at_store_id", "stores", ["updated_at", "store_id"])

    # 3. store_inventory
    op.create_table(
        "store_inventory",
        sa.Column(
            "store_id", mysql.BIGINT(unsigned=True), nullable=False,
        ),
        sa.Column(
            "variant_id", mysql.BIGINT(unsigned=True), nullable=False,
        ),
        sa.Column("on_hand", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("opening_on_hand", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("version", mysql.BIGINT(unsigned=True), nullable=False, server_default=sa.text("0")),
        sa.Column("updated_at", mysql.DATETIME(fsp=6), nullable=False, server_default=TS_ONUPDATE),
        sa.PrimaryKeyConstraint("store_id", "variant_id"),
        sa.ForeignKeyConstraint(
            ["store_id"], ["stores.store_id"],
            name="fk_store_inventory_store_id", ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["variant_id"], ["product_variants.variant_id"],
            name="fk_store_inventory_variant_id", ondelete="RESTRICT",
        ),
        sa.CheckConstraint("opening_on_hand >= 0", name="ck_store_inventory_opening_on_hand_non_negative"),
        sa.CheckConstraint("on_hand >= 0", name="ck_store_inventory_on_hand_non_negative"),
        sa.CheckConstraint("on_hand <= opening_on_hand", name="ck_store_inventory_on_hand_within_opening"),
        mysql_engine="InnoDB",
    )
    op.create_index("uq_store_inventory_store_id_variant_id", "store_inventory", ["store_id", "variant_id"], unique=True)
    op.create_index("ix_store_inventory_updated_at_store_id", "store_inventory", ["updated_at", "store_id"])

    # 4. alter customers: add city_id, store_id, expand role check constraint
    op.add_column(
        "customers",
        sa.Column(
            "city_id", mysql.BIGINT(unsigned=True), nullable=True,
        ),
    )
    op.add_column(
        "customers",
        sa.Column(
            "store_id", mysql.BIGINT(unsigned=True), nullable=True,
        ),
    )
    op.create_foreign_key(
        "fk_customers_city_id", "customers", "cities",
        ["city_id"], ["city_id"], ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_customers_store_id", "customers", "stores",
        ["store_id"], ["store_id"], ondelete="SET NULL",
    )

    # drop old role check constraint and recreate with expanded roles
    op.drop_constraint("ck_customers_role", "customers", type_="check")
    op.create_check_constraint(
        "ck_customers_role",
        "customers",
        "role in ('customer','admin','store_manager','city_planner')",
    )


def downgrade() -> None:
    # restore old role check constraint
    op.drop_constraint("ck_customers_role", "customers", type_="check")
    op.create_check_constraint(
        "ck_customers_role",
        "customers",
        "role in ('customer','admin')",
    )

    op.drop_constraint("fk_customers_store_id", "customers", type_="foreignkey")
    op.drop_constraint("fk_customers_city_id", "customers", type_="foreignkey")
    op.drop_column("customers", "store_id")
    op.drop_column("customers", "city_id")

    op.drop_table("store_inventory")
    op.drop_table("stores")
    op.drop_table("cities")
