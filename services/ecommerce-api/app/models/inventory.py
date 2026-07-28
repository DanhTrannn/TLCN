from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, Index, text
from sqlalchemy.dialects.mysql import BIGINT, DATETIME
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Inventory(Base):
    __tablename__ = "inventory"

    variant_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey("product_variants.variant_id", ondelete="RESTRICT"),
        primary_key=True,
    )
    opening_on_hand: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    on_hand: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
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
        Index("ix_inventory_updated_at_variant_id", "updated_at", "variant_id"),
    )
