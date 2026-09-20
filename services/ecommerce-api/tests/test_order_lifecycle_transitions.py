from datetime import datetime
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
from app.models.cart import Cart, CartItem
from app.models.catalog import Category, Product, ProductVariant
from app.models.customer import Customer
from app.models.inventory import Inventory
from app.models.logistics import DeliveryStaff, Shipment
from app.models.order import Order, OrderItem, OrderStatusHistory, Payment


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
    monkeypatch.setattr(app.db.deps, "SessionLocal", testing_session)

    def _get_test_db():
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    fastapi_app.dependency_overrides[get_db] = _get_test_db

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

    # Seed delivery staff
    staff_active = DeliveryStaff(
        staff_id=1,
        public_id=uuid7(),
        full_name="Nguyễn Văn Giao",
        phone="0901234567",
        vehicle_plate="59-A1 12345",
        is_active=True,
    )
    staff_inactive = DeliveryStaff(
        staff_id=2,
        public_id=uuid7(),
        full_name="Trần Nghỉ Việc",
        phone="0909999999",
        vehicle_plate="59-A1 99999",
        is_active=False,
    )

    # Seed customers
    c1 = Customer(
        customer_id=1,
        public_id=uuid7(),
        role="customer",
        display_name="Khách Hàng Một",
        status="active",
        is_cod_blocked=False,
        boom_count=0,
    )
    c2 = Customer(
        customer_id=2,
        public_id=uuid7(),
        role="customer",
        display_name="Khách Hàng Hai",
        status="active",
        is_cod_blocked=False,
        boom_count=2,
    )
    admin = Customer(
        customer_id=10,
        public_id=uuid7(),
        role="admin",
        display_name="Quản Trị Viên",
        status="active",
    )

    db.add_all([cat, prod, var, inv, staff_active, staff_inactive, c1, c2, admin])
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


def create_active_cart(session, customer_id: int, variant_id: int = 1, quantity: int = 1) -> Cart:
    cart = Cart(public_id=uuid7(), customer_id=customer_id, status="active")
    session.add(cart)
    session.flush()
    item = CartItem(cart_id=cart.cart_id, variant_id=variant_id, quantity=quantity, is_present=True)
    session.add(item)
    session.commit()
    return cart


@pytest.fixture()
def admin_headers(test_db):
    admin = test_db.execute(select(Customer).where(Customer.customer_id == 10)).scalar_one()
    fastapi_app.dependency_overrides[get_current_admin] = lambda: admin
    fastapi_app.dependency_overrides[verify_csrf] = lambda: None
    yield {
        "Authorization": "Bearer admin-token",
        "Idempotency-Key": "idemp-admin-1",
    }
    fastapi_app.dependency_overrides.pop(get_current_admin, None)
    fastapi_app.dependency_overrides.pop(verify_csrf, None)


@pytest.fixture()
def customer_headers(test_db):
    customer = test_db.execute(select(Customer).where(Customer.customer_id == 1)).scalar_one()
    fastapi_app.dependency_overrides[get_current_customer] = lambda: customer
    fastapi_app.dependency_overrides[verify_csrf] = lambda: None
    yield {
        "Authorization": "Bearer customer-token",
        "Idempotency-Key": "idemp-customer-1",
    }
    fastapi_app.dependency_overrides.pop(get_current_customer, None)
    fastapi_app.dependency_overrides.pop(verify_csrf, None)


@pytest.fixture()
def customer2_headers(test_db):
    customer = test_db.execute(select(Customer).where(Customer.customer_id == 2)).scalar_one()
    fastapi_app.dependency_overrides[get_current_customer] = lambda: customer
    fastapi_app.dependency_overrides[verify_csrf] = lambda: None
    yield {
        "Authorization": "Bearer customer2-token",
        "Idempotency-Key": "idemp-customer-2",
    }
    fastapi_app.dependency_overrides.pop(get_current_customer, None)
    fastapi_app.dependency_overrides.pop(verify_csrf, None)


