import sqlite3
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import create_engine, event, select
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.sql.elements import TextClause

from app.core.ids import uuid7
from app.db.base import Base
from app.db.deps import get_current_customer, verify_csrf
import app.db.uow
from app.main import app as fastapi_app
import app.models  # noqa: F401
from app.models.cart import Cart, CartItem
from app.models.catalog import Category, Product, ProductVariant
from app.models.customer import Customer
from app.models.inventory import Inventory
from app.models.order import Order, OrderStatusHistory, Payment
from app.modules.checkout.schemas import CheckoutRequest, CheckoutResultResponse


@compiles(TextClause, "sqlite")
def _compile_text(element, compiler, **kw):
    val = element.text
    if "CURRENT_TIMESTAMP(6)" in val:
        return val.replace("CURRENT_TIMESTAMP(6)", "CURRENT_TIMESTAMP")
    return val


@compiles(BIGINT, "sqlite")
def _compile_bigint(element, compiler, **kw):
    return "INTEGER"


@pytest.fixture(autouse=True)
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

    db = testing_session()
    # Seed catalog
    cat = Category(category_id=1, public_id=uuid7(), code="AO-NAM", name="Áo Nam", is_active=True)
    prod = Product(product_id=1, public_id=uuid7(), category_id=1, slug="ao-polo", name="Áo Polo Nam", is_active=True)
    var = ProductVariant(
        variant_id=1,
        public_id=uuid7(),
        product_id=1,
        sku="APN-001",
        size_code="L",
        color_code="DEN",
        price_vnd=300000,
        is_active=True,
    )
    inv = Inventory(variant_id=1, opening_on_hand=100, on_hand=100, version=1)

    # Seed customers
    c1 = Customer(
        customer_id=1,
        public_id=uuid7(),
        role="customer",
        display_name="Danh Tran",
        status="active",
        is_cod_blocked=False,
        boom_count=0,
    )
    c2 = Customer(
        customer_id=2,
        public_id=uuid7(),
        role="customer",
        display_name="Boomer Customer",
        status="active",
        is_cod_blocked=True,
        boom_count=3,
    )

    db.add_all([cat, prod, var, inv, c1, c2])
    db.commit()

    yield testing_session

    Base.metadata.drop_all(engine)


@pytest.fixture()
def test_db(setup_db):
    session = setup_db()
    try:
        yield session
    finally:
        session.close()


def create_active_cart(session, customer_id: int, variant_id: int = 1, quantity: int = 1) -> Cart:
    cart = Cart(public_id=uuid7(), customer_id=customer_id, status="active")
    session.add(cart)
    session.flush()
    item = CartItem(cart_id=cart.cart_id, variant_id=variant_id, quantity=quantity, is_present=True)
    session.add(item)
    session.commit()
    return cart


@pytest.fixture()
def customer_token_headers(test_db):
    customer = test_db.execute(select(Customer).where(Customer.customer_id == 1)).scalar_one()
    fastapi_app.dependency_overrides[get_current_customer] = lambda: customer
    fastapi_app.dependency_overrides[verify_csrf] = lambda: None
    yield {
        "Authorization": "Bearer normal-token",
        "Idempotency-Key": "idemp-customer-cod-1",
    }
    fastapi_app.dependency_overrides.pop(get_current_customer, None)
    fastapi_app.dependency_overrides.pop(verify_csrf, None)


@pytest.fixture()
def blocked_customer_headers(test_db):
    customer = test_db.execute(select(Customer).where(Customer.customer_id == 2)).scalar_one()
    fastapi_app.dependency_overrides[get_current_customer] = lambda: customer
    fastapi_app.dependency_overrides[verify_csrf] = lambda: None
    yield {
        "Authorization": "Bearer blocked-token",
        "Idempotency-Key": "idemp-blocked-cod-1",
    }
    fastapi_app.dependency_overrides.pop(get_current_customer, None)
    fastapi_app.dependency_overrides.pop(verify_csrf, None)


