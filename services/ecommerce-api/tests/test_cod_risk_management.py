import app.db.deps
import app.db.uow
import pytest
from app.core.ids import uuid7
from app.db.base import Base
from app.db.deps import get_current_admin, get_current_customer, get_db, verify_csrf
from app.main import app as fastapi_app
from app.models.customer import Customer, CustomerCredential
from app.models.inventory import Inventory
from app.models.logistics import DeliveryStaff, Shipment, ShipmentAttempt
from app.models.order import Order
from app.modules.orders.service import fail_delivery_order
from sqlalchemy import create_engine, event, select
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.sql.elements import TextClause


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
def cod_db(monkeypatch):
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def connect(dbapi_connection, connection_record):
        dbapi_connection.create_function("char_length", 1, lambda s: len(s) if s is not None else 0)

    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    monkeypatch.setattr(app.db.uow, "SessionLocal", session_factory)
    monkeypatch.setattr(app.db.deps, "SessionLocal", session_factory)

    def _get_test_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    fastapi_app.dependency_overrides[get_db] = _get_test_db

    db = session_factory()
    # Seed admin & customer
    admin = Customer(customer_id=1, public_id=uuid7(), role="admin", display_name="Admin User", status="active")
    cust = Customer(customer_id=2, public_id=uuid7(), role="customer", display_name="COD Customer", status="active", is_cod_blocked=True, boom_count=3)
    cred = CustomerCredential(customer_id=2, email_normalized="cod_cust@test.local", password_hash="hash", is_enabled=True)
    db.add_all([admin, cust, cred])

    # Seed staff & inventory
    staff = DeliveryStaff(staff_id=1, public_id=uuid7(), full_name="Shipper A", phone="0901112222", is_active=True)
    inv = Inventory(variant_id=1, on_hand=50, opening_on_hand=50, version=1)
    db.add_all([staff, inv])

    db.commit()
    yield db
    db.close()
    fastapi_app.dependency_overrides.clear()


def test_delivery_failure_non_buyer_fault_does_not_increment_boom_count(cod_db):
    # Customer starts with boom_count = 0
    cust = cod_db.scalar(select(Customer).where(Customer.customer_id == 2))
    cust.boom_count = 0
    cust.is_cod_blocked = False
    cod_db.commit()

    order = Order(
        order_id=10,
        order_number="ORD-FAIL-LOGISTICS",
        customer_id=2,
        checkout_idempotency_key="chk:fail:logistics",
        status="shipping",
        payment_method="cod",
        currency_code="VND",
        subtotal_vnd=200000,
        shipping_fee_vnd=30000,
        total_vnd=230000,
        receiver_name="COD Customer",
        receiver_phone="0901234567",
        shipping_address_text="123 Tran Hung Dao",
        channel="online",
    )
    cod_db.add(order)
    cod_db.flush()

    shipment = Shipment(
        shipment_id=10,
        public_id=uuid7(),
        shipment_code="SHP-FAIL-01",
        order_id=10,
        delivery_staff_id=1,
        status="assigned",
        attempt_count=1,
        cod_amount_vnd=230000,
        cod_collected_vnd=0,
    )
    cod_db.add(shipment)
    cod_db.flush()

    # Fail attempt 1 with damaged_in_transit (Logistics fault)
    res1 = fail_delivery_order(cod_db, "ORD-FAIL-LOGISTICS", reason="damaged_in_transit", idempotency_key="k1")
    assert res1.delivery_attempt_count == 1
    assert res1.remaining_delivery_attempts == 2

    attempt1 = cod_db.scalar(select(ShipmentAttempt).where(ShipmentAttempt.shipment_id == 10, ShipmentAttempt.attempt_number == 1))
    assert attempt1.is_buyer_fault is False
    assert attempt1.failure_reason == "damaged_in_transit"

    # Fail attempt 2 with wrong_item_shipped (Logistics fault)
    res2 = fail_delivery_order(cod_db, "ORD-FAIL-LOGISTICS", reason="wrong_item_shipped", idempotency_key="k2")
    assert res2.delivery_attempt_count == 2
    assert res2.remaining_delivery_attempts == 1

    attempt2 = cod_db.scalar(select(ShipmentAttempt).where(ShipmentAttempt.shipment_id == 10, ShipmentAttempt.attempt_number == 2))
    assert attempt2.is_buyer_fault is False

    # Fail attempt 3 with logistics_delayed (Logistics fault)
    res3 = fail_delivery_order(cod_db, "ORD-FAIL-LOGISTICS", reason="logistics_delayed", idempotency_key="k3")
    assert res3.delivery_attempt_count == 3
    assert res3.remaining_delivery_attempts == 0

    attempt3 = cod_db.scalar(select(ShipmentAttempt).where(ShipmentAttempt.shipment_id == 10, ShipmentAttempt.attempt_number == 3))
    assert attempt3.is_buyer_fault is False

    # Boom count should NOT be incremented because it was logistics fault!
    cod_db.refresh(cust)
    assert cust.boom_count == 0
    assert cust.is_cod_blocked is False


def test_admin_reinstate_cod_endpoint(client, cod_db):
    admin = cod_db.scalar(select(Customer).where(Customer.customer_id == 1))
    fastapi_app.dependency_overrides[get_current_admin] = lambda: admin
    fastapi_app.dependency_overrides[get_current_customer] = lambda: admin
    fastapi_app.dependency_overrides[verify_csrf] = lambda: None

    cust = cod_db.scalar(select(Customer).where(Customer.customer_id == 2))
    assert cust.is_cod_blocked is True
    assert cust.boom_count == 3

    # Admin calls reinstate COD
    res = client.post(
        f"/api/v1/admin/customers/{cust.customer_id}/reinstate-cod",
        json={"reason": "Khách hàng xác nhận thông tin địa chỉ mới chính xác", "probation_failed_count": 2},
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["is_cod_blocked"] is False
    assert data["boom_count"] == 2
    assert data["cod_reinstatement_reason"] == "Khách hàng xác nhận thông tin địa chỉ mới chính xác"
    assert data["cod_reinstated_by"] == 1

    # Verify DB state
    cod_db.refresh(cust)
    assert cust.is_cod_blocked is False
    assert cust.boom_count == 2
    assert cust.cod_reinstated_by == 1
    assert cust.cod_reinstated_at is not None
