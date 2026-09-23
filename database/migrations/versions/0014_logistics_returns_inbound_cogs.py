"""add logistics, return exchange, inventory transactions, cogs

Revision ID: 0014
Revises: 0013
Create Date: 2026-09-19
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None

TS = sa.text("CURRENT_TIMESTAMP(6)")
TS_ONUPDATE = sa.text("CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)")


def _guid() -> mysql.BINARY:
    return mysql.BINARY(16)


def upgrade() -> None:
    # 0. store_inventory: add store_inventory_id for single-pk tracking
    bind = op.get_bind()
    if bind.dialect.name == "mysql":
        inspector = sa.inspect(bind)
        cols = [c["name"] for c in inspector.get_columns("store_inventory")]
        if "store_inventory_id" not in cols:
            op.execute(
                "ALTER TABLE store_inventory ADD COLUMN store_inventory_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT, "
                "ADD UNIQUE KEY uq_store_inventory_id (store_inventory_id)"
            )
        else:
            uniques = [u["name"] for u in inspector.get_unique_constraints("store_inventory")]
            if "uq_store_inventory_id" not in uniques:
                op.execute("ALTER TABLE store_inventory DROP COLUMN store_inventory_id")
                op.execute(
                    "ALTER TABLE store_inventory ADD COLUMN store_inventory_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT, "
                    "ADD UNIQUE KEY uq_store_inventory_id (store_inventory_id)"
                )
    else:
        op.add_column(
            "store_inventory",
            sa.Column("store_inventory_id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        )
        op.create_unique_constraint("uq_store_inventory_id", "store_inventory", ["store_inventory_id"])

    # 1. product_variants: add cost_price_vnd
    op.add_column(
        "product_variants",
        sa.Column("cost_price_vnd", mysql.BIGINT(unsigned=True), nullable=False, server_default=sa.text("0")),
    )

    # 2. order_items: add cost_price_vnd
    op.add_column(
        "order_items",
        sa.Column("cost_price_vnd", mysql.BIGINT(unsigned=True), nullable=False, server_default=sa.text("0")),
    )

    # 3. customers: add is_cod_blocked and boom_count
    op.add_column(
        "customers",
        sa.Column("is_cod_blocked", sa.Boolean(), nullable=False, server_default=sa.text("0")),
    )
    op.add_column(
        "customers",
        sa.Column("boom_count", mysql.INTEGER(unsigned=True), nullable=False, server_default=sa.text("0")),
    )

    # 4. orders: add payment_method, update status constraints
    op.add_column(
        "orders",
        sa.Column("payment_method", sa.String(16), nullable=False, server_default="vietqr"),
    )
    # Drop existing status constraints to allow new statuses & COD flow
    op.drop_constraint("ck_orders_status", "orders", type_="check")
    op.drop_constraint("ck_orders_status_timestamp_consistency", "orders", type_="check")

    op.create_check_constraint(
        "ck_orders_status",
        "orders",
        "status in ('pending_payment','paid','payment_failed','confirmed','shipping','delivered','completed','cancelled','failed_delivery','returned')",
    )
    op.create_check_constraint(
        "ck_orders_payment_method",
        "orders",
        "payment_method in ('vietqr','cod')",
    )
    op.create_index("ix_orders_payment_method", "orders", ["payment_method"])

    # Update order_status_history valid transitions
    op.drop_constraint("ck_order_status_history_valid_transition", "order_status_history", type_="check")
    op.create_check_constraint(
        "ck_order_status_history_valid_transition",
        "order_status_history",
        "(from_status is null and to_status in ('pending_payment','paid','payment_failed','confirmed')) "
        "or (from_status = 'pending_payment' and to_status in ('paid','payment_failed','cancelled')) "
        "or (from_status = 'paid' and to_status in ('confirmed','cancelled')) "
        "or (from_status = 'confirmed' and to_status in ('shipping','completed','cancelled','failed_delivery')) "
        "or (from_status = 'shipping' and to_status in ('delivered','failed_delivery','returned')) "
        "or (from_status = 'delivered' and to_status in ('completed','returned')) "
        "or (from_status = 'completed' and to_status = 'returned')",
    )

    # 5. delivery_staff (in-house shippers)
    op.create_table(
        "delivery_staff",
        sa.Column("staff_id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column("public_id", _guid(), nullable=False),
        sa.Column("full_name", sa.String(100), nullable=False),
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column("vehicle_plate", sa.String(30), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", mysql.DATETIME(fsp=6), nullable=False, server_default=TS),
        sa.Column("updated_at", mysql.DATETIME(fsp=6), nullable=False, server_default=TS_ONUPDATE),
        sa.PrimaryKeyConstraint("staff_id"),
        sa.UniqueConstraint("public_id", name="uq_delivery_staff_public_id"),
        sa.UniqueConstraint("phone", name="uq_delivery_staff_phone"),
        mysql_engine="InnoDB",
    )
    op.create_index(
        "ix_delivery_staff_updated_at_staff_id",
        "delivery_staff",
        ["updated_at", "staff_id"],
    )

    # 6. shipments
    op.create_table(
        "shipments",
        sa.Column("shipment_id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column("public_id", _guid(), nullable=False),
        sa.Column("shipment_code", sa.String(64), nullable=False),
        sa.Column("order_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("delivery_staff_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="assigned"),
        sa.Column("attempt_count", mysql.INTEGER(unsigned=True), nullable=False, server_default=sa.text("1")),
        sa.Column("cod_amount_vnd", mysql.BIGINT(unsigned=True), nullable=False, server_default=sa.text("0")),
        sa.Column("cod_collected_vnd", mysql.BIGINT(unsigned=True), nullable=False, server_default=sa.text("0")),
        sa.Column("dispatched_at", mysql.DATETIME(fsp=6), nullable=True),
        sa.Column("delivered_at", mysql.DATETIME(fsp=6), nullable=True),
        sa.Column("failed_at", mysql.DATETIME(fsp=6), nullable=True),
        sa.Column("failure_reason", sa.String(255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", mysql.DATETIME(fsp=6), nullable=False, server_default=TS),
        sa.Column("updated_at", mysql.DATETIME(fsp=6), nullable=False, server_default=TS_ONUPDATE),
        sa.PrimaryKeyConstraint("shipment_id"),
        sa.UniqueConstraint("public_id", name="uq_shipments_public_id"),
        sa.UniqueConstraint("shipment_code", name="uq_shipments_code"),
        sa.ForeignKeyConstraint(
            ["order_id"], ["orders.order_id"], name="fk_shipments_order_id_orders", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["delivery_staff_id"], ["delivery_staff.staff_id"], name="fk_shipments_staff_id", ondelete="SET NULL"
        ),
        sa.CheckConstraint(
            "status in ('assigned','picked_up','in_transit','delivered','failed','returned_to_warehouse')",
            name="ck_shipments_status",
        ),
        mysql_engine="InnoDB",
    )
    op.create_index("ix_shipments_order_id", "shipments", ["order_id"])
    op.create_index("ix_shipments_delivery_staff_id", "shipments", ["delivery_staff_id"])
    op.create_index("ix_shipments_status", "shipments", ["status"])
    op.create_index("ix_shipments_updated_at_shipment_id", "shipments", ["updated_at", "shipment_id"])

    # 7. return_requests
    op.create_table(
        "return_requests",
        sa.Column("return_id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column("public_id", _guid(), nullable=False),
        sa.Column("return_code", sa.String(64), nullable=False),
        sa.Column("order_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("customer_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("action_type", sa.String(16), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending_review"),
        sa.Column("customer_reason", sa.Text(), nullable=False),
        sa.Column("image_urls", sa.JSON(), nullable=True),
        sa.Column("admin_note", sa.Text(), nullable=True),
        sa.Column("reviewed_at", mysql.DATETIME(fsp=6), nullable=True),
        sa.Column("resolved_at", mysql.DATETIME(fsp=6), nullable=True),
        sa.Column("created_at", mysql.DATETIME(fsp=6), nullable=False, server_default=TS),
        sa.Column("updated_at", mysql.DATETIME(fsp=6), nullable=False, server_default=TS_ONUPDATE),
        sa.PrimaryKeyConstraint("return_id"),
        sa.UniqueConstraint("public_id", name="uq_return_requests_public_id"),
        sa.UniqueConstraint("return_code", name="uq_return_requests_code"),
        sa.ForeignKeyConstraint(
            ["order_id"], ["orders.order_id"], name="fk_return_requests_order_id", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["customer_id"], ["customers.customer_id"], name="fk_return_requests_customer_id", ondelete="RESTRICT"
        ),
        sa.CheckConstraint("action_type in ('exchange','refund')", name="ck_return_requests_action_type"),
        sa.CheckConstraint(
            "status in ('pending_review','approved','rejected','goods_received','completed','cancelled')",
            name="ck_return_requests_status",
        ),
        mysql_engine="InnoDB",
    )
    op.create_index("ix_return_requests_order_id", "return_requests", ["order_id"])
    op.create_index("ix_return_requests_customer_id", "return_requests", ["customer_id"])
    op.create_index("ix_return_requests_status", "return_requests", ["status"])
    op.create_index("ix_return_requests_updated_at_return_id", "return_requests", ["updated_at", "return_id"])

    # 8. return_items
    op.create_table(
        "return_items",
        sa.Column("return_item_id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column("public_id", _guid(), nullable=False),
        sa.Column("return_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("order_item_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("variant_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("quantity", mysql.INTEGER(unsigned=True), nullable=False, server_default=sa.text("1")),
        sa.Column("exchange_variant_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("refund_amount_vnd", mysql.BIGINT(unsigned=True), nullable=False, server_default=sa.text("0")),
        sa.Column("inspection_status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("created_at", mysql.DATETIME(fsp=6), nullable=False, server_default=TS),
        sa.Column("updated_at", mysql.DATETIME(fsp=6), nullable=False, server_default=TS_ONUPDATE),
        sa.PrimaryKeyConstraint("return_item_id"),
        sa.UniqueConstraint("public_id", name="uq_return_items_public_id"),
        sa.ForeignKeyConstraint(
            ["return_id"], ["return_requests.return_id"], name="fk_return_items_return_id", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["order_item_id"], ["order_items.order_item_id"], name="fk_return_items_order_item_id", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["variant_id"], ["product_variants.variant_id"], name="fk_return_items_variant_id", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["exchange_variant_id"],
            ["product_variants.variant_id"],
            name="fk_return_items_exchange_variant_id",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "inspection_status in ('pending','passed','failed')", name="ck_return_items_inspection_status"
        ),
        mysql_engine="InnoDB",
    )
    op.create_index("ix_return_items_return_id", "return_items", ["return_id"])
    op.create_index("ix_return_items_variant_id", "return_items", ["variant_id"])
    op.create_index("ix_return_items_updated_at_item_id", "return_items", ["updated_at", "return_item_id"])

    # 9. inventory_transactions
    op.create_table(
        "inventory_transactions",
        sa.Column("transaction_id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column("public_id", _guid(), nullable=False),
        sa.Column("variant_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("location_type", sa.String(24), nullable=False),
        sa.Column("store_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("movement_type", sa.String(32), nullable=False),
        sa.Column("quantity_delta", sa.Integer(), nullable=False),
        sa.Column("reference_code", sa.String(64), nullable=True),
        sa.Column("notes", sa.String(255), nullable=True),
        sa.Column("created_at", mysql.DATETIME(fsp=6), nullable=False, server_default=TS),
        sa.PrimaryKeyConstraint("transaction_id"),
        sa.UniqueConstraint("public_id", name="uq_inventory_tx_public_id"),
        sa.ForeignKeyConstraint(
            ["variant_id"], ["product_variants.variant_id"], name="fk_inv_tx_variant_id", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["store_id"], ["stores.store_id"], name="fk_inv_tx_store_id", ondelete="RESTRICT"
        ),
        sa.CheckConstraint("location_type in ('central_warehouse','store')", name="ck_inv_tx_location_type"),
        sa.CheckConstraint(
            "movement_type in ('inbound','outbound_order','outbound_pos','transfer_to_store','transfer_received','return_boom','return_customer','exchange_out','adjustment')",
            name="ck_inv_tx_movement_type",
        ),
        mysql_engine="InnoDB",
    )
    op.create_index("ix_inv_tx_variant_id", "inventory_transactions", ["variant_id"])
    op.create_index("ix_inv_tx_store_id", "inventory_transactions", ["store_id"])
    op.create_index("ix_inv_tx_movement_type", "inventory_transactions", ["movement_type"])
    op.create_index("ix_inv_tx_created_at_tx_id", "inventory_transactions", ["created_at", "transaction_id"])


def downgrade() -> None:
    op.drop_table("inventory_transactions")
    op.drop_table("return_items")
    op.drop_table("return_requests")
    op.drop_table("shipments")
    op.drop_table("delivery_staff")

    op.drop_index("ix_orders_payment_method", table_name="orders")
    op.drop_constraint("ck_orders_payment_method", "orders", type_="check")
    op.drop_constraint("ck_orders_status", "orders", type_="check")
    op.create_check_constraint(
        "ck_orders_status",
        "orders",
        "status in ('paid','payment_failed','confirmed','completed','cancelled')",
    )
    op.drop_constraint("ck_order_status_history_valid_transition", "order_status_history", type_="check")
    op.create_check_constraint(
        "ck_order_status_history_valid_transition",
        "order_status_history",
        "(from_status is null and to_status in ('paid','payment_failed')) "
        "or (from_status = 'paid' and to_status in ('confirmed','cancelled')) "
        "or (from_status = 'confirmed' and to_status = 'completed')",
    )
    op.drop_column("orders", "payment_method")

    op.drop_column("customers", "boom_count")
    op.drop_column("customers", "is_cod_blocked")
    op.drop_column("order_items", "cost_price_vnd")
    op.drop_column("product_variants", "cost_price_vnd")
    op.drop_constraint("uq_store_inventory_id", "store_inventory", type_="unique")
    op.drop_column("store_inventory", "store_inventory_id")
