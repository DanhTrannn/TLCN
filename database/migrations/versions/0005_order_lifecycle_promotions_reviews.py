"""add order lifecycle, coupons, refunds, and reviews

Revision ID: 0005_order_lifecycle
Revises: 0004_simplify_checkout_payment
Create Date: 2026-08-02
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


revision = "0005_order_lifecycle"
down_revision = "0004_simplify_checkout_payment"
branch_labels = None
depends_on = None

TS = sa.text("CURRENT_TIMESTAMP(6)")
TS_ONUPDATE = sa.text("CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)")


def _guid() -> mysql.BINARY:
    return mysql.BINARY(16)


def upgrade() -> None:
    op.create_table(
        "coupons",
        sa.Column("coupon_id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column("public_id", _guid(), nullable=False),
        sa.Column("code_normalized", sa.String(64), nullable=False),
        sa.Column("discount_type", sa.String(24), nullable=False),
        sa.Column("discount_value", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column(
            "minimum_subtotal_vnd",
            mysql.BIGINT(unsigned=True),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("starts_at", mysql.DATETIME(fsp=6), nullable=False),
        sa.Column("ends_at", mysql.DATETIME(fsp=6), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("total_usage_limit", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("per_customer_usage_limit", mysql.INTEGER(unsigned=True), nullable=True),
        sa.Column("used_count", mysql.BIGINT(unsigned=True), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", mysql.DATETIME(fsp=6), nullable=False, server_default=TS),
        sa.Column("updated_at", mysql.DATETIME(fsp=6), nullable=False, server_default=TS_ONUPDATE),
        sa.PrimaryKeyConstraint("coupon_id"),
        sa.CheckConstraint(
            "discount_type in ('percentage','fixed_amount')",
            name="ck_coupons_discount_type",
        ),
        sa.CheckConstraint(
            "(discount_type = 'percentage' and discount_value between 1 and 100) "
            "or (discount_type = 'fixed_amount' and discount_value > 0)",
            name="ck_coupons_discount_value",
        ),
        sa.CheckConstraint("starts_at < ends_at", name="ck_coupons_effective_window"),
        sa.CheckConstraint(
            "total_usage_limit is null or total_usage_limit > 0",
            name="ck_coupons_total_usage_limit_positive",
        ),
        sa.CheckConstraint(
            "per_customer_usage_limit is null or per_customer_usage_limit > 0",
            name="ck_coupons_customer_usage_limit_positive",
        ),
        sa.CheckConstraint(
            "total_usage_limit is null or used_count <= total_usage_limit",
            name="ck_coupons_used_count_within_limit",
        ),
        mysql_engine="InnoDB",
    )
    op.create_index("uq_coupons_public_id", "coupons", ["public_id"], unique=True)
    op.create_index("uq_coupons_code_normalized", "coupons", ["code_normalized"], unique=True)
    op.create_index("ix_coupons_updated_at_coupon_id", "coupons", ["updated_at", "coupon_id"])

    op.drop_constraint("ck_orders_status", "orders", type_="check")
    op.drop_constraint("ck_orders_total_arithmetic", "orders", type_="check")
    op.add_column("orders", sa.Column("coupon_id", mysql.BIGINT(unsigned=True), nullable=True))
    op.add_column("orders", sa.Column("coupon_code_snapshot", sa.String(64), nullable=True))
    op.add_column("orders", sa.Column("coupon_type_snapshot", sa.String(24), nullable=True))
    op.add_column(
        "orders",
        sa.Column("coupon_value_snapshot", mysql.BIGINT(unsigned=True), nullable=True),
    )
    op.add_column(
        "orders",
        sa.Column(
            "discount_amount_vnd",
            mysql.BIGINT(unsigned=True),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.add_column("orders", sa.Column("confirmed_at", mysql.DATETIME(fsp=6), nullable=True))
    op.add_column("orders", sa.Column("cancelled_at", mysql.DATETIME(fsp=6), nullable=True))
    op.execute(
        "UPDATE orders SET paid_at = COALESCE(paid_at, created_at) "
        "WHERE status in ('paid','completed')"
    )
    op.execute(
        "UPDATE orders SET completed_at = COALESCE(completed_at, updated_at, paid_at), "
        "confirmed_at = COALESCE(completed_at, updated_at, paid_at) "
        "WHERE status = 'completed'"
    )
    op.create_foreign_key(
        "fk_orders_coupon_id_coupons",
        "orders",
        "coupons",
        ["coupon_id"],
        ["coupon_id"],
        ondelete="RESTRICT",
    )
    op.create_check_constraint(
        "ck_orders_status",
        "orders",
        "status in ('paid','payment_failed','confirmed','completed','cancelled')",
    )
    op.create_check_constraint(
        "ck_orders_discount_within_subtotal",
        "orders",
        "discount_amount_vnd <= subtotal_vnd",
    )
    op.create_check_constraint(
        "ck_orders_total_arithmetic",
        "orders",
        "total_vnd = subtotal_vnd - discount_amount_vnd + shipping_fee_vnd",
    )
    op.create_check_constraint(
        "ck_orders_coupon_snapshot_consistency",
        "orders",
        "(coupon_id is null and coupon_code_snapshot is null and coupon_type_snapshot is null "
        "and coupon_value_snapshot is null and discount_amount_vnd = 0) or "
        "(coupon_id is not null and coupon_code_snapshot is not null and coupon_type_snapshot is not null "
        "and coupon_value_snapshot is not null and discount_amount_vnd > 0)",
    )
    op.create_check_constraint(
        "ck_orders_coupon_snapshot_value",
        "orders",
        "coupon_type_snapshot is null or "
        "(coupon_type_snapshot = 'percentage' and coupon_value_snapshot between 1 and 100) or "
        "(coupon_type_snapshot = 'fixed_amount' and coupon_value_snapshot > 0)",
    )
    op.create_check_constraint(
        "ck_orders_status_timestamp_consistency",
        "orders",
        "(status = 'payment_failed' and paid_at is null and confirmed_at is null "
        "and completed_at is null and cancelled_at is null) or "
        "(status = 'paid' and paid_at is not null and confirmed_at is null "
        "and completed_at is null and cancelled_at is null) or "
        "(status = 'confirmed' and paid_at is not null and confirmed_at is not null "
        "and completed_at is null and cancelled_at is null) or "
        "(status = 'completed' and paid_at is not null and confirmed_at is not null "
        "and completed_at is not null and cancelled_at is null) or "
        "(status = 'cancelled' and paid_at is not null and confirmed_at is null "
        "and completed_at is null and cancelled_at is not null)",
    )
    op.create_index("ix_orders_coupon_id_order_id", "orders", ["coupon_id", "order_id"])

    op.add_column("order_items", sa.Column("public_id", _guid(), nullable=True))
    op.execute("UPDATE order_items SET public_id = UUID_TO_BIN(UUID()) WHERE public_id IS NULL")
    op.alter_column("order_items", "public_id", existing_type=_guid(), nullable=False)
    op.create_index("uq_order_items_public_id", "order_items", ["public_id"], unique=True)

    op.drop_constraint("ck_order_status_history_valid_transition", "order_status_history", type_="check")
    op.drop_constraint("ck_order_status_history_transition_source", "order_status_history", type_="check")
    op.execute(
        "INSERT INTO order_status_history "
        "(order_id, from_status, to_status, transition_source, reason, "
        "transition_idempotency_key, transitioned_at, created_at) "
        "SELECT order_id, 'paid', 'confirmed', 'system', "
        "'Backfill lifecycle khi nâng cấp schema', CONCAT('migration:confirm:', order_id), "
        "confirmed_at, confirmed_at FROM orders WHERE status = 'completed'"
    )
    op.execute(
        "UPDATE order_status_history SET from_status = 'confirmed' "
        "WHERE to_status = 'completed' AND from_status = 'paid'"
    )
    op.create_check_constraint(
        "ck_order_status_history_valid_transition",
        "order_status_history",
        "(from_status is null and to_status in ('paid','payment_failed')) "
        "or (from_status = 'paid' and to_status in ('confirmed','cancelled')) "
        "or (from_status = 'confirmed' and to_status = 'completed')",
    )
    op.create_check_constraint(
        "ck_order_status_history_transition_source",
        "order_status_history",
        "transition_source in ('checkout','internal_endpoint','generator','system','admin','customer')",
    )
    op.create_check_constraint(
        "ck_order_status_history_cancel_reason",
        "order_status_history",
        "to_status <> 'cancelled' or reason is not null",
    )

    op.create_table(
        "coupon_redemptions",
        sa.Column(
            "coupon_redemption_id",
            mysql.BIGINT(unsigned=True),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column("coupon_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("order_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("customer_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("redeemed_at", mysql.DATETIME(fsp=6), nullable=False),
        sa.Column("released_at", mysql.DATETIME(fsp=6), nullable=True),
        sa.Column("created_at", mysql.DATETIME(fsp=6), nullable=False, server_default=TS),
        sa.Column("updated_at", mysql.DATETIME(fsp=6), nullable=False, server_default=TS_ONUPDATE),
        sa.PrimaryKeyConstraint("coupon_redemption_id"),
        sa.ForeignKeyConstraint(
            ["coupon_id"], ["coupons.coupon_id"], name="fk_coupon_redemptions_coupon_id_coupons", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["order_id"], ["orders.order_id"], name="fk_coupon_redemptions_order_id_orders", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["customer_id"], ["customers.customer_id"], name="fk_coupon_redemptions_customer_id_customers", ondelete="RESTRICT"
        ),
        sa.CheckConstraint(
            "status in ('redeemed','released')",
            name="ck_coupon_redemptions_status",
        ),
        sa.CheckConstraint(
            "(status = 'redeemed' and released_at is null) "
            "or (status = 'released' and released_at is not null)",
            name="ck_coupon_redemptions_release_consistency",
        ),
        mysql_engine="InnoDB",
    )
    op.create_index(
        "uq_coupon_redemptions_order_id", "coupon_redemptions", ["order_id"], unique=True
    )
    op.create_index(
        "ix_coupon_redemptions_coupon_customer_status",
        "coupon_redemptions",
        ["coupon_id", "customer_id", "status"],
    )
    op.create_index(
        "ix_coupon_redemptions_updated_at_id",
        "coupon_redemptions",
        ["updated_at", "coupon_redemption_id"],
    )

    op.create_table(
        "refunds",
        sa.Column("refund_id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column("public_id", _guid(), nullable=False),
        sa.Column("payment_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("refund_idempotency_key", sa.String(64), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("currency_code", sa.CHAR(3), nullable=False, server_default=sa.text("'VND'")),
        sa.Column("amount_vnd", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("reason", sa.String(500), nullable=False),
        sa.Column("requested_by_customer_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("created_at", mysql.DATETIME(fsp=6), nullable=False, server_default=TS),
        sa.Column("completed_at", mysql.DATETIME(fsp=6), nullable=True),
        sa.PrimaryKeyConstraint("refund_id"),
        sa.ForeignKeyConstraint(
            ["payment_id"], ["payments.payment_id"], name="fk_refunds_payment_id_payments", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["requested_by_customer_id"],
            ["customers.customer_id"],
            name="fk_refunds_requested_by_customer_id_customers",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint("status in ('succeeded','failed')", name="ck_refunds_status"),
        sa.CheckConstraint("currency_code = 'VND'", name="ck_refunds_currency_code"),
        sa.CheckConstraint("amount_vnd >= 0", name="ck_refunds_amount_non_negative"),
        sa.CheckConstraint(
            "(status = 'succeeded' and completed_at is not null) "
            "or (status = 'failed' and completed_at is null)",
            name="ck_refunds_completion_consistency",
        ),
        mysql_engine="InnoDB",
    )
    op.create_index("uq_refunds_public_id", "refunds", ["public_id"], unique=True)
    op.create_index("uq_refunds_payment_id", "refunds", ["payment_id"], unique=True)
    op.create_index(
        "uq_refunds_refund_idempotency_key",
        "refunds",
        ["refund_idempotency_key"],
        unique=True,
    )
    op.create_index("ix_refunds_created_at_refund_id", "refunds", ["created_at", "refund_id"])

    op.create_table(
        "product_reviews",
        sa.Column("review_id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column("public_id", _guid(), nullable=False),
        sa.Column("order_item_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("customer_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("product_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("rating", mysql.INTEGER(unsigned=True), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("status", sa.String(16), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("moderation_reason", sa.String(500), nullable=True),
        sa.Column("moderated_by_customer_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("moderated_at", mysql.DATETIME(fsp=6), nullable=True),
        sa.Column("created_at", mysql.DATETIME(fsp=6), nullable=False, server_default=TS),
        sa.Column("updated_at", mysql.DATETIME(fsp=6), nullable=False, server_default=TS_ONUPDATE),
        sa.PrimaryKeyConstraint("review_id"),
        sa.ForeignKeyConstraint(
            ["order_item_id"], ["order_items.order_item_id"], name="fk_product_reviews_order_item_id_order_items", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["customer_id"], ["customers.customer_id"], name="fk_product_reviews_customer_id_customers", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["product_id"], ["products.product_id"], name="fk_product_reviews_product_id_products", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["moderated_by_customer_id"],
            ["customers.customer_id"],
            name="fk_product_reviews_moderated_by_customer_id_customers",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint("rating between 1 and 5", name="ck_product_reviews_rating"),
        sa.CheckConstraint(
            "status in ('pending','approved','rejected')",
            name="ck_product_reviews_status",
        ),
        sa.CheckConstraint(
            "(status = 'pending' and moderated_by_customer_id is null and moderated_at is null) "
            "or (status in ('approved','rejected') and moderated_by_customer_id is not null "
            "and moderated_at is not null)",
            name="ck_product_reviews_moderation_consistency",
        ),
        mysql_engine="InnoDB",
    )
    op.create_index("uq_product_reviews_public_id", "product_reviews", ["public_id"], unique=True)
    op.create_index(
        "uq_product_reviews_order_item_id", "product_reviews", ["order_item_id"], unique=True
    )
    op.create_index(
        "ix_product_reviews_product_status_created_at_id",
        "product_reviews",
        ["product_id", "status", "created_at", "review_id"],
    )
    op.create_index(
        "ix_product_reviews_customer_created_at_id",
        "product_reviews",
        ["customer_id", "created_at", "review_id"],
    )
    op.create_index(
        "ix_product_reviews_updated_at_review_id",
        "product_reviews",
        ["updated_at", "review_id"],
    )


def downgrade() -> None:
    op.drop_table("product_reviews")
    op.drop_table("refunds")
    op.drop_table("coupon_redemptions")

    op.drop_constraint("ck_order_status_history_cancel_reason", "order_status_history", type_="check")
    op.drop_constraint("ck_order_status_history_transition_source", "order_status_history", type_="check")
    op.drop_constraint("ck_order_status_history_valid_transition", "order_status_history", type_="check")
    op.create_check_constraint(
        "ck_order_status_history_valid_transition",
        "order_status_history",
        "(from_status is null and to_status in ('paid','payment_failed')) "
        "or (from_status = 'paid' and to_status = 'completed')",
    )
    op.create_check_constraint(
        "ck_order_status_history_transition_source",
        "order_status_history",
        "transition_source in ('checkout','internal_endpoint','generator','system','admin')",
    )

    op.drop_index("uq_order_items_public_id", table_name="order_items")
    op.drop_column("order_items", "public_id")

    op.drop_index("ix_orders_coupon_id_order_id", table_name="orders")
    op.drop_constraint("ck_orders_status_timestamp_consistency", "orders", type_="check")
    op.drop_constraint("ck_orders_coupon_snapshot_value", "orders", type_="check")
    op.drop_constraint("ck_orders_coupon_snapshot_consistency", "orders", type_="check")
    op.drop_constraint("ck_orders_total_arithmetic", "orders", type_="check")
    op.drop_constraint("ck_orders_discount_within_subtotal", "orders", type_="check")
    op.drop_constraint("ck_orders_status", "orders", type_="check")
    op.drop_constraint("fk_orders_coupon_id_coupons", "orders", type_="foreignkey")
    op.drop_column("orders", "cancelled_at")
    op.drop_column("orders", "confirmed_at")
    op.drop_column("orders", "discount_amount_vnd")
    op.drop_column("orders", "coupon_value_snapshot")
    op.drop_column("orders", "coupon_type_snapshot")
    op.drop_column("orders", "coupon_code_snapshot")
    op.drop_column("orders", "coupon_id")
    op.create_check_constraint(
        "ck_orders_status", "orders", "status in ('paid','payment_failed','completed')"
    )
    op.create_check_constraint(
        "ck_orders_total_arithmetic",
        "orders",
        "total_vnd = subtotal_vnd + shipping_fee_vnd",
    )

    op.drop_table("coupons")
