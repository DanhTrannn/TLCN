from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.sql.elements import TextClause

from app.core.ids import uuid7
from app.db.deps import get_db
from app.main import app
from app.models.logistics import DeliveryStaff, Shipment
from app.models.order import Order


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
def setup_logistics_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    DeliveryStaff.__table__.create(engine)
    Order.__table__.create(engine)
    Shipment.__table__.create(engine)
    testing_session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def _get_test_db():
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _get_test_db
    yield testing_session
    app.dependency_overrides.pop(get_db, None)
    Shipment.__table__.drop(engine)
    Order.__table__.drop(engine)
    DeliveryStaff.__table__.drop(engine)


@pytest.fixture()
def db_session(setup_logistics_db):
    session = setup_logistics_db()
    try:
        yield session
    finally:
        session.close()


def test_admin_delivery_staff_crud(client: TestClient, admin_token_headers: dict[str, str]):
    # 1. Create delivery staff
    payload = {
        "full_name": "Nguyễn Văn Shipper",
        "phone": "0987654321",
        "vehicle_plate": "59-X1 12345",
    }
    create_res = client.post("/api/v1/admin/delivery-staff", json=payload, headers=admin_token_headers)
    assert create_res.status_code == 201
    staff_data = create_res.json()
    assert staff_data["full_name"] == "Nguyễn Văn Shipper"
    assert staff_data["is_active"] is True
    staff_id = staff_data["staff_id"]

    # 2. List delivery staff
    list_res = client.get("/api/v1/admin/delivery-staff", headers=admin_token_headers)
    assert list_res.status_code == 200
    staff_list = list_res.json()
    assert any(s["staff_id"] == staff_id for s in staff_list)

    # 3. Patch delivery staff
    patch_res = client.patch(
        f"/api/v1/admin/delivery-staff/{staff_id}",
        json={"is_active": False},
        headers=admin_token_headers,
    )
    assert patch_res.status_code == 204

    # Verify updated
    get_res = client.get("/api/v1/admin/delivery-staff", headers=admin_token_headers)
    target = next(s for s in get_res.json() if s["staff_id"] == staff_id)
    assert target["is_active"] is False


def test_patch_delivery_staff_not_found(client: TestClient, admin_token_headers: dict[str, str]):
    patch_res = client.patch(
        "/api/v1/admin/delivery-staff/99999",
        json={"is_active": False},
        headers=admin_token_headers,
    )
    assert patch_res.status_code == 404


def test_admin_shipments_list_and_filter(
    client: TestClient, admin_token_headers: dict[str, str], db_session
):
    staff = DeliveryStaff(
        public_id=uuid7(),
        full_name="Trần Văn Giao",
        phone="0912345678",
        vehicle_plate="29-A1 99999",
        is_active=True,
    )
    db_session.add(staff)
    db_session.flush()

    order1 = Order(
        order_number="ORD-TEST-001",
        customer_id=1,
        checkout_idempotency_key="idemp-1",
        status="shipping",
        payment_method="cod",
        currency_code="VND",
        subtotal_vnd=250000,
        shipping_fee_vnd=30000,
        total_vnd=280000,
        receiver_name="Người Mua 1",
        receiver_phone="0901112222",
        shipping_address_text="123 Phố Huế, Hà Nội",
    )
    order2 = Order(
        order_number="ORD-TEST-002",
        customer_id=2,
        checkout_idempotency_key="idemp-2",
        status="delivered",
        payment_method="vietqr",
        currency_code="VND",
        subtotal_vnd=500000,
        shipping_fee_vnd=0,
        total_vnd=500000,
        receiver_name="Người Mua 2",
        receiver_phone="0903334444",
        shipping_address_text="456 Lê Lợi, TP.HCM",
    )
    db_session.add_all([order1, order2])
    db_session.flush()

    shipment1 = Shipment(
        public_id=uuid7(),
        shipment_code="SHIP-TEST-001",
        order_id=order1.order_id,
        delivery_staff_id=staff.staff_id,
        status="in_transit",
        attempt_count=1,
        cod_amount_vnd=280000,
        cod_collected_vnd=0,
    )
    shipment2 = Shipment(
        public_id=uuid7(),
        shipment_code="SHIP-TEST-002",
        order_id=order2.order_id,
        delivery_staff_id=staff.staff_id,
        status="delivered",
        attempt_count=1,
        cod_amount_vnd=0,
        cod_collected_vnd=0,
    )
    db_session.add_all([shipment1, shipment2])
    db_session.commit()

    # List all
    res_all = client.get("/api/v1/admin/shipments", headers=admin_token_headers)
    assert res_all.status_code == 200
    shipments = res_all.json()
    assert len(shipments) == 2
    codes = [s["shipment_code"] for s in shipments]
    assert "SHIP-TEST-001" in codes
    assert "SHIP-TEST-002" in codes

    # Filter by status
    res_filtered = client.get("/api/v1/admin/shipments?status=in_transit", headers=admin_token_headers)
    assert res_filtered.status_code == 200
    filtered_list = res_filtered.json()
    assert len(filtered_list) == 1
    assert filtered_list[0]["shipment_code"] == "SHIP-TEST-001"
    assert filtered_list[0]["order_number"] == "ORD-TEST-001"
    assert filtered_list[0]["delivery_staff_name"] == "Trần Văn Giao"


def test_admin_shipment_by_order_number(
    client: TestClient, admin_token_headers: dict[str, str], db_session
):
    staff = DeliveryStaff(
        public_id=uuid7(),
        full_name="Lê Giao Hàng",
        phone="0933333333",
        vehicle_plate="43-C1 11111",
        is_active=True,
    )
    db_session.add(staff)
    db_session.flush()

    order = Order(
        order_number="ORD-DETAIL-001",
        customer_id=1,
        checkout_idempotency_key="idemp-detail-1",
        status="shipping",
        payment_method="cod",
        currency_code="VND",
        subtotal_vnd=300000,
        shipping_fee_vnd=20000,
        total_vnd=320000,
        receiver_name="Khách Hàng Chi Tiết",
        receiver_phone="0911223344",
        shipping_address_text="789 Nguyễn Huệ, Đà Nẵng",
    )
    db_session.add(order)
    db_session.flush()

    shipment = Shipment(
        public_id=uuid7(),
        shipment_code="SHIP-DETAIL-001",
        order_id=order.order_id,
        delivery_staff_id=staff.staff_id,
        status="assigned",
        attempt_count=1,
        cod_amount_vnd=320000,
        cod_collected_vnd=0,
        notes="Giao trước 17h",
    )
    db_session.add(shipment)
    db_session.commit()

    res = client.get(f"/api/v1/admin/shipments/{order.order_number}", headers=admin_token_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["shipment_code"] == "SHIP-DETAIL-001"
    assert data["order_number"] == "ORD-DETAIL-001"
    assert data["delivery_staff_name"] == "Lê Giao Hàng"
    assert data["cod_amount_vnd"] == 320000
    assert data["notes"] == "Giao trước 17h"

    # Not found case
    res_404 = client.get("/api/v1/admin/shipments/NONEXISTENT-ORDER", headers=admin_token_headers)
    assert res_404.status_code == 404
