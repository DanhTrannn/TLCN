from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, text
from sqlalchemy.dialects.mysql import BIGINT, DATETIME
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class WishlistItem(Base):
    __tablename__ = "wishlist_items"

    wishlist_item_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True), primary_key=True, autoincrement=True
    )
    customer_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey("customers.customer_id", ondelete="RESTRICT"),
        nullable=False,
    )
    product_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey("products.product_id", ondelete="RESTRICT"),
        nullable=False,
    )
    is_present: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    first_added_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6)")
    )
    last_added_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6)")
    )
    removed_at: Mapped[datetime | None] = mapped_column(DATETIME(fsp=6), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
        server_onupdate=text("CURRENT_TIMESTAMP(6)"),
    )

    __table_args__ = (
        CheckConstraint(
            "(is_present = 1 and removed_at is null) "
            "or (is_present = 0 and removed_at is not null)",
            name="presence_removed_consistency",
        ),
        CheckConstraint("last_added_at >= first_added_at", name="last_added_after_first"),
        CheckConstraint(
            "removed_at is null or removed_at >= last_added_at",
            name="removed_after_last_added",
        ),
        Index(
            "uq_wishlist_items_customer_id_product_id",
            "customer_id",
            "product_id",
            unique=True,
        ),
        Index(
            "ix_wishlist_items_customer_present_last_added_id",
            "customer_id",
            "is_present",
            "last_added_at",
            "wishlist_item_id",
        ),
        Index(
            "ix_wishlist_items_product_id_wishlist_item_id",
            "product_id",
            "wishlist_item_id",
        ),
        Index(
            "ix_wishlist_items_updated_at_wishlist_item_id",
            "updated_at",
            "wishlist_item_id",
        ),
    )
