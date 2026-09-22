"""Integration tests for Admin Financial & Operational Metrics Extension in Overview API (Gói 4 - Task 1)."""

import uuid
from datetime import UTC, datetime, timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, select
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.sql.elements import TextClause

from app.core.ids import uuid7
from app.db.base import Base
from app.db.deps import get_current_admin, get_current_customer, get_db, verify_csrf
import app.db.deps
import app.db.uow
from app.main import app as fastapi_app
import app.models  # noqa: F401
from app.models.catalog import Category, Product, ProductVariant
from app.models.customer import Customer
from app.models.order import Order, OrderItem, Payment, Refund


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
def setup_db(monkeypatch):
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

    monkeypatch.setattr(app.db.uow, "SessionLocal", testing_session)
    monkeypatch.setattr(app.db.deps, "SessionLocal", testing_session)

    def _get_test_db():
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    fastapi_app.dependency_overrides[get_db] = _get_test_db

    db = testing_session()
    admin = Customer(
        customer_id=10,
        public_id=uuid7(),
        role="admin",
        display_name="Quản Trị Viên",
        status="active",
    )
    buyer = Customer(
        customer_id=1,
        public_id=uuid7(),
        role="customer",
        display_name="Khách Hàng",
        status="active",
    )
    cat = Category(category_id=1, public_id=uuid7(), code="AO-NAM", name="Áo Nam", is_active=True)
    prod = Product(
        product_id=1,
        public_id=uuid7(),
        category_id=1,
        slug="ao-polo",
        name="Áo Polo Nam",
        is_active=True,
    )
    # Variant 1: cost_price = 100,000, price = 300,000
    var1 = ProductVariant(
        variant_id=1,
        public_id=uuid7(),
        product_id=1,
        sku="APN-001",
        size_code="L",
        color_code="DEN",
        price_vnd=300000,
        cost_price_vnd=100000,
        is_active=True,
    )
    # Variant 2: cost_price = 50,000, price = 150,000
    var2 = ProductVariant(
        variant_id=2,
        public_id=uuid7(),
        product_id=1,
        sku="APN-002",
        size_code="M",
        color_code="TRANG",
        price_vnd=150000,
        cost_price_vnd=50000,
        is_active=True,
    )
    db.add_all([admin, buyer, cat, prod, var1, var2])
    db.commit()

    yield testing_session

    fastapi_app.dependency_overrides.pop(get_db, None)
    Base.metadata.drop_all(engine)


@pytest.fixture()
def test_db(setup_db):
    session = setup_db()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def admin_client(setup_db):
    mock_admin = Customer(
        customer_id=10,
        public_id=uuid7(),
        role="admin",
        display_name="Quản Trị Viên",
        status="active",
    )
    fastapi_app.dependency_overrides[get_current_admin] = lambda: mock_admin
    fastapi_app.dependency_overrides[get_current_customer] = lambda: mock_admin
    fastapi_app.dependency_overrides[verify_csrf] = lambda: None

    with TestClient(fastapi_app, raise_server_exceptions=False) as client:
        yield client

    fastapi_app.dependency_overrides.pop(get_current_admin, None)
    fastapi_app.dependency_overrides.pop(get_current_customer, None)
    fastapi_app.dependency_overrides.pop(verify_csrf, None)


