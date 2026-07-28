from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Computed,
    ForeignKey,
    Index,
    String,
    text,
)
from sqlalchemy.dialects.mysql import BIGINT, DATETIME, INTEGER
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import GUID


class Cart(Base):
    __tablename__ = "carts"

    cart_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    public_id: Mapped[str] = mapped_column(GUID(), nullable=False)
    customer_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True), ForeignKey("customers.customer_id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")
    active_customer_guard: Mapped[int | None] = mapped_column(
        BIGINT(unsigned=True),
        Computed("(case when status = 'active' then customer_id else null end)", persisted=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6)")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
        server_onupdate=text("CURRENT_TIMESTAMP(6)"),
    )
    checked_out_at: Mapped[datetime | None] = mapped_column(DATETIME(fsp=6), nullable=True)

    items: Mapped[list["CartItem"]] = relationship(back_populates="cart")

    __table_args__ = (
        CheckConstraint("status in ('active','checked_out')", name="status"),
        Index("uq_carts_public_id", "public_id", unique=True),
        Index("uq_carts_active_customer_guard", "active_customer_guard", unique=True),
        Index("ix_carts_customer_id_created_at_cart_id", "customer_id", "created_at", "cart_id"),
        Index("ix_carts_updated_at_cart_id", "updated_at", "cart_id"),
    )


class CartItem(Base):
    __tablename__ = "cart_items"

    cart_item_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    cart_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True), ForeignKey("carts.cart_id", ondelete="RESTRICT"), nullable=False
    )
    variant_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True), ForeignKey("product_variants.variant_id", ondelete="RESTRICT"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(INTEGER(unsigned=True), nullable=False)
    is_present: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    first_added_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6)")
    )
    removed_at: Mapped[datetime | None] = mapped_column(DATETIME(fsp=6), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
        server_onupdate=text("CURRENT_TIMESTAMP(6)"),
    )

    cart: Mapped["Cart"] = relationship(back_populates="items")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="quantity_positive"),
        CheckConstraint(
            "(is_present = 1 and removed_at is null) or (is_present = 0 and removed_at is not null)",
            name="presence_removed_consistency",
        ),
        Index("uq_cart_items_cart_id_variant_id", "cart_id", "variant_id", unique=True),
        Index("ix_cart_items_variant_id_cart_item_id", "variant_id", "cart_item_id"),
        Index("ix_cart_items_updated_at_cart_item_id", "updated_at", "cart_item_id"),
    )
