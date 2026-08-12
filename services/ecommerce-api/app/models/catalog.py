from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.mysql import BIGINT, DATETIME
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import GUID


class Category(Base):
    __tablename__ = "categories"

    category_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    public_id: Mapped[str] = mapped_column(GUID(), nullable=False)
    parent_category_id: Mapped[int | None] = mapped_column(
        BIGINT(unsigned=True), ForeignKey("categories.category_id", ondelete="RESTRICT"), nullable=True
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
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
        Index("uq_categories_code", "code", unique=True),
        Index("uq_categories_public_id", "public_id", unique=True),
        Index(
            "ix_categories_parent_is_active_id",
            "parent_category_id",
            "is_active",
            "category_id",
        ),
        Index("ix_categories_updated_at_category_id", "updated_at", "category_id"),
    )


class Product(Base):
    __tablename__ = "products"

    product_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    public_id: Mapped[str] = mapped_column(GUID(), nullable=False)
    category_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True), ForeignKey("categories.category_id", ondelete="RESTRICT"), nullable=False
    )
    slug: Mapped[str] = mapped_column(String(180), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    archived_at: Mapped[datetime | None] = mapped_column(DATETIME(fsp=6), nullable=True)
    archived_by_customer_id: Mapped[int | None] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey("customers.customer_id", ondelete="RESTRICT"),
        nullable=True,
    )
    archive_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
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
        Index("uq_products_slug", "slug", unique=True),
        Index("uq_products_public_id", "public_id", unique=True),
        Index("ix_products_category_id_is_active_product_id", "category_id", "is_active", "product_id"),
        Index("ix_products_is_active_product_id", "is_active", "product_id"),
        Index("ix_products_archived_at_product_id", "archived_at", "product_id"),
        Index("ix_products_updated_at_product_id", "updated_at", "product_id"),
    )


class ProductVariant(Base):
    __tablename__ = "product_variants"

    variant_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    public_id: Mapped[str] = mapped_column(GUID(), nullable=False)
    product_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True), ForeignKey("products.product_id", ondelete="RESTRICT"), nullable=False
    )
    sku: Mapped[str] = mapped_column(String(64), nullable=False)
    size_code: Mapped[str] = mapped_column(String(32), nullable=False)
    color_code: Mapped[str] = mapped_column(String(64), nullable=False)
    price_vnd: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
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
        CheckConstraint("price_vnd >= 0", name="price_non_negative"),
        Index("uq_product_variants_sku", "sku", unique=True),
        Index("uq_product_variants_public_id", "public_id", unique=True),
        Index("uq_product_variants_product_size_color", "product_id", "size_code", "color_code", unique=True),
        Index("ix_product_variants_product_id_is_active_variant_id", "product_id", "is_active", "variant_id"),
        Index("ix_product_variants_updated_at_variant_id", "updated_at", "variant_id"),
    )
