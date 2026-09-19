from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.mysql import BIGINT, DATETIME, INTEGER
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import GUID


class DeliveryStaff(Base):
    __tablename__ = "delivery_staff"

    staff_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    public_id: Mapped[UUID] = mapped_column(GUID(), nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    vehicle_plate: Mapped[str | None] = mapped_column(String(30), nullable=True)
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

    shipments: Mapped[list["Shipment"]] = relationship(back_populates="delivery_staff")

    __table_args__ = (
        Index("uq_delivery_staff_public_id", "public_id", unique=True),
        Index("uq_delivery_staff_phone", "phone", unique=True),
        Index("ix_delivery_staff_updated_at_staff_id", "updated_at", "staff_id"),
    )


class Shipment(Base):
    __tablename__ = "shipments"

    shipment_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    public_id: Mapped[UUID] = mapped_column(GUID(), nullable=False)
    shipment_code: Mapped[str] = mapped_column(String(64), nullable=False)
    order_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True), ForeignKey("orders.order_id", ondelete="RESTRICT"), nullable=False
    )
    delivery_staff_id: Mapped[int | None] = mapped_column(
        BIGINT(unsigned=True), ForeignKey("delivery_staff.staff_id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="assigned")
    attempt_count: Mapped[int] = mapped_column(
        INTEGER(unsigned=True), nullable=False, default=1, server_default=text("1")
    )
    cod_amount_vnd: Mapped[int] = mapped_column(
        BIGINT(unsigned=True), nullable=False, default=0, server_default=text("0")
    )
    cod_collected_vnd: Mapped[int] = mapped_column(
        BIGINT(unsigned=True), nullable=False, default=0, server_default=text("0")
    )
    dispatched_at: Mapped[datetime | None] = mapped_column(DATETIME(fsp=6), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DATETIME(fsp=6), nullable=True)
    failed_at: Mapped[datetime | None] = mapped_column(DATETIME(fsp=6), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6)")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
        server_onupdate=text("CURRENT_TIMESTAMP(6)"),
    )

    delivery_staff: Mapped["DeliveryStaff | None"] = relationship(back_populates="shipments")

    __table_args__ = (
        CheckConstraint(
            "status in ('assigned','picked_up','in_transit','delivered','failed','returned_to_warehouse')",
            name="ck_shipments_status",
        ),
        Index("uq_shipments_public_id", "public_id", unique=True),
        Index("uq_shipments_code", "shipment_code", unique=True),
        Index("ix_shipments_order_id", "order_id"),
        Index("ix_shipments_delivery_staff_id", "delivery_staff_id"),
        Index("ix_shipments_status", "status"),
        Index("ix_shipments_updated_at_shipment_id", "updated_at", "shipment_id"),
    )
