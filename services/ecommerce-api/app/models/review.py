from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.mysql import BIGINT, DATETIME, INTEGER
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import GUID


class ProductReview(Base):
    __tablename__ = "product_reviews"

    review_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    public_id: Mapped[UUID] = mapped_column(GUID(), nullable=False)
    order_item_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True), ForeignKey("order_items.order_item_id", ondelete="RESTRICT"), nullable=False
    )
    customer_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True), ForeignKey("customers.customer_id", ondelete="RESTRICT"), nullable=False
    )
    product_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True), ForeignKey("products.product_id", ondelete="RESTRICT"), nullable=False
    )
    rating: Mapped[int] = mapped_column(INTEGER(unsigned=True), nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    moderation_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    moderated_by_customer_id: Mapped[int | None] = mapped_column(
        BIGINT(unsigned=True), ForeignKey("customers.customer_id", ondelete="RESTRICT"), nullable=True
    )
    moderated_at: Mapped[datetime | None] = mapped_column(DATETIME(fsp=6), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6)")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
        server_onupdate=text("CURRENT_TIMESTAMP(6)"),
    )

    __table_args__ = (
        CheckConstraint("rating between 1 and 5", name="rating"),
        CheckConstraint("status in ('pending','approved','rejected')", name="status"),
        CheckConstraint(
            "(status = 'pending' and moderated_by_customer_id is null and moderated_at is null) "
            "or (status in ('approved','rejected') and moderated_by_customer_id is not null "
            "and moderated_at is not null)",
            name="moderation_consistency",
        ),
        Index("uq_product_reviews_public_id", "public_id", unique=True),
        Index("uq_product_reviews_order_item_id", "order_item_id", unique=True),
        Index(
            "ix_product_reviews_product_status_created_at_id",
            "product_id",
            "status",
            "created_at",
            "review_id",
        ),
        Index(
            "ix_product_reviews_customer_created_at_id",
            "customer_id",
            "created_at",
            "review_id",
        ),
        Index("ix_product_reviews_updated_at_review_id", "updated_at", "review_id"),
    )
