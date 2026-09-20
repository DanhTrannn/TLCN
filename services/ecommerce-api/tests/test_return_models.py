"""Model-level tests for Returns & Refunds flow (Gói 2) - Task 1."""

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.sql.elements import TextClause

from app.core.ids import uuid7
from app.db.base import Base
import app.models  # noqa: F401
from app.models.customer import Customer
from app.models.order import Order, OrderStatusHistory


@compiles(TextClause, "sqlite")
def _compile_text(element, compiler, **kw):
    val = element.text
    if "CURRENT_TIMESTAMP(6)" in val:
        return val.replace("CURRENT_TIMESTAMP(6)", "CURRENT_TIMESTAMP")
    return val


@compiles(BIGINT, "sqlite")
def _compile_bigint(element, compiler, **kw):
    return "INTEGER"


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def connect(dbapi_connection, connection_record):
        dbapi_connection.create_function("char_length", 1, lambda s: len(s) if s is not None else 0)

    Base.metadata.create_all(engine)
    testing_session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    db = testing_session()

    customer = Customer(
        customer_id=1,
        public_id=str(uuid7()),
        role="customer",
        display_name="Test Customer",
        status="active",
    )
    db.add(customer)
    db.commit()

    yield db
    db.close()
    engine.dispose()


@pytest.fixture()
def test_order(db_session):
    order = Order(
        order_id=1,
        order_number="ORD-TEST-0001",
        customer_id=1,
        checkout_idempotency_key=f"chk-{uuid.uuid4().hex[:30]}",
        status="completed",
        subtotal_vnd=1000000,
        discount_amount_vnd=0,
        shipping_fee_vnd=30000,
        total_vnd=1030000,
        receiver_name="Test Customer",
        receiver_phone="0900000000",
        shipping_address_text="123 Đường Test, TP.HCM",
        completed_at=datetime.now(timezone.utc),
    )
    db_session.add(order)
    db_session.commit()
    return order


def test_order_status_history_allows_completed_to_returned(db_session, test_order):
    test_order.status = "completed"
    db_session.commit()

    now = datetime.now(timezone.utc)
    history = OrderStatusHistory(
        order_id=test_order.order_id,
        from_status="completed",
        to_status="returned",
        transition_source="admin_return",
        transition_idempotency_key=f"ret-{uuid.uuid4().hex[:30]}",
        transitioned_at=now,
    )
    db_session.add(history)
    db_session.commit()

    saved = db_session.scalar(
        select(OrderStatusHistory).where(
            OrderStatusHistory.order_status_history_id == history.order_status_history_id
        )
    )
    assert saved is not None
    assert saved.to_status == "returned"
    assert saved.transition_source == "admin_return"
