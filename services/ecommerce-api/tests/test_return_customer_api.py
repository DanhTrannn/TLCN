"""Integration tests for Customer Returns API (Gói 2) - Task 2."""

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
from app.db.deps import get_current_customer, get_db, verify_csrf
import app.db.deps
import app.db.uow
from app.main import app as fastapi_app
import app.models  # noqa: F401
from app.models.catalog import Category, Product, ProductVariant
from app.models.customer import Customer
from app.models.inventory import Inventory
from app.models.order import Order, OrderItem, Payment
from app.models.promotion import Coupon
from app.models.returns import ReturnRequest


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
    cat = Category(category_id=1, public_id=uuid7(), code="AO-NAM", name="Áo Nam", is_active=True)
    prod = Product(product_id=1, public_id=uuid7(), category_id=1, slug="ao-polo", name="Áo Polo Nam", is_active=True)
    var1 = ProductVariant(
        variant_id=1, public_id=uuid7(), product_id=1, sku="APN-001",
        size_code="L", color_code="DEN", price_vnd=300000, is_active=True,
    )
    var2 = ProductVariant(
        variant_id=2, public_id=uuid7(), product_id=1, sku="APN-002",
        size_code="M", color_code="TRANG", price_vnd=150000, is_active=True,
    )
    db.add_all([cat, prod, var1, var2])
    now = datetime.now(UTC).replace(tzinfo=None)
    db.add_all([
        Coupon(
            coupon_id=1, public_id=uuid7(), code_normalized="SALE10",
            discount_type="percentage", discount_value=10, minimum_subtotal_vnd=0,
            starts_at=now - timedelta(days=30), ends_at=now + timedelta(days=30),
            is_active=True, used_count=0,
        ),
        Inventory(variant_id=1, opening_on_hand=100, on_hand=98, version=1),
        Inventory(variant_id=2, opening_on_hand=50, on_hand=49, version=1),
    ])
    db.add_all([
        Customer(customer_id=1, public_id=uuid7(), role="customer", display_name="Khách Một", status="active"),
        Customer(customer_id=2, public_id=uuid7(), role="customer", display_name="Khách Hai", status="active"),
        Customer(customer_id=10, public_id=uuid7(), role="admin", display_name="Quản Trị", status="active"),
    ])
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


def create_completed_order(
    session,
    order_number: str = "ORD-RT-001",
    customer_id: int = 1,
    status: str = "completed",
    completed_at: datetime | None = None,
    subtotal_vnd: int = 750000,
    discount_amount_vnd: int = 75000,
    shipping_fee_vnd: int = 30000,
) -> Order:
    now = datetime.now(UTC).replace(tzinfo=None)
    order = Order(
        order_number=order_number,
        customer_id=customer_id,
        checkout_idempotency_key=f"chk-{uuid.uuid4().hex[:30]}",
        status=status,
        coupon_id=1 if discount_amount_vnd > 0 else None,
        subtotal_vnd=subtotal_vnd,
        discount_amount_vnd=discount_amount_vnd,
        shipping_fee_vnd=shipping_fee_vnd,
        total_vnd=subtotal_vnd - discount_amount_vnd + shipping_fee_vnd,
        receiver_name="Khách Một",
        receiver_phone="0900000001",
        shipping_address_text="123 Đường Test, TP.HCM",
        coupon_code_snapshot="SALE10" if discount_amount_vnd > 0 else None,
        coupon_type_snapshot="percentage" if discount_amount_vnd > 0 else None,
        coupon_value_snapshot=10 if discount_amount_vnd > 0 else None,
        completed_at=completed_at if completed_at is not None else now,
    )
    session.add(order)
    session.flush()
    session.add_all([
        OrderItem(
            public_id=uuid7(), order_id=order.order_id, variant_id=1,
            product_public_id_snapshot=uuid7(), category_code_snapshot="AO-NAM",
            category_name_snapshot="Áo Nam", product_name_snapshot="Áo Polo Nam",
            sku_snapshot="APN-001", size_code_snapshot="L", color_code_snapshot="DEN",
            unit_price_vnd=300000, quantity=2, line_total_vnd=600000,
        ),
        OrderItem(
            public_id=uuid7(), order_id=order.order_id, variant_id=2,
            product_public_id_snapshot=uuid7(), category_code_snapshot="AO-NAM",
            category_name_snapshot="Áo Nam", product_name_snapshot="Áo Polo Nam",
            sku_snapshot="APN-002", size_code_snapshot="M", color_code_snapshot="TRANG",
            unit_price_vnd=150000, quantity=1, line_total_vnd=150000,
        ),
    ])
    session.add(
        Payment(
            payment_reference=f"PAY-{order_number}",
            order_id=order.order_id,
            payment_idempotency_key=f"pay-{uuid.uuid4().hex[:30]}",
            status="succeeded",
            amount_vnd=order.total_vnd,
            attempted_at=now,
        )
    )
    session.commit()
    return order