def test_full_cod_order_lifecycle(
    client: TestClient, admin_headers: dict[str, str], customer_headers: dict[str, str], test_db
):
    create_active_cart(test_db, customer_id=1, variant_id=1, quantity=2)

    # 1. Checkout COD -> status='confirmed', payment_status='pending'
    checkout_payload = {
        "receiver_name": "Khách Hàng Một",
        "receiver_phone": "0912345678",
        "shipping_address_text": "123 Đường Số 1, Quận 1, TP HCM",
        "payment_method": "cod",
    }
    res_checkout = client.post("/api/v1/checkout", json=checkout_payload, headers=customer_headers)
    assert res_checkout.status_code == 200, res_checkout.text
    order_data = res_checkout.json()
    order_number = order_data["order_number"]
    assert order_data["status"] == "confirmed"
    assert order_data["payment_status"] == "pending"

    # 2. Dispatch with staff_id -> status='shipping', shipment created
    dispatch_payload = {
        "delivery_staff_id": 1,
        "notes": "Giao trong giờ hành chính",
    }
    res_dispatch = client.post(
        f"/api/v1/admin/orders/{order_number}/dispatch",
        json=dispatch_payload,
        headers=admin_headers,
    )
    assert res_dispatch.status_code == 200, res_dispatch.text
    dispatch_data = res_dispatch.json()
    assert dispatch_data["order_number"] == order_number
    assert dispatch_data["status"] == "shipping"

    # Verify order and shipment in DB
    order = test_db.execute(select(Order).where(Order.order_number == order_number)).scalar_one()
    assert order.status == "shipping"

    shipment = test_db.execute(select(Shipment).where(Shipment.order_id == order.order_id)).scalar_one()
    assert shipment.delivery_staff_id == 1
    assert shipment.status == "in_transit"
    assert shipment.cod_amount_vnd == order.total_vnd
    assert shipment.cod_collected_vnd == 0
    assert shipment.dispatched_at is not None
    assert shipment.notes == "Giao trong giờ hành chính"

    history_disp = (
        test_db.execute(
            select(OrderStatusHistory)
            .where(OrderStatusHistory.order_id == order.order_id, OrderStatusHistory.to_status == "shipping")
        )
        .scalar_one()
    )
    assert history_disp.from_status == "confirmed"
    assert history_disp.transition_source == "admin_dispatch"
    assert len(history_disp.transition_idempotency_key) <= 64

    # 3. Deliver -> status='delivered', payment='succeeded', order.paid_at set
    deliver_headers = {**admin_headers, "Idempotency-Key": "idemp-deliver-1"}
    res_deliver = client.post(
        f"/api/v1/admin/orders/{order_number}/deliver",
        headers=deliver_headers,
    )
    assert res_deliver.status_code == 200, res_deliver.text
    deliver_data = res_deliver.json()
    assert deliver_data["status"] == "delivered"

    test_db.refresh(order)
    assert order.status == "delivered"
    assert order.paid_at is not None

    test_db.refresh(shipment)
    assert shipment.status == "delivered"
    assert shipment.delivered_at is not None
    assert shipment.cod_collected_vnd == shipment.cod_amount_vnd

    payment = test_db.execute(select(Payment).where(Payment.order_id == order.order_id)).scalar_one()
    assert payment.status == "succeeded"

    history_deliv = (
        test_db.execute(
            select(OrderStatusHistory)
            .where(OrderStatusHistory.order_id == order.order_id, OrderStatusHistory.to_status == "delivered")
        )
        .scalar_one()
    )
    assert history_deliv.from_status == "shipping"
    assert history_deliv.transition_source == "admin_deliver"
    assert len(history_deliv.transition_idempotency_key) <= 64

    # 4. Complete -> status='completed', completed_at set
    complete_headers = {**admin_headers, "Idempotency-Key": "idemp-complete-1"}
    res_complete = client.post(
        f"/api/v1/admin/orders/{order_number}/complete",
        headers=complete_headers,
    )
    assert res_complete.status_code == 200, res_complete.text
    complete_data = res_complete.json()
    assert complete_data["status"] == "completed"

    test_db.refresh(order)
    assert order.status == "completed"
    assert order.completed_at is not None

    history_comp = (
        test_db.execute(
            select(OrderStatusHistory)
            .where(OrderStatusHistory.order_id == order.order_id, OrderStatusHistory.to_status == "completed")
        )
        .scalar_one()
    )
    assert history_comp.from_status == "delivered"
    assert history_comp.transition_source == "admin_complete"
    assert len(history_comp.transition_idempotency_key) <= 64


