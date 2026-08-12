from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, String, text
from sqlalchemy.dialects.mysql import BIGINT, DATETIME, INTEGER
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import GUID


class Coupon(Base):
    __tablename__ = "coupons"

    coupon_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    public_id: Mapped[UUID] = mapped_column(GUID(), nullable=False)
    code_normalized: Mapped[str] = mapped_column(String(64), nullable=False)
    discount_type: Mapped[str] = mapped_column(String(24), nullable=False)
    discount_value: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    minimum_subtotal_vnd: Mapped[int] = mapped_column(
        BIGINT(unsigned=True), nullable=False, default=0
    )
    starts_at: Mapped[datetime] = mapped_column(DATETIME(fsp=6), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DATETIME(fsp=6), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    archived_at: Mapped[datetime | None] = mapped_column(DATETIME(fsp=6), nullable=True)
    archived_by_customer_id: Mapped[int | None] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey("customers.customer_id", ondelete="RESTRICT"),
        nullable=True,
    )
    archive_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    total_usage_limit: Mapped[int | None] = mapped_column(BIGINT(unsigned=True), nullable=True)
    per_customer_usage_limit: Mapped[int | None] = mapped_column(INTEGER(unsigned=True), nullable=True)
    used_count: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6)")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
        server_onupdate=text("CURRENT_TIMESTAMP(6)"),
    )

    redemptions: Mapped[list["CouponRedemption"]] = relationship(back_populates="coupon")

    __table_args__ = (
        CheckConstraint("discount_type in ('percentage','fixed_amount')", name="discount_type"),
        CheckConstraint(
            "(discount_type = 'percentage' and discount_value between 1 and 100) "
            "or (discount_type = 'fixed_amount' and discount_value > 0)",
            name="discount_value",
        ),
        CheckConstraint("starts_at < ends_at", name="effective_window"),
        CheckConstraint(
            "total_usage_limit is null or total_usage_limit > 0",
            name="total_usage_limit_positive",
        ),
        CheckConstraint(
            "per_customer_usage_limit is null or per_customer_usage_limit > 0",
            name="customer_usage_limit_positive",
        ),
        CheckConstraint(
            "total_usage_limit is null or used_count <= total_usage_limit",
            name="used_count_within_limit",
        ),
        CheckConstraint(
            "(archived_at is null and archived_by_customer_id is null and archive_reason is null) "
            "or (archived_at is not null and archived_by_customer_id is not null "
            "and archive_reason is not null and char_length(trim(archive_reason)) >= 3)",
            name="archive_metadata_consistency",
        ),
        CheckConstraint(
            "archived_at is null or is_active = 0",
            name="archived_not_active",
        ),
        Index("uq_coupons_public_id", "public_id", unique=True),
        Index("uq_coupons_code_normalized", "code_normalized", unique=True),
        Index("ix_coupons_archived_at_coupon_id", "archived_at", "coupon_id"),
        Index("ix_coupons_updated_at_coupon_id", "updated_at", "coupon_id"),
    )


class CouponRedemption(Base):
    __tablename__ = "coupon_redemptions"

    coupon_redemption_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True), primary_key=True, autoincrement=True
    )
    coupon_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True), ForeignKey("coupons.coupon_id", ondelete="RESTRICT"), nullable=False
    )
    order_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True), ForeignKey("orders.order_id", ondelete="RESTRICT"), nullable=False
    )
    customer_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True), ForeignKey("customers.customer_id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    redeemed_at: Mapped[datetime] = mapped_column(DATETIME(fsp=6), nullable=False)
    released_at: Mapped[datetime | None] = mapped_column(DATETIME(fsp=6), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6)")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
        server_onupdate=text("CURRENT_TIMESTAMP(6)"),
    )

    coupon: Mapped["Coupon"] = relationship(back_populates="redemptions")

    __table_args__ = (
        CheckConstraint("status in ('redeemed','released')", name="status"),
        CheckConstraint(
            "(status = 'redeemed' and released_at is null) "
            "or (status = 'released' and released_at is not null)",
            name="release_consistency",
        ),
        Index("uq_coupon_redemptions_order_id", "order_id", unique=True),
        Index(
            "ix_coupon_redemptions_coupon_customer_status",
            "coupon_id",
            "customer_id",
            "status",
        ),
        Index(
            "ix_coupon_redemptions_updated_at_id",
            "updated_at",
            "coupon_redemption_id",
        ),
    )
