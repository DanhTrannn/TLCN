"""Integration tests for Admin Returns Management API (Gói 2) - Task 3."""

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
from app.models.inventory import Inventory
from app.models.inventory_tx import InventoryTransaction
from app.models.order import Order, OrderItem, OrderStatusHistory, Payment, Refund
from app.models.promotion import Coupon
from app.models.returns import ReturnItem, ReturnRequest


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
    now = datetime.now(UTC).replace(tzinfo=None)
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
        completed_at=now,
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


RETURN_PAYLOAD = {
    "customer_reason": "Áo bị lỗi đường may sau khi giặt lần đầu",
    "bank_name": "Vietcombank",
    "bank_account_number": "0123456789",
    "bank_account_holder": "NGUYEN VAN A",
    "image_urls": ["https://example.com/img1.jpg"],
    "items": [{"order_item_id": 1, "quantity": 2}],
}


@pytest.fixture()
def customer_headers(test_db):
    customer = test_db.execute(select(Customer).where(Customer.customer_id == 1)).scalar_one()
    fastapi_app.dependency_overrides[get_current_customer] = lambda: customer
    fastapi_app.dependency_overrides[verify_csrf] = lambda: None
    yield {"Authorization": "Bearer customer-token", "Idempotency-Key": "idemp-return-c1"}
    fastapi_app.dependency_overrides.pop(get_current_customer, None)
    fastapi_app.dependency_overrides.pop(verify_csrf, None)


@pytest.fixture()
def admin_headers(test_db):
    admin = test_db.execute(select(Customer).where(Customer.customer_id == 10)).scalar_one()
    fastapi_app.dependency_overrides[get_current_admin] = lambda: admin
    fastapi_app.dependency_overrides[verify_csrf] = lambda: None
    yield {"Authorization": "Bearer admin-token", "Idempotency-Key": "idemp-return-a1"}
    fastapi_app.dependency_overrides.pop(get_current_admin, None)
    fastapi_app.dependency_overrides.pop(verify_csrf, None)


def _create_pending_return(client, customer_headers) -> str:
    create_return = client.post(
        "/api/v1/orders/ORD-RT-001/returns", json=RETURN_PAYLOAD, headers=customer_headers
    )
    assert create_return.status_code == 200, create_return.text
    return create_return.json()["return_code"]


def _advance_status(client, admin_headers, return_code: str, status: str) -> None:
    if status == "approved":
        resp = client.post(
            f"/api/v1/admin/returns/{return_code}/review",
            json={"action": "approved"},
            headers=admin_headers,
        )
        assert resp.status_code == 200, resp.text
    elif status == "goods_received":
        _advance_status(client, admin_headers, return_code, "approved")
        resp = client.post(
            f"/api/v1/admin/returns/{return_code}/receive", headers=admin_headers
        )
        assert resp.status_code == 200, resp.text