def test_cod_order_boom_handling(
    client: TestClient, admin_headers: dict[str, str], customer_headers: dict[str, str], test_db
):
    create_active_cart(test_db, customer_id=1, variant_id=1, quantity=2)

    # Initial inventory
    inv_before = test_db.execute(select(Inventory).where(Inventory.variant_id == 1)).scalar_one()
    assert inv_before.on_hand == 100

    # 1. Checkout COD (quantity 2)
    checkout_payload = {
        "receiver_name": "Khách Hàng Một",
        "receiver_phone": "0912345678",
        "shipping_address_text": "123 Đường Số 1, Quận 1, TP HCM",
        "payment_method": "cod",
    }
    res_checkout = client.post("/api/v1/checkout", json=checkout_payload, headers=customer_headers)
    assert res_checkout.status_code == 200, res_checkout.text
    order_number = res_checkout.json()["order_number"]

    test_db.refresh(inv_before)
    assert inv_before.on_hand == 98  # Reserved/deducted at checkout

    # 2. Dispatch
    res_dispatch = client.post(
        f"/api/v1/admin/orders/{order_number}/dispatch",
        json={"delivery_staff_id": 1},
        headers=admin_headers,
    )
    assert res_dispatch.status_code == 200, res_dispatch.text

    # 3. Failed delivery with reason
    failed_payload = {"reason": "Khách không nghe máy sau 3 cuộc gọi, từ chối nhận"}
    failed_headers = {**admin_headers, "Idempotency-Key": "idemp-failed-1"}
    res_failed = client.post(
        f"/api/v1/admin/orders/{order_number}/failed-delivery",
        json=failed_payload,
        headers=failed_headers,
    )
    assert res_failed.status_code == 200, res_failed.text
    failed_data = res_failed.json()
    assert failed_data["status"] == "failed_delivery"

    # Verify DB: Order status='failed_delivery'
    order = test_db.execute(select(Order).where(Order.order_number == order_number)).scalar_one()
    assert order.status == "failed_delivery"

    # Verify Shipment updated
    shipment = test_db.execute(select(Shipment).where(Shipment.order_id == order.order_id)).scalar_one()
    assert shipment.status == "failed"
    assert shipment.failure_reason == failed_payload["reason"]
    assert shipment.attempt_count == 2
    assert shipment.failed_at is not None

    # Verify Inventory restored
    test_db.refresh(inv_before)
    assert inv_before.on_hand == 100

    # Verify Customer boom_count incremented
    customer = test_db.execute(select(Customer).where(Customer.customer_id == 1)).scalar_one()
    test_db.refresh(customer)
    assert customer.boom_count == 1
    assert customer.is_cod_blocked is False

    # Verify OrderStatusHistory
    history = (
        test_db.execute(
            select(OrderStatusHistory)
            .where(OrderStatusHistory.order_id == order.order_id, OrderStatusHistory.to_status == "failed_delivery")
        )
        .scalar_one()
    )
    assert history.from_status == "shipping"
    assert history.transition_source == "admin_failed_delivery"
    assert history.reason == failed_payload["reason"]
    assert len(history.transition_idempotency_key) <= 64


