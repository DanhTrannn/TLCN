from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, String, text
from sqlalchemy.dialects.mysql import BIGINT, DATETIME
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import GUID


class Customer(Base):
    __tablename__ = "customers"

    customer_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    public_id: Mapped[str] = mapped_column(GUID(), nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False, default="customer")
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")
    data_origin: Mapped[str] = mapped_column(String(16), nullable=False, default="manual")
    generation_run_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    anonymized_at: Mapped[datetime | None] = mapped_column(DATETIME(fsp=6), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6)")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
        server_onupdate=text("CURRENT_TIMESTAMP(6)"),
    )

    credential: Mapped["CustomerCredential"] = relationship(back_populates="customer", uselist=False)

    __table_args__ = (
        CheckConstraint("status in ('active','inactive')", name="status"),
        CheckConstraint("role in ('customer','admin')", name="role"),
        CheckConstraint("data_origin in ('manual','synthetic')", name="data_origin"),
        Index("uq_customers_public_id", "public_id", unique=True),
        Index("ix_customers_role_status_id", "role", "status", "customer_id"),
        Index("ix_customers_updated_at_customer_id", "updated_at", "customer_id"),
    )


class CustomerCredential(Base):
    __tablename__ = "customer_credentials"

    customer_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey("customers.customer_id", ondelete="RESTRICT"),
        primary_key=True,
    )
    email_normalized: Mapped[str] = mapped_column(String(320), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    password_changed_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6)")
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

    customer: Mapped["Customer"] = relationship(back_populates="credential")

    __table_args__ = (
        Index("uq_customer_credentials_email_normalized", "email_normalized", unique=True),
    )
