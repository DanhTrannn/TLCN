from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, JSON, String, Text, text
from sqlalchemy.dialects.mysql import BIGINT, DATETIME, INTEGER
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import GUID


class ReturnRequest(Base):
    __tablename__ = "return_requests"

    return_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    public_id: Mapped[UUID] = mapped_column(GUID(), nullable=False)
    return_code: Mapped[str] = mapped_column(String(64), nullable=False)
    order_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True), ForeignKey("orders.order_id", ondelete="RESTRICT"), nullable=False
    )
    customer_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True), ForeignKey("customers.customer_id", ondelete="RESTRICT"), nullable=False
    )
    action_type: Mapped[str] = mapped_column(String(16), nullable=False)  # 'exchange' | 'refund'
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending_review")
    customer_reason: Mapped[str] = mapped_column(Text, nullable=False)
    image_urls: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    admin_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DATETIME(fsp=6), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DATETIME(fsp=6), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6)")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
        server_onupdate=text("CURRENT_TIMESTAMP(6)"),
    )

    items: Mapped[list["ReturnItem"]] = relationship(back_populates="return_request", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("action_type in ('exchange','refund')", name="ck_return_requests_action_type"),
        CheckConstraint(
            "status in ('pending_review','approved','rejected','goods_received','completed','cancelled')",
            name="ck_return_requests_status",
        ),
        Index("uq_return_requests_public_id", "public_id", unique=True),
        Index("uq_return_requests_code", "return_code", unique=True),
        Index("ix_return_requests_order_id", "order_id"),
        Index("ix_return_requests_customer_id", "customer_id"),
        Index("ix_return_requests_status", "status"),
        Index("ix_return_requests_updated_at_return_id", "updated_at", "return_id"),
    )


class ReturnItem(Base):
    __tablename__ = "return_items"

    return_item_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    public_id: Mapped[UUID] = mapped_column(GUID(), nullable=False)
    return_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True), ForeignKey("return_requests.return_id", ondelete="CASCADE"), nullable=False
    )
    order_item_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True), ForeignKey("order_items.order_item_id", ondelete="RESTRICT"), nullable=False
    )
    variant_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True), ForeignKey("product_variants.variant_id", ondelete="RESTRICT"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(
        INTEGER(unsigned=True), nullable=False, default=1, server_default=text("1")
    )
    exchange_variant_id: Mapped[int | None] = mapped_column(
        BIGINT(unsigned=True), ForeignKey("product_variants.variant_id", ondelete="RESTRICT"), nullable=True
    )
    refund_amount_vnd: Mapped[int] = mapped_column(
        BIGINT(unsigned=True), nullable=False, default=0, server_default=text("0")
    )
    inspection_status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6)")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
        server_onupdate=text("CURRENT_TIMESTAMP(6)"),
    )

    return_request: Mapped["ReturnRequest"] = relationship(back_populates="items")

    __table_args__ = (
        CheckConstraint(
            "inspection_status in ('pending','passed','failed')", name="ck_return_items_inspection_status"
        ),
        Index("uq_return_items_public_id", "public_id", unique=True),
        Index("ix_return_items_return_id", "return_id"),
        Index("ix_return_items_variant_id", "variant_id"),
        Index("ix_return_items_updated_at_item_id", "updated_at", "return_item_id"),
    )