def test_boom_handling_blocks_customer_on_third_boom(
    client: TestClient, admin_headers: dict[str, str], customer2_headers: dict[str, str], test_db
):
    # Customer 2 starts with boom_count=2
    customer = test_db.execute(select(Customer).where(Customer.customer_id == 2)).scalar_one()
    assert customer.boom_count == 2
    assert customer.is_cod_blocked is False

    create_active_cart(test_db, customer_id=2, variant_id=1, quantity=1)

    # 1. Checkout COD succeeds
    checkout_payload = {
        "receiver_name": "Khách Hàng Hai",
        "receiver_phone": "0987654321",
        "shipping_address_text": "456 Đường Số 2, Quận 3, TP HCM",
        "payment_method": "cod",
    }
    res_checkout = client.post("/api/v1/checkout", json=checkout_payload, headers=customer2_headers)
    assert res_checkout.status_code == 200, res_checkout.text
    order_number = res_checkout.json()["order_number"]

    # 2. Dispatch
    res_disp = client.post(
        f"/api/v1/admin/orders/{order_number}/dispatch",
        json={"delivery_staff_id": 1},
        headers=admin_headers,
    )
    assert res_disp.status_code == 200

    # 3. Failed delivery -> 3rd boom
    res_fail = client.post(
        f"/api/v1/admin/orders/{order_number}/failed-delivery",
        json={"reason": "Bom hàng lần 3"},
        headers=admin_headers,
    )
    assert res_fail.status_code == 200

    test_db.refresh(customer)
    assert customer.boom_count == 3
    assert customer.is_cod_blocked is True

    # 4. Next COD checkout must be blocked (403)
    create_active_cart(test_db, customer_id=2, variant_id=1, quantity=1)
    res_blocked = client.post(
        "/api/v1/checkout",
        json=checkout_payload,
        headers={**customer2_headers, "Idempotency-Key": "idemp-customer2-blocked"},
    )
    assert res_blocked.status_code == 403


def test_full_vietqr_order_lifecycle(
    client: TestClient, admin_headers: dict[str, str], customer_headers: dict[str, str], test_db
):
    create_active_cart(test_db, customer_id=1, variant_id=1, quantity=1)

    # 1. Checkout VietQR -> status='paid', payment_status='succeeded'
    checkout_payload = {
        "receiver_name": "Khách Hàng Một",
        "receiver_phone": "0912345678",
        "shipping_address_text": "123 Đường Số 1, Quận 1, TP HCM",
        "payment_method": "vietqr",
    }
    res_checkout = client.post(
        "/api/v1/checkout",
        json=checkout_payload,
        headers={**customer_headers, "Idempotency-Key": "idemp-vqr-checkout-1"},
    )
    assert res_checkout.status_code == 200, res_checkout.text
    order_number = res_checkout.json()["order_number"]

    order = test_db.execute(select(Order).where(Order.order_number == order_number)).scalar_one()
    assert order.status == "paid"
    assert order.paid_at is not None

    # 2. Dispatch with staff_id -> status='shipping', shipment created with cod_amount_vnd=0
    res_disp = client.post(
        f"/api/v1/admin/orders/{order_number}/dispatch",
        json={"delivery_staff_id": 1},
        headers={**admin_headers, "Idempotency-Key": "idemp-vqr-disp-1"},
    )
    assert res_disp.status_code == 200, res_disp.text

    shipment = test_db.execute(select(Shipment).where(Shipment.order_id == order.order_id)).scalar_one()
    assert shipment.cod_amount_vnd == 0
    assert shipment.status == "in_transit"

    # 3. Deliver -> status='delivered'
    res_deliv = client.post(
        f"/api/v1/admin/orders/{order_number}/deliver",
        headers={**admin_headers, "Idempotency-Key": "idemp-vqr-deliv-1"},
    )
    assert res_deliv.status_code == 200, res_deliv.text

    test_db.refresh(order)
    assert order.status == "delivered"

    # 4. Complete -> status='completed'
    res_comp = client.post(
        f"/api/v1/admin/orders/{order_number}/complete",
        headers={**admin_headers, "Idempotency-Key": "idemp-vqr-comp-1"},
    )
    assert res_comp.status_code == 200, res_comp.text

    test_db.refresh(order)
    assert order.status == "completed"


