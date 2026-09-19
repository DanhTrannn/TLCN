from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, text
from sqlalchemy.dialects.mysql import BIGINT, DATETIME
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import GUID


class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"

    transaction_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    public_id: Mapped[UUID] = mapped_column(GUID(), nullable=False)
    variant_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True), ForeignKey("product_variants.variant_id", ondelete="RESTRICT"), nullable=False
    )
    location_type: Mapped[str] = mapped_column(String(24), nullable=False)  # 'central_warehouse' | 'store'
    store_id: Mapped[int | None] = mapped_column(
        BIGINT(unsigned=True), ForeignKey("stores.store_id", ondelete="RESTRICT"), nullable=True
    )
    movement_type: Mapped[str] = mapped_column(String(32), nullable=False)
    quantity_delta: Mapped[int] = mapped_column(Integer, nullable=False)
    reference_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6)")
    )

    __table_args__ = (
        CheckConstraint("location_type in ('central_warehouse','store')", name="ck_inv_tx_location_type"),
        CheckConstraint(
            "movement_type in ('inbound','outbound_order','outbound_pos','transfer_to_store','transfer_received','return_boom','return_customer','exchange_out','adjustment')",
            name="ck_inv_tx_movement_type",
        ),
        Index("uq_inventory_tx_public_id", "public_id", unique=True),
        Index("ix_inv_tx_variant_id", "variant_id"),
        Index("ix_inv_tx_store_id", "store_id"),
        Index("ix_inv_tx_movement_type", "movement_type"),
        Index("ix_inv_tx_created_at_tx_id", "created_at", "transaction_id"),
    )