def test_checkout_cod_success(client: TestClient, customer_token_headers: dict[str, str], test_db):
    create_active_cart(test_db, customer_id=1, variant_id=1, quantity=1)

    payload = {
        "receiver_name": "Danh Tran",
        "receiver_phone": "0912345678",
        "shipping_address_text": "123 Le Loi, Ben Nghe, Quan 1, TP HCM",
        "payment_method": "cod",
    }
    res = client.post("/api/v1/checkout", json=payload, headers=customer_token_headers)
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["status"] == "confirmed"
    assert data["payment_status"] == "pending"
    assert data.get("payment_method") == "cod"

    # Verify order and payment in DB
    order = test_db.execute(select(Order).where(Order.order_number == data["order_number"])).scalar_one()
    assert order.status == "confirmed"
    assert order.payment_method == "cod"
    assert order.paid_at is None
    assert order.confirmed_at is not None

    payment = test_db.execute(select(Payment).where(Payment.order_id == order.order_id)).scalar_one()
    assert payment.status == "pending"

    histories = (
        test_db.execute(
            select(OrderStatusHistory)
            .where(OrderStatusHistory.order_id == order.order_id)
            .order_by(OrderStatusHistory.order_status_history_id)
        )
        .scalars()
        .all()
    )
    assert len(histories) == 1
    assert histories[0].from_status is None
    assert histories[0].to_status == "confirmed"
    assert histories[0].transition_source == "checkout"
    assert histories[0].transition_idempotency_key == f"{customer_token_headers['Idempotency-Key']}:confirmed"


def test_checkout_cod_blocked(client: TestClient, blocked_customer_headers: dict[str, str], test_db):
    create_active_cart(test_db, customer_id=2, variant_id=1, quantity=1)

    payload = {
        "receiver_name": "Boomer",
        "receiver_phone": "0999999999",
        "shipping_address_text": "456 Tran Hung Dao, TP HCM",
        "payment_method": "cod",
    }
    res = client.post("/api/v1/checkout", json=payload, headers=blocked_customer_headers)
    assert res.status_code == 403, res.text
    data = res.json()
    error_msg = data.get("message") or data.get("error", {}).get("message", "")
    assert "khóa phương thức COD" in error_msg


def test_checkout_cod_blocked_customer_can_vietqr(client: TestClient, blocked_customer_headers: dict[str, str], test_db):
    create_active_cart(test_db, customer_id=2, variant_id=1, quantity=1)

    headers = {**blocked_customer_headers, "Idempotency-Key": "idemp-blocked-vietqr-1"}
    payload = {
        "receiver_name": "Boomer",
        "receiver_phone": "0999999999",
        "shipping_address_text": "456 Tran Hung Dao, TP HCM",
        "payment_method": "vietqr",
    }
    res = client.post("/api/v1/checkout", json=payload, headers=headers)
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["status"] == "paid"
    assert data["payment_status"] == "succeeded"
    assert data.get("payment_method") == "vietqr"

    # Verify order in DB
    order = test_db.execute(select(Order).where(Order.order_number == data["order_number"])).scalar_one()
    assert order.status == "paid"
    assert order.payment_method == "vietqr"
    assert order.paid_at is not None

    payment = test_db.execute(select(Payment).where(Payment.order_id == order.order_id)).scalar_one()
    assert payment.status == "succeeded"

    histories = (
        test_db.execute(
            select(OrderStatusHistory)
            .where(OrderStatusHistory.order_id == order.order_id)
            .order_by(OrderStatusHistory.order_status_history_id)
        )
        .scalars()
        .all()
    )
    assert len(histories) == 1
    assert histories[0].to_status == "paid"
    assert histories[0].transition_idempotency_key == f"{headers['Idempotency-Key']}:paid"


def test_checkout_request_schema():
    # Valid COD
    req_cod = CheckoutRequest(
        receiver_name="Danh Tran",
        receiver_phone="0912345678",
        shipping_address_text="123 Le Loi, Quan 1",
        payment_method="cod",
    )
    assert req_cod.payment_method == "cod"

    # Valid VietQR explicitly
    req_vqr = CheckoutRequest(
        receiver_name="Danh Tran",
        receiver_phone="0912345678",
        shipping_address_text="123 Le Loi, Quan 1",
        payment_method="vietqr",
    )
    assert req_vqr.payment_method == "vietqr"

    # Default is vietqr
    req_default = CheckoutRequest(
        receiver_name="Danh Tran",
        receiver_phone="0912345678",
        shipping_address_text="123 Le Loi, Quan 1",
    )
    assert req_default.payment_method == "vietqr"

    # Invalid payment method rejected
    with pytest.raises(ValidationError):
        CheckoutRequest(
            receiver_name="Danh Tran",
            receiver_phone="0912345678",
            shipping_address_text="123 Le Loi, Quan 1",
            payment_method="credit_card",  # type: ignore
        )


def test_checkout_result_response_schema():
    resp = CheckoutResultResponse(
        order_number="OD123",
        status="confirmed",
        payment_status="pending",
        failure_code=None,
        coupon_code=None,
        subtotal_vnd=100000,
        discount_amount_vnd=0,
        shipping_fee_vnd=30000,
        total_vnd=130000,
        payment_method="cod",
    )
    assert resp.payment_method == "cod"