def test_invalid_transitions_rejected(
    client: TestClient, admin_headers: dict[str, str], customer_headers: dict[str, str], test_db
):
    create_active_cart(test_db, customer_id=1, variant_id=1, quantity=1)

    checkout_payload = {
        "receiver_name": "Khách Hàng Một",
        "receiver_phone": "0912345678",
        "shipping_address_text": "123 Đường Số 1, Quận 1, TP HCM",
        "payment_method": "cod",
    }
    res = client.post("/api/v1/checkout", json=checkout_payload, headers=customer_headers)
    order_number = res.json()["order_number"]

    # 1. Attempt deliver before dispatch (order is in 'confirmed') -> 409
    res_early_deliver = client.post(
        f"/api/v1/admin/orders/{order_number}/deliver",
        headers={**admin_headers, "Idempotency-Key": "idemp-inv-1"},
    )
    assert res_early_deliver.status_code == 409

    # 2. Attempt failed-delivery before dispatch -> 409
    res_early_fail = client.post(
        f"/api/v1/admin/orders/{order_number}/failed-delivery",
        json={"reason": "Hàng chưa giao"},
        headers={**admin_headers, "Idempotency-Key": "idemp-inv-2"},
    )
    assert res_early_fail.status_code == 409

    # 3. Attempt complete before deliver -> 409
    res_early_comp = client.post(
        f"/api/v1/admin/orders/{order_number}/complete",
        headers={**admin_headers, "Idempotency-Key": "idemp-inv-3"},
    )
    assert res_early_comp.status_code == 409

    # 4. Attempt dispatch with non-existent staff -> 400
    res_nonexistent_staff = client.post(
        f"/api/v1/admin/orders/{order_number}/dispatch",
        json={"delivery_staff_id": 999},
        headers={**admin_headers, "Idempotency-Key": "idemp-inv-4"},
    )
    assert res_nonexistent_staff.status_code in (400, 404)

    # 5. Attempt dispatch with inactive staff -> 400
    res_inactive_staff = client.post(
        f"/api/v1/admin/orders/{order_number}/dispatch",
        json={"delivery_staff_id": 2},
        headers={**admin_headers, "Idempotency-Key": "idemp-inv-5"},
    )
    assert res_inactive_staff.status_code in (400, 404)

    # 6. Dispatch successfully
    res_disp = client.post(
        f"/api/v1/admin/orders/{order_number}/dispatch",
        json={"delivery_staff_id": 1},
        headers={**admin_headers, "Idempotency-Key": "idemp-disp-ok"},
    )
    assert res_disp.status_code == 200

    # 7. Attempt dispatch again when already shipping -> 409
    res_disp_again = client.post(
        f"/api/v1/admin/orders/{order_number}/dispatch",
        json={"delivery_staff_id": 1},
        headers={**admin_headers, "Idempotency-Key": "idemp-disp-dup"},
    )
    assert res_disp_again.status_code == 409

    # 8. Attempt failed-delivery with empty reason -> 422
    res_empty_reason = client.post(
        f"/api/v1/admin/orders/{order_number}/failed-delivery",
        json={"reason": ""},
        headers={**admin_headers, "Idempotency-Key": "idemp-fail-empty"},
    )
    assert res_empty_reason.status_code == 422

    # 9. Non-existent order number -> 404
    res_not_found = client.post(
        "/api/v1/admin/orders/NONEXISTENT-ORDER/dispatch",
        json={"delivery_staff_id": 1},
        headers={**admin_headers, "Idempotency-Key": "idemp-404"},
    )
    assert res_not_found.status_code == 404


def test_admin_orders_filter_statuses(client: TestClient, admin_headers: dict[str, str]):
    for status in ["shipping", "delivered", "failed_delivery", "completed", "cancelled", "confirmed", "paid"]:
        res = client.get(f"/api/v1/admin/orders?status={status}", headers=admin_headers)
        assert res.status_code == 200, f"Failed for status={status}: {res.text}"

    # Invalid status should return 422
    res_inv = client.get("/api/v1/admin/orders?status=not_a_valid_status", headers=admin_headers)
    assert res_inv.status_code == 422
