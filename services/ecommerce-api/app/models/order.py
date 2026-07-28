from datetime import datetime

from sqlalchemy import (
    CHAR,
    CheckConstraint,
    ForeignKey,
    Index,
    String,
    text,
)
from sqlalchemy.dialects.mysql import BIGINT, DATETIME, INTEGER
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import GUID


class Order(Base):
    __tablename__ = "orders"

    order_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    order_number: Mapped[str] = mapped_column(String(32), nullable=False)
    cart_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True), ForeignKey("carts.cart_id", ondelete="RESTRICT"), nullable=False
    )
    customer_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True), ForeignKey("customers.customer_id", ondelete="RESTRICT"), nullable=False
    )
    checkout_idempotency_key: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    currency_code: Mapped[str] = mapped_column(CHAR(3), nullable=False, default="VND")
    subtotal_vnd: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    shipping_fee_vnd: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    total_vnd: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    receiver_name: Mapped[str] = mapped_column(String(160), nullable=False)
    receiver_phone: Mapped[str] = mapped_column(String(32), nullable=False)
    shipping_address_text: Mapped[str] = mapped_column(String(1000), nullable=False)
    data_origin: Mapped[str] = mapped_column(String(16), nullable=False, default="manual")
    generation_run_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6)")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
        server_onupdate=text("CURRENT_TIMESTAMP(6)"),
    )
    paid_at: Mapped[datetime | None] = mapped_column(DATETIME(fsp=6), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DATETIME(fsp=6), nullable=True)

    items: Mapped[list["OrderItem"]] = relationship(back_populates="order")
    payment: Mapped["Payment"] = relationship(back_populates="order", uselist=False)
    status_history: Mapped[list["OrderStatusHistory"]] = relationship(back_populates="order")

    __table_args__ = (
        CheckConstraint("status in ('paid','payment_failed','completed')", name="status"),
        CheckConstraint("currency_code = 'VND'", name="currency_code"),
        CheckConstraint("subtotal_vnd >= 0", name="subtotal_non_negative"),
        CheckConstraint("shipping_fee_vnd >= 0", name="shipping_fee_non_negative"),
        CheckConstraint("total_vnd = subtotal_vnd + shipping_fee_vnd", name="total_arithmetic"),
        CheckConstraint("data_origin in ('manual','synthetic')", name="data_origin"),
        Index("uq_orders_order_number", "order_number", unique=True),
        Index("uq_orders_cart_id", "cart_id", unique=True),
        Index("uq_orders_checkout_idempotency_key", "checkout_idempotency_key", unique=True),
        Index("ix_orders_customer_id_created_at_order_id", "customer_id", "created_at", "order_id"),
        Index("ix_orders_status_created_at_order_id", "status", "created_at", "order_id"),
        Index("ix_orders_updated_at_order_id", "updated_at", "order_id"),
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    order_item_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True), ForeignKey("orders.order_id", ondelete="RESTRICT"), nullable=False
    )
    variant_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True), ForeignKey("product_variants.variant_id", ondelete="RESTRICT"), nullable=False
    )
    product_public_id_snapshot: Mapped[str] = mapped_column(GUID(), nullable=False)
    category_code_snapshot: Mapped[str] = mapped_column(String(64), nullable=False)
    category_name_snapshot: Mapped[str] = mapped_column(String(160), nullable=False)
    product_name_snapshot: Mapped[str] = mapped_column(String(200), nullable=False)
    sku_snapshot: Mapped[str] = mapped_column(String(64), nullable=False)
    size_code_snapshot: Mapped[str] = mapped_column(String(32), nullable=False)
    color_code_snapshot: Mapped[str] = mapped_column(String(64), nullable=False)
    unit_price_vnd: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    quantity: Mapped[int] = mapped_column(INTEGER(unsigned=True), nullable=False)
    line_total_vnd: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6)")
    )

    order: Mapped["Order"] = relationship(back_populates="items")

    __table_args__ = (
        CheckConstraint("unit_price_vnd >= 0", name="unit_price_non_negative"),
        CheckConstraint("quantity > 0", name="quantity_positive"),
        CheckConstraint("line_total_vnd = unit_price_vnd * quantity", name="line_total_arithmetic"),
        Index("uq_order_items_order_id_variant_id", "order_id", "variant_id", unique=True),
        Index("ix_order_items_variant_id_order_item_id", "variant_id", "order_item_id"),
        Index("ix_order_items_created_at_order_item_id", "created_at", "order_item_id"),
    )


class Payment(Base):
    __tablename__ = "payments"

    payment_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    payment_reference: Mapped[str] = mapped_column(String(64), nullable=False)
    order_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True), ForeignKey("orders.order_id", ondelete="RESTRICT"), nullable=False
    )
    payment_idempotency_key: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    currency_code: Mapped[str] = mapped_column(CHAR(3), nullable=False, default="VND")
    amount_vnd: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    failure_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    attempted_at: Mapped[datetime] = mapped_column(DATETIME(fsp=6), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6)")
    )

    order: Mapped["Order"] = relationship(back_populates="payment")

    __table_args__ = (
        CheckConstraint("status in ('succeeded','failed')", name="status"),
        CheckConstraint("currency_code = 'VND'", name="currency_code"),
        CheckConstraint("amount_vnd >= 0", name="amount_non_negative"),
        CheckConstraint(
            "(status = 'succeeded' and failure_code is null) or (status = 'failed' and failure_code is not null)",
            name="failure_code_consistency",
        ),
        Index("uq_payments_payment_reference", "payment_reference", unique=True),
        Index("uq_payments_order_id", "order_id", unique=True),
        Index("uq_payments_payment_idempotency_key", "payment_idempotency_key", unique=True),
        Index("ix_payments_created_at_payment_id", "created_at", "payment_id"),
    )


class OrderStatusHistory(Base):
    __tablename__ = "order_status_history"

    order_status_history_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True), primary_key=True, autoincrement=True
    )
    order_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True), ForeignKey("orders.order_id", ondelete="RESTRICT"), nullable=False
    )
    from_status: Mapped[str | None] = mapped_column(String(24), nullable=True)
    to_status: Mapped[str] = mapped_column(String(24), nullable=False)
    transition_source: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    transition_idempotency_key: Mapped[str] = mapped_column(String(64), nullable=False)
    transitioned_at: Mapped[datetime] = mapped_column(DATETIME(fsp=6), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6)")
    )

    order: Mapped["Order"] = relationship(back_populates="status_history")

    __table_args__ = (
        CheckConstraint(
            "(from_status is null and to_status in ('paid','payment_failed')) "
            "or (from_status = 'paid' and to_status = 'completed')",
            name="valid_transition",
        ),
        CheckConstraint(
            "transition_source in ('checkout','internal_endpoint','generator','system','admin')",
            name="transition_source",
        ),
        Index("uq_order_status_history_transition_idempotency_key", "transition_idempotency_key", unique=True),
        Index("uq_order_status_history_order_id_to_status", "order_id", "to_status", unique=True),
        Index(
            "ix_order_status_history_order_id_transitioned_at_id",
            "order_id",
            "transitioned_at",
            "order_status_history_id",
        ),
        Index("ix_order_status_history_created_at_id", "created_at", "order_status_history_id"),
    )
