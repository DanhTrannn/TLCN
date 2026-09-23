"""add inbound production receipts, refund updated_at, and extend customer staff roles

Revision ID: 0015
Revises: 0014
Create Date: 2026-09-23
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None

TS = sa.text("CURRENT_TIMESTAMP(6)")
TS_ONUPDATE = sa.text("CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)")


def _guid() -> mysql.BINARY:
    return mysql.BINARY(16)


def upgrade() -> None:
    bind = op.get_bind()

    # 1. Update customers.role column length and check constraint
    if bind.dialect.name == "mysql":
        op.alter_column(
            "customers",
            "role",
            existing_type=sa.String(16),
            type_=sa.String(32),
            existing_nullable=False,
            server_default="customer",
        )
        # Drop old check constraint on role if present
        inspector = sa.inspect(bind)
        check_names = {c["name"] for c in inspector.get_check_constraints("customers") if c.get("name")}
        for old_ck in ["ck_customers_ck_customers_role", "ck_customers_role"]:
            if old_ck in check_names:
                op.execute(f"ALTER TABLE customers DROP CHECK {old_ck}")

        op.execute(
            "ALTER TABLE customers ADD CONSTRAINT ck_customers_role "
            "CHECK (role in ('customer','admin','store_manager','sales_manager','marketing_manager','inventory_manager','operations_manager','system_admin','city_planner'))"
        )

    # 2. Add updated_at to refunds
    inspector = sa.inspect(bind)
    refund_cols = [c["name"] for c in inspector.get_columns("refunds")]
    if "updated_at" not in refund_cols:
        op.add_column(
            "refunds",
            sa.Column("updated_at", mysql.DATETIME(fsp=6), nullable=False, server_default=TS_ONUPDATE),
        )
        op.create_index("ix_refunds_updated_at_refund_id", "refunds", ["updated_at", "refund_id"])

    # 3. Create inbound_receipts
    tables = inspector.get_table_names()
    if "inbound_receipts" not in tables:
        op.create_table(
            "inbound_receipts",
            sa.Column("receipt_id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
            sa.Column("public_id", _guid(), nullable=False),
            sa.Column("receipt_code", sa.String(64), nullable=False),
            sa.Column("batch_name", sa.String(255), nullable=False),
            sa.Column("status", sa.String(24), nullable=False, server_default="completed"),
            sa.Column("total_items_count", mysql.INTEGER(unsigned=True), nullable=False, server_default=sa.text("0")),
            sa.Column("total_cost_vnd", mysql.BIGINT(unsigned=True), nullable=False, server_default=sa.text("0")),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_by_customer_id", mysql.BIGINT(unsigned=True), nullable=False),
            sa.Column("created_at", mysql.DATETIME(fsp=6), nullable=False, server_default=TS),
            sa.Column("updated_at", mysql.DATETIME(fsp=6), nullable=False, server_default=TS_ONUPDATE),
            sa.PrimaryKeyConstraint("receipt_id"),
            sa.UniqueConstraint("public_id", name="uq_inbound_receipts_public_id"),
            sa.UniqueConstraint("receipt_code", name="uq_inbound_receipts_code"),
            sa.ForeignKeyConstraint(
                ["created_by_customer_id"],
                ["customers.customer_id"],
                name="fk_inbound_receipts_created_by",
                ondelete="RESTRICT",
            ),
            sa.CheckConstraint("status = 'completed'", name="ck_inbound_receipts_status"),
            sa.CheckConstraint("total_items_count >= 0", name="ck_inbound_receipts_items_count"),
            sa.CheckConstraint("total_cost_vnd >= 0", name="ck_inbound_receipts_total_cost"),
            mysql_engine="InnoDB",
        )
        op.create_index(
            "ix_inbound_receipts_created_at_id",
            "inbound_receipts",
            ["created_at", "receipt_id"],
        )

    # 4. Create inbound_receipt_items
    if "inbound_receipt_items" not in tables:
        op.create_table(
            "inbound_receipt_items",
            sa.Column("item_id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
            sa.Column("public_id", _guid(), nullable=False),
            sa.Column("receipt_id", mysql.BIGINT(unsigned=True), nullable=False),
            sa.Column("variant_id", mysql.BIGINT(unsigned=True), nullable=False),
            sa.Column("quantity", mysql.INTEGER(unsigned=True), nullable=False),
            sa.Column("unit_cost_vnd", mysql.BIGINT(unsigned=True), nullable=False, server_default=sa.text("0")),
            sa.Column("total_cost_vnd", mysql.BIGINT(unsigned=True), nullable=False, server_default=sa.text("0")),
            sa.Column("previous_cost_price_vnd", mysql.BIGINT(unsigned=True), nullable=False, server_default=sa.text("0")),
            sa.Column("new_cost_price_vnd", mysql.BIGINT(unsigned=True), nullable=False, server_default=sa.text("0")),
            sa.Column("created_at", mysql.DATETIME(fsp=6), nullable=False, server_default=TS),
            sa.PrimaryKeyConstraint("item_id"),
            sa.UniqueConstraint("public_id", name="uq_inbound_items_public_id"),
            sa.ForeignKeyConstraint(
                ["receipt_id"],
                ["inbound_receipts.receipt_id"],
                name="fk_inbound_items_receipt_id",
                ondelete="CASCADE",
            ),
            sa.ForeignKeyConstraint(
                ["variant_id"],
                ["product_variants.variant_id"],
                name="fk_inbound_items_variant_id",
                ondelete="RESTRICT",
            ),
            sa.CheckConstraint("quantity > 0", name="ck_inbound_items_quantity"),
            sa.CheckConstraint("unit_cost_vnd >= 0", name="ck_inbound_items_unit_cost"),
            sa.CheckConstraint("total_cost_vnd >= 0", name="ck_inbound_items_total_cost"),
            mysql_engine="InnoDB",
        )
        op.create_index("ix_inbound_items_receipt_id", "inbound_receipt_items", ["receipt_id"])
        op.create_index("ix_inbound_items_variant_id", "inbound_receipt_items", ["variant_id"])


def downgrade() -> None:
    op.drop_table("inbound_receipt_items")
    op.drop_table("inbound_receipts")
    op.drop_index("ix_refunds_updated_at_refund_id", table_name="refunds")
    op.drop_column("refunds", "updated_at")