def _create_order_with_items(
    session,
    order_number: str,
    status: str,
    items_data: list[dict],
    customer_id: int = 1,
    payment_status: str | None = None,
    payment_amount: int | None = None,
) -> Order:
    now = datetime.now(UTC).replace(tzinfo=None)
    subtotal = sum(it["unit_price"] * it["quantity"] for it in items_data)
    total = subtotal

    order = Order(
        order_number=order_number,
        customer_id=customer_id,
        checkout_idempotency_key=f"chk-{uuid.uuid4().hex[:30]}",
        status=status,
        subtotal_vnd=subtotal,
        discount_amount_vnd=0,
        shipping_fee_vnd=0,
        total_vnd=total,
        receiver_name="Người Nhận",
        receiver_phone="0901234567",
        shipping_address_text="123 Nguyễn Huệ, Q1, TP.HCM",
        completed_at=now if status == "completed" else None,
        cancelled_at=now if status == "cancelled" else None,
    )
    session.add(order)
    session.flush()

    for it in items_data:
        session.add(
            OrderItem(
                public_id=uuid7(),
                order_id=order.order_id,
                variant_id=it["variant_id"],
                product_public_id_snapshot=uuid7(),
                category_code_snapshot="AO-NAM",
                category_name_snapshot="Áo Nam",
                product_name_snapshot="Áo Polo Nam",
                sku_snapshot=it.get("sku", "APN-001"),
                size_code_snapshot="L",
                color_code_snapshot="DEN",
                unit_price_vnd=it["unit_price"],
                cost_price_vnd=it["cost_price"],
                quantity=it["quantity"],
                line_total_vnd=it["unit_price"] * it["quantity"],
            )
        )

    if payment_status:
        pay_amount = payment_amount if payment_amount is not None else total
        session.add(
            Payment(
                payment_reference=f"PAY-{order_number}",
                order_id=order.order_id,
                payment_idempotency_key=f"pay-{uuid.uuid4().hex[:30]}",
                status=payment_status,
                amount_vnd=pay_amount,
                failure_code="PAYMENT_REJECTED" if payment_status == "failed" else None,
                attempted_at=now,
            )
        )
    session.commit()
    return order


def test_admin_overview_baseline_empty(admin_client, test_db):
    """Ensure financial and operational metrics default properly when empty."""
    res = admin_client.get("/api/v1/admin/overview")
    assert res.status_code == 200, res.text
    data = res.json()
    assert "cogs_vnd" in data
    assert "gross_profit_vnd" in data
    assert "gross_margin_percent" in data
    assert "boom_orders_count" in data
    assert "return_orders_count" in data
    assert data["cogs_vnd"] == 0
    assert data["gross_profit_vnd"] == 0
    assert data["gross_margin_percent"] == 0.0
    assert data["boom_orders_count"] == 0
    assert data["return_orders_count"] == 0