def test_admin_review_approves_and_rejects(client: TestClient, test_db, customer_headers, admin_headers):
    create_completed_order(test_db)
    return_code = _create_pending_return(client, customer_headers)

    approved = client.post(
        f"/api/v1/admin/returns/{return_code}/review",
        json={"action": "approved"},
        headers=admin_headers,
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["status"] == "approved"
    assert approved.json()["reviewed_at"] is not None

    # Rejected flow on a second order
    create_completed_order(test_db, order_number="ORD-RT-002")
    code2 = client.post(
        "/api/v1/orders/ORD-RT-002/returns",
        json={**RETURN_PAYLOAD, "items": [{"order_item_id": 3, "quantity": 2}]},
        headers=customer_headers,
    ).json()["return_code"]
    rejected = client.post(
        f"/api/v1/admin/returns/{code2}/review",
        json={"action": "rejected", "admin_note": "Hàng không đáp ứng điều kiện đổi trả."},
        headers=admin_headers,
    )
    assert rejected.status_code == 200, rejected.text
    assert rejected.json()["status"] == "rejected"
    assert rejected.json()["admin_note"] == "Hàng không đáp ứng điều kiện đổi trả."


def test_admin_receive_moves_to_goods_received(client: TestClient, test_db, customer_headers, admin_headers):
    create_completed_order(test_db)
    return_code = _create_pending_return(client, customer_headers)
    _advance_status(client, admin_headers, return_code, "approved")

    received = client.post(
        f"/api/v1/admin/returns/{return_code}/receive", headers=admin_headers
    )
    assert received.status_code == 200, received.text
    assert received.json()["status"] == "goods_received"


def test_inspect_resolve_passed_partial_return(client: TestClient, test_db, customer_headers, admin_headers):
    create_completed_order(test_db)
    return_code = _create_pending_return(client, customer_headers)
    _advance_status(client, admin_headers, return_code, "goods_received")

    resolve = client.post(
        f"/api/v1/admin/returns/{return_code}/inspect-and-resolve",
        json={
            "items": [{"return_item_id": 1, "inspection_status": "passed"}],
            "admin_note": "Hàng đạt chuẩn, nhập lại kho.",
        },
        headers=admin_headers,
    )
    assert resolve.status_code == 200, resolve.text
    body = resolve.json()
    assert body["status"] == "completed"
    assert body["resolved_at"] is not None

    test_db.expire_all()
    # Inventory restocked: 98 + 2 = 100
    inv = test_db.execute(select(Inventory).where(Inventory.variant_id == 1)).scalar_one()
    assert inv.on_hand == 100

    # InventoryTransaction recorded
    tx = test_db.execute(
        select(InventoryTransaction).where(
            InventoryTransaction.movement_type == "return_customer"
        )
    ).scalar_one()
    assert tx.quantity_delta == 2
    assert tx.reference_code == return_code
    assert tx.location_type == "central_warehouse"

    # Refund created
    refund = test_db.execute(select(Refund)).scalar_one()
    assert refund.status == "succeeded"
    assert refund.amount_vnd == 540000  # 2 * 300000 * 0.9

    # Partial return (2 of 3 units): order stays completed
    order = test_db.execute(select(Order).where(Order.order_number == "ORD-RT-001")).scalar_one()
    assert order.status == "completed"


def test_inspect_resolve_full_return_moves_order_to_returned(client: TestClient, test_db, customer_headers, admin_headers):
    create_completed_order(test_db)
    payload = dict(RETURN_PAYLOAD)
    payload["items"] = [
        {"order_item_id": 1, "quantity": 2},
        {"order_item_id": 2, "quantity": 1},
    ]
    created = client.post(
        "/api/v1/orders/ORD-RT-001/returns", json=payload, headers=customer_headers
    )
    return_code = created.json()["return_code"]
    _advance_status(client, admin_headers, return_code, "goods_received")

    resolve = client.post(
        f"/api/v1/admin/returns/{return_code}/inspect-and-resolve",
        json={
            "items": [
                {"return_item_id": 1, "inspection_status": "passed"},
                {"return_item_id": 2, "inspection_status": "passed"},
            ],
        },
        headers=admin_headers,
    )
    assert resolve.status_code == 200, resolve.text
    assert resolve.json()["status"] == "completed"

    test_db.expire_all()
    order = test_db.execute(select(Order).where(Order.order_number == "ORD-RT-001")).scalar_one()
    assert order.status == "returned"
    history = test_db.execute(
        select(OrderStatusHistory).where(
            OrderStatusHistory.order_id == order.order_id,
            OrderStatusHistory.to_status == "returned",
        )
    ).scalar_one()
    assert history.transition_source == "admin_return"
    assert history.from_status == "completed"

    # Both variants restocked
    inv1 = test_db.execute(select(Inventory).where(Inventory.variant_id == 1)).scalar_one()
    inv2 = test_db.execute(select(Inventory).where(Inventory.variant_id == 2)).scalar_one()
    assert inv1.on_hand == 100
    assert inv2.on_hand == 50


def test_inspect_resolve_failed_items_no_restock_no_refund(client: TestClient, test_db, customer_headers, admin_headers):
    create_completed_order(test_db)
    return_code = _create_pending_return(client, customer_headers)
    _advance_status(client, admin_headers, return_code, "goods_received")

    resolve = client.post(
        f"/api/v1/admin/returns/{return_code}/inspect-and-resolve",
        json={"items": [{"return_item_id": 1, "inspection_status": "failed"}]},
        headers=admin_headers,
    )
    assert resolve.status_code == 200, resolve.text
    assert resolve.json()["status"] == "completed"
    assert resolve.json()["items"][0]["inspection_status"] == "failed"

    test_db.expire_all()
    inv = test_db.execute(select(Inventory).where(Inventory.variant_id == 1)).scalar_one()
    assert inv.on_hand == 98  # unchanged
    assert test_db.execute(select(InventoryTransaction)).scalars().all() == []
    assert test_db.execute(select(Refund)).scalars().all() == []


def test_inspect_and_resolve_is_idempotent(client: TestClient, test_db, customer_headers, admin_headers):
    create_completed_order(test_db)
    return_code = _create_pending_return(client, customer_headers)
    _advance_status(client, admin_headers, return_code, "goods_received")

    payload = {"items": [{"return_item_id": 1, "inspection_status": "passed"}]}
    first = client.post(
        f"/api/v1/admin/returns/{return_code}/inspect-and-resolve",
        json=payload,
        headers=admin_headers,
    )
    assert first.status_code == 200, first.text

    replay = client.post(
        f"/api/v1/admin/returns/{return_code}/inspect-and-resolve",
        json=payload,
        headers=admin_headers,
    )
    assert replay.status_code == 200, replay.text
    assert replay.json()["return_code"] == return_code
    assert replay.json()["status"] == "completed"

    test_db.expire_all()
    # No duplicate side effects
    inv = test_db.execute(select(Inventory).where(Inventory.variant_id == 1)).scalar_one()
    assert inv.on_hand == 100
    assert len(test_db.execute(select(InventoryTransaction)).scalars().all()) == 1
    assert len(test_db.execute(select(Refund)).scalars().all()) == 1


def test_admin_list_and_detail(client: TestClient, test_db, customer_headers, admin_headers):
    create_completed_order(test_db)
    return_code = _create_pending_return(client, customer_headers)

    listing = client.get("/api/v1/admin/returns", headers=admin_headers)
    assert listing.status_code == 200, listing.text
    assert listing.json()["total"] == 1
    assert listing.json()["items"][0]["return_code"] == return_code

    detail = client.get(f"/api/v1/admin/returns/{return_code}", headers=admin_headers)
    assert detail.status_code == 200, detail.text
    assert detail.json()["return_code"] == return_code
    assert detail.json()["items"][0]["quantity"] == 2


def test_inspect_and_resolve_rejects_duplicate_return_item_ids(
    client: TestClient, test_db, customer_headers, admin_headers
):
    create_completed_order(test_db)
    return_code = _create_pending_return(client, customer_headers)
    _advance_status(client, admin_headers, return_code, "goods_received")

    resolve = client.post(
        f"/api/v1/admin/returns/{return_code}/inspect-and-resolve",
        json={
            "items": [
                {"return_item_id": 1, "inspection_status": "passed"},
                {"return_item_id": 1, "inspection_status": "failed"},
            ]
        },
        headers=admin_headers,
    )
    assert resolve.status_code == 422, resolve.text


def test_inspect_with_all_failed_items_does_not_mark_order_returned(
    client: TestClient, test_db, customer_headers, admin_headers
):
    create_completed_order(test_db)
    # Return all ordered items (item 1: 2 units, item 2: 1 unit)
    payload = dict(RETURN_PAYLOAD)
    payload["items"] = [
        {"order_item_id": 1, "quantity": 2},
        {"order_item_id": 2, "quantity": 1},
    ]
    created = client.post(
        "/api/v1/orders/ORD-RT-001/returns", json=payload, headers=customer_headers
    )
    return_code = created.json()["return_code"]
    _advance_status(client, admin_headers, return_code, "goods_received")

    # Inspect with ALL failed
    resolve = client.post(
        f"/api/v1/admin/returns/{return_code}/inspect-and-resolve",
        json={
            "items": [
                {"return_item_id": 1, "inspection_status": "failed"},
                {"return_item_id": 2, "inspection_status": "failed"},
            ],
        },
        headers=admin_headers,
    )
    assert resolve.status_code == 200, resolve.text
    assert resolve.json()["status"] == "completed"

    test_db.expire_all()
    order = test_db.execute(select(Order).where(Order.order_number == "ORD-RT-001")).scalar_one()
    # Order status must REMAIN completed, NOT returned!
    assert order.status == "completed"
    returned_history = test_db.execute(
        select(OrderStatusHistory).where(
            OrderStatusHistory.order_id == order.order_id,
            OrderStatusHistory.to_status == "returned",
        )
    ).scalars().all()
    assert len(returned_history) == 0


def test_cumulative_refund_amount_capped_and_reason_truncated(
    client: TestClient, test_db, customer_headers, admin_headers
):
    order = create_completed_order(test_db)
    payment = test_db.execute(select(Payment).where(Payment.order_id == order.order_id)).scalar_one()
    # Pre-seed an existing refund with long reason and high amount
    existing_refund = Refund(
        public_id=uuid.uuid4(),
        payment_id=payment.payment_id,
        refund_idempotency_key="ref:seed",
        status="succeeded",
        amount_vnd=payment.amount_vnd - 1000,
        reason="A" * 495,
        requested_by_customer_id=order.customer_id,
        completed_at=datetime.now(UTC).replace(tzinfo=None),
    )
    test_db.add(existing_refund)
    test_db.commit()

    return_code = _create_pending_return(client, customer_headers)
    _advance_status(client, admin_headers, return_code, "goods_received")

    resolve = client.post(
        f"/api/v1/admin/returns/{return_code}/inspect-and-resolve",
        json={"items": [{"return_item_id": 1, "inspection_status": "passed"}]},
        headers=admin_headers,
    )
    assert resolve.status_code == 200, resolve.text

    test_db.expire_all()
    refund = test_db.execute(select(Refund).where(Refund.payment_id == payment.payment_id)).scalar_one()
    # Amount must be capped at payment.amount_vnd
    assert refund.amount_vnd == payment.amount_vnd
    # Reason must be capped at 500 chars
    assert len(refund.reason) <= 500

