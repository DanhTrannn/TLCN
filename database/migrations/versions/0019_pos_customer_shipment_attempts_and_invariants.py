"""pos customer nullable, shipment attempts table, and business invariants

Revision ID: 0019
Revises: 0018
Create Date: 2026-10-12
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision = "0019"
down_revision = "0018"
branch_labels = None
depends_on = None

TS = sa.text("CURRENT_TIMESTAMP(6)")


def _guid() -> mysql.BINARY:
    return mysql.BINARY(16)


def _drop_matching_checks(table: str, fragments: tuple[str, ...]) -> None:
    bind = op.get_bind()
    checks = sa.inspect(bind).get_check_constraints(table)
    for check in checks:
        name = check.get("name")
        normalized = (name or "").lower()
        if name and any(fragment in normalized for fragment in fragments):
            op.execute(f"ALTER TABLE {table} DROP CHECK {name}")


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "mysql":
        return

    # 1. orders: allow customer_id to be NULL for walk-in POS customers
    op.execute("ALTER TABLE orders MODIFY customer_id BIGINT UNSIGNED NULL")

    # 1b. orders: add channel and status invariants
    _drop_matching_checks("orders", ("pos_channel", "channel_payment", "cod_pending_no_paid_at"))
    op.execute(
        "ALTER TABLE orders ADD CONSTRAINT ck_orders_pos_channel CHECK ("
        "(channel != 'pos') OR (store_id IS NOT NULL AND staff_id IS NOT NULL)"
        ")"
    )
    op.execute(
        "ALTER TABLE orders ADD CONSTRAINT ck_orders_channel_payment CHECK ("
        "((channel = 'pos' AND payment_method IN ('cash', 'card', 'vietqr')) OR "
        "(channel = 'online' AND payment_method IN ('vietqr', 'cod')))"
        ")"
    )
    op.execute(
        "ALTER TABLE orders ADD CONSTRAINT ck_orders_cod_pending_no_paid_at CHECK ("
        "NOT (payment_method = 'cod' AND status IN ('pending_payment', 'confirmed', 'shipping') AND paid_at IS NOT NULL)"
        ")"
    )

    # 2. shipments: create shipment_attempts table
    op.create_table(
        "shipment_attempts",
        sa.Column("attempt_id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column("public_id", _guid(), nullable=False),
        sa.Column("shipment_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("attempt_number", mysql.INTEGER(unsigned=True), nullable=False),
        sa.Column("delivery_staff_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("failure_reason", sa.String(255), nullable=True),
        sa.Column("is_buyer_fault", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("idempotency_key", sa.String(64), nullable=False),
        sa.Column("attempted_at", mysql.DATETIME(fsp=6), nullable=False),
        sa.Column("created_at", mysql.DATETIME(fsp=6), nullable=False, server_default=TS),
        sa.Column("updated_at", mysql.DATETIME(fsp=6), nullable=False, server_default=TS),
        sa.PrimaryKeyConstraint("attempt_id"),
        sa.UniqueConstraint("public_id", name="uq_shipment_attempts_public_id"),
        sa.UniqueConstraint("idempotency_key", name="uq_shipment_attempts_idempotency_key"),
        sa.UniqueConstraint("shipment_id", "attempt_number", name="uq_shipment_attempts_shipment_attempt_number"),
        sa.ForeignKeyConstraint(
            ["shipment_id"], ["shipments.shipment_id"], name="fk_shipment_attempts_shipment_id", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["delivery_staff_id"], ["delivery_staff.staff_id"], name="fk_shipment_attempts_delivery_staff_id", ondelete="SET NULL"
        ),
        sa.CheckConstraint("attempt_number between 1 and 3", name="ck_shipment_attempts_attempt_number"),
        sa.CheckConstraint(
            "status in ('attempted_failed', 'attempted_success', 'failed', 'delivered')",
            name="ck_shipment_attempts_status",
        ),
        mysql_engine="InnoDB",
    )
    op.create_index("ix_shipment_attempts_delivery_staff_id", "shipment_attempts", ["delivery_staff_id"])
    op.create_index("ix_shipment_attempts_attempted_at", "shipment_attempts", ["attempted_at"])

    # Preserve delivery attempts recorded by revision 0018 before removing the
    # denormalized key columns. The old schema only retained the latest failure
    # reason/timestamp on the shipment, so those values are the best historical
    # snapshot available for every migrated attempt.
    for attempt_number in range(1, 4):
        op.execute(
            sa.text(
                f"""
                INSERT INTO shipment_attempts (
                    public_id, shipment_id, attempt_number, delivery_staff_id,
                    status, failure_reason, is_buyer_fault, idempotency_key,
                    attempted_at, created_at, updated_at
                )
                SELECT
                    UUID_TO_BIN(UUID()), shipment_id, :attempt_number, delivery_staff_id,
                    'attempted_failed', failure_reason, 1,
                    failed_attempt_{attempt_number}_key,
                    COALESCE(updated_at, created_at),
                    COALESCE(updated_at, created_at),
                    COALESCE(updated_at, created_at)
                FROM shipments
                WHERE failed_attempt_{attempt_number}_key IS NOT NULL
                """
            ).bindparams(attempt_number=attempt_number)
        )

    # 2b. shipments: drop 3 flat attempt key columns
    op.drop_index("uq_shipments_failed_attempt_3_key", table_name="shipments")
    op.drop_index("uq_shipments_failed_attempt_2_key", table_name="shipments")
    op.drop_index("uq_shipments_failed_attempt_1_key", table_name="shipments")
    op.drop_column("shipments", "failed_attempt_3_key")
    op.drop_column("shipments", "failed_attempt_2_key")
    op.drop_column("shipments", "failed_attempt_1_key")

    # 2c. shipments: add cod_collected_vnd <= cod_amount_vnd check
    _drop_matching_checks("shipments", ("cod_collected_limit",))
    op.execute(
        "ALTER TABLE shipments ADD CONSTRAINT ck_shipments_cod_collected_limit CHECK ("
        "cod_collected_vnd <= cod_amount_vnd"
        ")"
    )

    # 3. customers: add COD reinstatement audit trail
    op.add_column("customers", sa.Column("cod_reinstated_at", mysql.DATETIME(fsp=6), nullable=True))
    op.add_column("customers", sa.Column("cod_reinstated_by", mysql.BIGINT(unsigned=True), nullable=True))
    op.add_column("customers", sa.Column("cod_reinstatement_reason", sa.String(255), nullable=True))
    op.create_foreign_key(
        "fk_customers_cod_reinstated_by",
        "customers",
        "customers",
        ["cod_reinstated_by"],
        ["customer_id"],
        ondelete="SET NULL",
    )

    # 4. inventory_transactions: add 'order_cancellation' to movement_type check
    _drop_matching_checks("inventory_transactions", ("movement_type",))
    op.execute(
        "ALTER TABLE inventory_transactions ADD CONSTRAINT ck_inventory_transactions_movement_type CHECK ("
        "movement_type in ('inbound','outbound_order','outbound_pos','transfer_to_store','transfer_received',"
        "'return_boom','return_customer','exchange_out','adjustment','order_cancellation')"
        ")"
    )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "mysql":
        return

    # 4. inventory_transactions: retain rows while mapping the new movement
    # type to the closest type understood by revision 0018.
    _drop_matching_checks("inventory_transactions", ("movement_type",))
    op.execute(
        "UPDATE inventory_transactions SET movement_type = 'adjustment' "
        "WHERE movement_type = 'order_cancellation'"
    )
    op.execute(
        "ALTER TABLE inventory_transactions ADD CONSTRAINT ck_inventory_transactions_movement_type CHECK ("
        "movement_type in ('inbound','outbound_order','outbound_pos','transfer_to_store','transfer_received',"
        "'return_boom','return_customer','exchange_out','adjustment')"
        ")"
    )

    # 3. customers: remove audit columns
    op.drop_constraint("fk_customers_cod_reinstated_by", "customers", type_="foreignkey")
    op.drop_column("customers", "cod_reinstatement_reason")
    op.drop_column("customers", "cod_reinstated_by")
    op.drop_column("customers", "cod_reinstated_at")

    # 2. shipments: drop check, restore flat columns and drop shipment_attempts
    _drop_matching_checks("shipments", ("cod_collected_limit",))
    op.add_column("shipments", sa.Column("failed_attempt_1_key", sa.String(64), nullable=True))
    op.add_column("shipments", sa.Column("failed_attempt_2_key", sa.String(64), nullable=True))
    op.add_column("shipments", sa.Column("failed_attempt_3_key", sa.String(64), nullable=True))
    op.execute(
        """
        UPDATE shipments AS s
        LEFT JOIN shipment_attempts AS a1
          ON a1.shipment_id = s.shipment_id AND a1.attempt_number = 1
             AND a1.status = 'attempted_failed'
        LEFT JOIN shipment_attempts AS a2
          ON a2.shipment_id = s.shipment_id AND a2.attempt_number = 2
             AND a2.status = 'attempted_failed'
        LEFT JOIN shipment_attempts AS a3
          ON a3.shipment_id = s.shipment_id AND a3.attempt_number = 3
             AND a3.status = 'attempted_failed'
        SET s.failed_attempt_1_key = a1.idempotency_key,
            s.failed_attempt_2_key = a2.idempotency_key,
            s.failed_attempt_3_key = a3.idempotency_key
        """
    )
    op.create_index("uq_shipments_failed_attempt_1_key", "shipments", ["failed_attempt_1_key"], unique=True)
    op.create_index("uq_shipments_failed_attempt_2_key", "shipments", ["failed_attempt_2_key"], unique=True)
    op.create_index("uq_shipments_failed_attempt_3_key", "shipments", ["failed_attempt_3_key"], unique=True)
    op.drop_table("shipment_attempts")

    # 1. orders: drop constraints, set default for nulls, restore customer_id NOT NULL
    _drop_matching_checks("orders", ("pos_channel", "channel_payment", "cod_pending_no_paid_at"))
    op.execute("UPDATE orders SET customer_id = staff_id WHERE customer_id IS NULL AND staff_id IS NOT NULL")
    op.execute("ALTER TABLE orders MODIFY customer_id BIGINT UNSIGNED NOT NULL")
