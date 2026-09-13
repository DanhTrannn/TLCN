from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, String, text
from sqlalchemy.dialects.mysql import BIGINT, DATETIME
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class City(Base):
    __tablename__ = "cities"

    city_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
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
        Index("uq_cities_code", "code", unique=True),
        Index("ix_cities_updated_at_city_id", "updated_at", "city_id"),
    )


class Store(Base):
    __tablename__ = "stores"

    store_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    city_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey("cities.city_id", ondelete="RESTRICT"),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)
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
        Index("uq_stores_code", "code", unique=True),
        Index("ix_stores_city_id_store_id", "city_id", "store_id"),
        Index("ix_stores_updated_at_store_id", "updated_at", "store_id"),
    )


class StoreInventory(Base):
    __tablename__ = "store_inventory"

    store_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey("stores.store_id", ondelete="RESTRICT"),
        primary_key=True,
    )
    variant_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey("product_variants.variant_id", ondelete="RESTRICT"),
        primary_key=True,
    )
    on_hand: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    opening_on_hand: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    version: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
        server_onupdate=text("CURRENT_TIMESTAMP(6)"),
    )

    __table_args__ = (
        CheckConstraint("opening_on_hand >= 0", name="opening_on_hand_non_negative"),
        CheckConstraint("on_hand >= 0", name="on_hand_non_negative"),
        CheckConstraint("on_hand <= opening_on_hand", name="on_hand_within_opening"),
        Index("uq_store_inventory_store_id_variant_id", "store_id", "variant_id", unique=True),
        Index("ix_store_inventory_updated_at_store_id", "updated_at", "store_id"),
    )