def test_admin_overview_financial_metrics_calculation(admin_client, test_db):
    """
    Comprehensive test for:
    - cogs_vnd sums quantity * cost_price_vnd for delivered and completed orders
    - excluded statuses (cancelled, payment_failed, shipping, failed_delivery, returned) do not contribute to cogs_vnd
    - gross_profit_vnd = net_revenue_vnd - cogs_vnd
    - gross_margin_percent = round((gross_profit / net_rev) * 100, 1)
    - boom_orders_count counts failed_delivery
    - return_orders_count counts returned
    """
    now = datetime.now(UTC).replace(tzinfo=None)

    # 1. Delivered order: 2 x var1 (unit: 300k, cost: 100k) -> Rev: 600k, COGS: 200k
    o1 = _create_order_with_items(
        test_db,
        order_number="ORD-DELIVERED-1",
        status="delivered",
        items_data=[{"variant_id": 1, "unit_price": 300000, "cost_price": 100000, "quantity": 2}],
        payment_status="succeeded",
        payment_amount=600000,
    )

    # 2. Completed order: 3 x var2 (unit: 150k, cost: 50k) -> Rev: 450k, COGS: 150k
    o2 = _create_order_with_items(
        test_db,
        order_number="ORD-COMPLETED-2",
        status="completed",
        items_data=[{"variant_id": 2, "unit_price": 150000, "cost_price": 50000, "quantity": 3}],
        payment_status="succeeded",
        payment_amount=450000,
    )

    # 3. Cancelled order: 1 x var1 (unit: 300k, cost: 100k) -> Must NOT be in COGS
    _create_order_with_items(
        test_db,
        order_number="ORD-CANCELLED-3",
        status="cancelled",
        items_data=[{"variant_id": 1, "unit_price": 300000, "cost_price": 100000, "quantity": 1}],
        payment_status=None,
    )

    # 4. Payment failed order: 1 x var1 -> Must NOT be in COGS
    _create_order_with_items(
        test_db,
        order_number="ORD-FAILED-4",
        status="payment_failed",
        items_data=[{"variant_id": 1, "unit_price": 300000, "cost_price": 100000, "quantity": 1}],
        payment_status="failed",
        payment_amount=300000,
    )

    # 5. Shipping order: 1 x var1 -> Must NOT be in COGS (not fulfilled yet)
    _create_order_with_items(
        test_db,
        order_number="ORD-SHIPPING-5",
        status="shipping",
        items_data=[{"variant_id": 1, "unit_price": 300000, "cost_price": 100000, "quantity": 1}],
        payment_status="succeeded",
        payment_amount=300000,
    )

    # 6. Failed delivery (boom) order: 1 x var1 -> Must NOT be in COGS, boom_orders_count += 1
    _create_order_with_items(
        test_db,
        order_number="ORD-BOOM-6",
        status="failed_delivery",
        items_data=[{"variant_id": 1, "unit_price": 300000, "cost_price": 100000, "quantity": 1}],
        payment_status=None,
    )

    # 7. Returned order 1: 1 x var1 -> Must NOT be in COGS, return_orders_count += 1
    _create_order_with_items(
        test_db,
        order_number="ORD-RETURN-7",
        status="returned",
        items_data=[{"variant_id": 1, "unit_price": 300000, "cost_price": 100000, "quantity": 1}],
        payment_status=None,
    )

    # 8. Returned order 2: 1 x var2 -> return_orders_count += 1
    _create_order_with_items(
        test_db,
        order_number="ORD-RETURN-8",
        status="returned",
        items_data=[{"variant_id": 2, "unit_price": 150000, "cost_price": 50000, "quantity": 1}],
        payment_status=None,
    )

    # Add a refund on o2 payment: 50,000 VND
    o2_payment = test_db.scalar(select(Payment).where(Payment.order_id == o2.order_id))
    test_db.add(
        Refund(
            public_id=uuid7(),
            payment_id=o2_payment.payment_id,
            refund_idempotency_key=f"ref-{uuid.uuid4().hex[:30]}",
            status="succeeded",
            currency_code="VND",
            amount_vnd=50000,
            reason="Khách trả một phần",
            requested_by_customer_id=10,
            completed_at=now,
        )
    )
    test_db.commit()

    # Calculation:
    # gross_revenue = o1 (600k) + o2 (450k) + shipping_order (300k) = 1,350,000 VND
    # refunded_amount = 50,000 VND
    # net_revenue = 1,350,000 - 50,000 = 1,300,000 VND
    # COGS (o1 delivered + o2 completed) = (2 * 100,000) + (3 * 50,000) = 200,000 + 150,000 = 350,000 VND
    # gross_profit = 1,300,000 - 350,000 = 950,000 VND
    # gross_margin = round((950,000 / 1,300,000) * 100, 1) = round(73.0769..., 1) = 73.1%
    # boom_orders_count = 1 (ORD-BOOM-6)
    # return_orders_count = 2 (ORD-RETURN-7, ORD-RETURN-8)

    res = admin_client.get("/api/v1/admin/overview")
    assert res.status_code == 200, res.text
    data = res.json()

    assert data["gross_revenue_vnd"] == 1350000
    assert data["refunded_amount_vnd"] == 50000
    assert data["net_revenue_vnd"] == 1300000
    assert data["cogs_vnd"] == 350000
    assert data["gross_profit_vnd"] == 950000
    assert data["gross_margin_percent"] == 73.1
    assert data["boom_orders_count"] == 1
    assert data["return_orders_count"] == 2