@pytest.fixture()
def customer_headers(test_db):
    customer = test_db.execute(select(Customer).where(Customer.customer_id == 1)).scalar_one()
    fastapi_app.dependency_overrides[get_current_customer] = lambda: customer
    fastapi_app.dependency_overrides[verify_csrf] = lambda: None
    yield {"Authorization": "Bearer customer-token", "Idempotency-Key": "idemp-return-1"}
    fastapi_app.dependency_overrides.pop(get_current_customer, None)
    fastapi_app.dependency_overrides.pop(verify_csrf, None)


RETURN_PAYLOAD = {
    "customer_reason": "Áo bị lỗi đường may sau khi giặt lần đầu",
    "bank_name": "Vietcombank",
    "bank_account_number": "0123456789",
    "bank_account_holder": "NGUYEN VAN A",
    "image_urls": ["https://example.com/img1.jpg"],
    "items": [{"order_item_id": 1, "quantity": 1}],
}


def test_create_return_within_7_days_succeeds(client: TestClient, test_db, customer_headers):
    create_completed_order(test_db)
    resp = client.post(
        "/api/v1/orders/ORD-RT-001/returns", json=RETURN_PAYLOAD, headers=customer_headers
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "pending_review"
    assert body["order_number"] == "ORD-RT-001"
    assert body["return_code"].startswith("RT-")
    assert body["total_refund_amount_vnd"] == 270000  # 300000 * (1 - 75000/750000)


def test_create_return_rejects_non_delivered_order(client: TestClient, test_db, customer_headers):
    create_completed_order(test_db, status="shipping")
    resp = client.post(
        "/api/v1/orders/ORD-RT-001/returns", json=RETURN_PAYLOAD, headers=customer_headers
    )
    assert resp.status_code == 409, resp.text


def test_create_return_rejects_after_7_days(client: TestClient, test_db, customer_headers):
    old_date = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=8)
    create_completed_order(test_db, completed_at=old_date)
    resp = client.post(
        "/api/v1/orders/ORD-RT-001/returns", json=RETURN_PAYLOAD, headers=customer_headers
    )
    assert resp.status_code == 400, resp.text


def test_create_return_rejects_when_active_return_exists(client: TestClient, test_db, customer_headers):
    create_completed_order(test_db)
    first = client.post(
        "/api/v1/orders/ORD-RT-001/returns", json=RETURN_PAYLOAD, headers=customer_headers
    )
    assert first.status_code == 200, first.text

    headers2 = dict(customer_headers)
    headers2["Idempotency-Key"] = "idemp-return-2"
    second = client.post(
        "/api/v1/orders/ORD-RT-001/returns", json=RETURN_PAYLOAD, headers=headers2
    )
    assert second.status_code == 409, second.text


def test_create_return_is_idempotent_with_same_key(client: TestClient, test_db, customer_headers):
    create_completed_order(test_db)
    first = client.post(
        "/api/v1/orders/ORD-RT-001/returns", json=RETURN_PAYLOAD, headers=customer_headers
    )
    replay = client.post(
        "/api/v1/orders/ORD-RT-001/returns", json=RETURN_PAYLOAD, headers=customer_headers
    )
    assert replay.status_code == 200, replay.text
    assert replay.json()["return_code"] == first.json()["return_code"]
    assert len(test_db.execute(select(ReturnRequest)).scalars().all()) == 1


def test_list_and_detail_returns(client: TestClient, test_db, customer_headers):
    create_completed_order(test_db)
    created = client.post(
        "/api/v1/orders/ORD-RT-001/returns", json=RETURN_PAYLOAD, headers=customer_headers
    )
    return_code = created.json()["return_code"]

    listing = client.get("/api/v1/returns", headers=customer_headers)
    assert listing.status_code == 200, listing.text
    items = listing.json()["items"]
    assert len(items) == 1
    assert items[0]["return_code"] == return_code
    assert items[0]["total_refund_amount_vnd"] == 270000

    detail = client.get(f"/api/v1/returns/{return_code}", headers=customer_headers)
    assert detail.status_code == 200, detail.text
    body = detail.json()
    assert body["return_code"] == return_code
    assert body["bank_info"]["bank_name"] == "Vietcombank"
    assert body["image_urls"] == ["https://example.com/img1.jpg"]
    assert len(body["items"]) == 1
    assert body["items"][0]["refund_amount_vnd"] == 270000


def test_cancel_return_when_pending_review(client: TestClient, test_db, customer_headers):
    create_completed_order(test_db)
    created = client.post(
        "/api/v1/orders/ORD-RT-001/returns", json=RETURN_PAYLOAD, headers=customer_headers
    )
    return_code = created.json()["return_code"]

    cancelled = client.post(
        f"/api/v1/returns/{return_code}/cancel", headers=customer_headers
    )
    assert cancelled.status_code == 200, cancelled.text
    assert cancelled.json()["status"] == "cancelled"

