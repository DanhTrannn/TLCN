"""Integration tests for Admin Inbound Receipts & Moving Weighted Average Costing (Gói 3 - Task 3)."""

import uuid
from datetime import UTC, datetime
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
from app.models.inbound import InboundReceipt, InboundReceiptItem
from app.models.inventory import Inventory
from app.models.inventory_tx import InventoryTransaction


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

    admin = Customer(
        customer_id=1,
        public_id=uuid7(),
        role="admin",
        display_name="Quản Trị Viên",
        status="active",
    )
    db.add(admin)

    cat = Category(category_id=1, public_id=uuid7(), code="AO-NAM", name="Áo Nam", is_active=True)
    prod = Product(
        product_id=1,
        public_id=uuid7(),
        category_id=1,
        slug="ao-polo",
        name="Áo Polo Nam",
        is_active=True,
    )
    # Variant 1: Existing stock = 10, current cost = 100,000 VND
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
    # Variant 2: Zero stock, current cost = 0 VND
    var2 = ProductVariant(
        variant_id=2,
        public_id=uuid7(),
        product_id=1,
        sku="APN-002",
        size_code="M",
        color_code="TRANG",
        price_vnd=150000,
        cost_price_vnd=0,
        is_active=True,
    )
    db.add_all([cat, prod, var1, var2])
    db.add_all([
        Inventory(variant_id=1, opening_on_hand=10, on_hand=10, version=1),
        Inventory(variant_id=2, opening_on_hand=0, on_hand=0, version=1),
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


@pytest.fixture()
def admin_client(setup_db):
    mock_admin = Customer(
        customer_id=1,
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


def test_create_inbound_receipt_success(admin_client, test_db):
    """Test scenario 1 & 2:
    - Successful creation of inbound receipt.
    - Increases on_hand and opening_on_hand.
    - Creates InventoryTransaction with movement_type='inbound'.
    - Cost price updates using Moving Weighted Average formula:
      round((10 * 100,000 + 20 * 130,000) / (10 + 20)) = 120,000 VND.
    """
    payload = {
        "batch_name": "Lô hàng Polo Đợt 1",
        "notes": "Nhập hàng từ xưởng may",
        "items": [
            {
                "variant_id": 1,
                "quantity": 20,
                "unit_cost_vnd": 130000,
            }
        ],
    }
    headers = {"Idempotency-Key": "idemp-test-001"}
    response = admin_client.post("/api/v1/admin/inbound/receipts", json=payload, headers=headers)
    assert response.status_code == 201, response.text
    data = response.json()

    assert data["batch_name"] == "Lô hàng Polo Đợt 1"
    assert data["status"] == "completed"
    assert data["total_items_count"] == 20
    assert data["total_cost_vnd"] == 2600000
    assert data["created_by_name"] == "Quản Trị Viên"
    assert data["receipt_code"].startswith("INB-")
    assert len(data["items"]) == 1

    item = data["items"][0]
    assert item["variant_id"] == 1
    assert item["sku"] == "APN-001"
    assert item["product_name"] == "Áo Polo Nam"
    assert item["quantity"] == 20
    assert item["unit_cost_vnd"] == 130000
    assert item["total_cost_vnd"] == 2600000
    assert item["previous_cost_price_vnd"] == 100000
    assert item["new_cost_price_vnd"] == 120000

    # Verify DB state
    inv = test_db.scalar(select(Inventory).where(Inventory.variant_id == 1))
    assert inv.on_hand == 30
    assert inv.opening_on_hand == 30
    assert inv.version == 2

    variant = test_db.scalar(select(ProductVariant).where(ProductVariant.variant_id == 1))
    assert variant.cost_price_vnd == 120000

    tx = test_db.scalar(select(InventoryTransaction).where(InventoryTransaction.variant_id == 1))
    assert tx is not None
    assert tx.location_type == "central_warehouse"
    assert tx.movement_type == "inbound"
    assert tx.quantity_delta == 20
    assert tx.reference_code == data["receipt_code"]
    assert "Lô hàng Polo Đợt 1" in tx.notes


def test_inbound_costing_zero_existing_inventory(admin_client, test_db):
    """Test scenario 3:
    - Edge case: Q_current == 0.
    - New cost price = Inbound unit cost.
    """
    payload = {
        "batch_name": "Lô hàng Polo Trắng",
        "notes": "Nhập lần đầu",
        "items": [
            {
                "variant_id": 2,
                "quantity": 15,
                "unit_cost_vnd": 85000,
            }
        ],
    }
    headers = {"Idempotency-Key": "idemp-test-002"}
    response = admin_client.post("/api/v1/admin/inbound/receipts", json=payload, headers=headers)
    assert response.status_code == 201, response.text
    data = response.json()

    item = data["items"][0]
    assert item["previous_cost_price_vnd"] == 0
    assert item["new_cost_price_vnd"] == 85000

    # Verify DB
    inv = test_db.scalar(select(Inventory).where(Inventory.variant_id == 2))
    assert inv.on_hand == 15
    assert inv.opening_on_hand == 15

    variant = test_db.scalar(select(ProductVariant).where(ProductVariant.variant_id == 2))
    assert variant.cost_price_vnd == 85000


def test_create_inbound_receipt_validations(admin_client):
    """Test scenario 4:
    - Reject duplicate variant_id in items (422).
    - Reject quantity <= 0 (422).
    - Reject unit_cost_vnd < 0 (422).
    - Reject non-existent variant_id (404).
    - Reject missing or empty Idempotency-Key (400).
    """
    headers = {"Idempotency-Key": "idemp-val-001"}

    # 1. Duplicate variant_id in items
    res_dup = admin_client.post(
        "/api/v1/admin/inbound/receipts",
        json={
            "batch_name": "Lô trùng lặp",
            "items": [
                {"variant_id": 1, "quantity": 5, "unit_cost_vnd": 50000},
                {"variant_id": 1, "quantity": 10, "unit_cost_vnd": 60000},
            ],
        },
        headers=headers,
    )
    assert res_dup.status_code == 422

    # 2. Quantity <= 0
    res_qty = admin_client.post(
        "/api/v1/admin/inbound/receipts",
        json={
            "batch_name": "Lô số lượng 0",
            "items": [{"variant_id": 1, "quantity": 0, "unit_cost_vnd": 50000}],
        },
        headers=headers,
    )
    assert res_qty.status_code == 422

    # 3. Unit cost < 0
    res_cost = admin_client.post(
        "/api/v1/admin/inbound/receipts",
        json={
            "batch_name": "Lô giá âm",
            "items": [{"variant_id": 1, "quantity": 5, "unit_cost_vnd": -1000}],
        },
        headers=headers,
    )
    assert res_cost.status_code == 422

    # 4. Non-existent variant_id -> 404
    res_not_found = admin_client.post(
        "/api/v1/admin/inbound/receipts",
        json={
            "batch_name": "Lô variant không tồn tại",
            "items": [{"variant_id": 999999, "quantity": 5, "unit_cost_vnd": 50000}],
        },
        headers=headers,
    )
    assert res_not_found.status_code == 404

    # 5. Missing Idempotency-Key
    res_no_key = admin_client.post(
        "/api/v1/admin/inbound/receipts",
        json={
            "batch_name": "Lô thiếu idempotency",
            "items": [{"variant_id": 1, "quantity": 5, "unit_cost_vnd": 50000}],
        },
    )
    assert res_no_key.status_code == 400


def test_inbound_receipt_idempotency(admin_client, test_db):
    """Test scenario:
    - Submitting identical payload with same Idempotency-Key returns existing receipt.
    - Does NOT double-increment inventory or re-apply costing.
    """
    payload = {
        "batch_name": "Lô kiểm tra Idempotency",
        "items": [{"variant_id": 1, "quantity": 10, "unit_cost_vnd": 120000}],
    }
    headers = {"Idempotency-Key": "idemp-repeat-test"}

    # First request
    res1 = admin_client.post("/api/v1/admin/inbound/receipts", json=payload, headers=headers)
    assert res1.status_code == 201
    receipt_code_1 = res1.json()["receipt_code"]

    inv_after_1 = test_db.scalar(select(Inventory).where(Inventory.variant_id == 1))
    assert inv_after_1.on_hand == 20  # initial 10 + 10

    # Second request with same idempotency key
    res2 = admin_client.post("/api/v1/admin/inbound/receipts", json=payload, headers=headers)
    assert res2.status_code in (200, 201)
    assert res2.json()["receipt_code"] == receipt_code_1

    # Inventory must remain 20 (not 30)
    test_db.expire_all()
    inv_after_2 = test_db.scalar(select(Inventory).where(Inventory.variant_id == 1))
    assert inv_after_2.on_hand == 20

    # Only 1 inbound receipt in DB
    receipts_count = len(test_db.scalars(select(InboundReceipt)).all())
    assert receipts_count == 1


def test_list_and_detail_endpoints(admin_client):
    """Test scenario 5:
    - List and detail retrieval endpoints work as expected.
    """
    # Create 2 receipts
    for idx in (1, 2):
        admin_client.post(
            "/api/v1/admin/inbound/receipts",
            json={
                "batch_name": f"Lô thử nghiệm {idx}",
                "items": [{"variant_id": 1, "quantity": idx * 5, "unit_cost_vnd": 100000}],
            },
            headers={"Idempotency-Key": f"idemp-list-detail-{idx}"},
        )

    # 1. List receipts
    res_list = admin_client.get("/api/v1/admin/inbound/receipts")
    assert res_list.status_code == 200
    list_data = res_list.json()
    assert list_data["total"] >= 2
    assert len(list_data["items"]) >= 2
    first_code = list_data["items"][0]["receipt_code"]

    # Search filter
    res_search = admin_client.get("/api/v1/admin/inbound/receipts?search=Lô thử nghiệm 1")
    assert res_search.status_code == 200
    search_data = res_search.json()
    assert search_data["total"] == 1
    assert search_data["items"][0]["batch_name"] == "Lô thử nghiệm 1"

    # 2. Detail receipt
    res_detail = admin_client.get(f"/api/v1/admin/inbound/receipts/{first_code}")
    assert res_detail.status_code == 200
    detail_data = res_detail.json()
    assert detail_data["receipt_code"] == first_code
    assert len(detail_data["items"]) >= 1

    # Detail not found
    res_not_found = admin_client.get("/api/v1/admin/inbound/receipts/INB-NON-EXISTENT")
    assert res_not_found.status_code == 404


def test_admin_products_includes_cost_price(admin_client):
    """Verify AdminVariantResponse includes cost_price_vnd and variant_id."""
    res = admin_client.get("/api/v1/admin/products")
    assert res.status_code == 200
    products = res.json()
    assert len(products) > 0
    variant = products[0]["variants"][0]
    assert "cost_price_vnd" in variant
    assert variant["cost_price_vnd"] == 100000
    assert "variant_id" in variant
    assert variant["variant_id"] == 1


def test_long_batch_name_truncation(admin_client, test_db):
    """Verify that batch_name up to 255 chars does not cause DB DataError on InventoryTransaction.notes."""
    long_name = (
        "Lô hàng vải cotton chất lượng cao đặc biệt từ xưởng sản xuất số 1 "
        "khu công nghiệp Tân Bình thành phố Hồ Chí Minh đợt kiểm tra chất lượng "
        "lần cuối trước khi nhập kho trung tâm " + "X" * 150
    )[:255]
    payload = {
        "batch_name": long_name,
        "items": [{"variant_id": 1, "quantity": 5, "unit_cost_vnd": 100000}],
    }
    headers = {"Idempotency-Key": "idemp-long-batch-name"}
    res = admin_client.post("/api/v1/admin/inbound/receipts", json=payload, headers=headers)
    assert res.status_code == 201
    tx = test_db.scalar(
        select(InventoryTransaction).where(InventoryTransaction.reference_code == res.json()["receipt_code"])
    )
    assert tx is not None
    assert len(tx.notes) <= 255


def test_midnight_boundary_idempotency(admin_client, test_db):
    """Verify that retrying with the same Idempotency-Key across midnight returns existing receipt."""
    import hashlib

    key = "idemp-midnight-key"
    digest = hashlib.sha256(key.encode()).hexdigest()[:6].upper()
    past_date_code = f"INB-20260901-{digest}"

    now = datetime.now(UTC).replace(tzinfo=None)
    past_receipt = InboundReceipt(
        public_id=uuid.uuid4(),
        receipt_code=past_date_code,
        batch_name="Lô hôm qua",
        status="completed",
        total_items_count=10,
        total_cost_vnd=1000000,
        created_by_customer_id=1,
        created_at=now,
        updated_at=now,
    )
    test_db.add(past_receipt)
    test_db.commit()

    payload = {
        "batch_name": "Lô thử nghiệm retry hôm nay",
        "items": [{"variant_id": 1, "quantity": 10, "unit_cost_vnd": 100000}],
    }
    headers = {"Idempotency-Key": key}
    res = admin_client.post("/api/v1/admin/inbound/receipts", json=payload, headers=headers)
    assert res.status_code in (200, 201)
    assert res.json()["receipt_code"] == past_date_code


def test_inventory_manager_can_access_inbound_and_products(setup_db):
    """Verify inventory_manager role can create receipts, view list, and access products list."""
    session = setup_db()
    inv_user = Customer(
        customer_id=99,
        public_id=uuid7(),
        role="inventory_manager",
        display_name="Trưởng Kho",
        status="active",
    )
    session.add(inv_user)
    session.commit()
    session.close()

    fastapi_app.dependency_overrides[get_current_customer] = lambda: inv_user
    fastapi_app.dependency_overrides[verify_csrf] = lambda: None

    with TestClient(fastapi_app, raise_server_exceptions=False) as client:
        # Can read products
        res_prod = client.get("/api/v1/admin/products")
        assert res_prod.status_code == 200

        # Can create inbound receipt
        payload = {
            "batch_name": "Lô hàng của Trưởng Kho",
            "items": [{"variant_id": 1, "quantity": 4, "unit_cost_vnd": 120000}],
        }
        res_create = client.post(
            "/api/v1/admin/inbound/receipts",
            json=payload,
            headers={"Idempotency-Key": "idemp-inv-mgr-1"},
        )
        assert res_create.status_code == 201
        receipt_code = res_create.json()["receipt_code"]

        # Can list inbound receipts
        res_list = client.get("/api/v1/admin/inbound/receipts")
        assert res_list.status_code == 200
        assert res_list.json()["total"] >= 1

        # Can view inbound receipt detail
        res_detail = client.get(f"/api/v1/admin/inbound/receipts/{receipt_code}")
        assert res_detail.status_code == 200
        assert res_detail.json()["created_by_name"] == "Trưởng Kho"

    fastapi_app.dependency_overrides.pop(get_current_customer, None)
    fastapi_app.dependency_overrides.pop(verify_csrf, None)


def test_unauthorized_role_cannot_access_inbound(setup_db):
    """Verify other roles (e.g. marketing_manager, customer) get 403 Forbidden on inbound receipts."""
    session = setup_db()
    marketing_user = Customer(
        customer_id=100,
        public_id=uuid7(),
        role="marketing_manager",
        display_name="Trưởng Marketing",
        status="active",
    )
    session.add(marketing_user)
    session.commit()
    session.close()

    fastapi_app.dependency_overrides[get_current_customer] = lambda: marketing_user
    fastapi_app.dependency_overrides[verify_csrf] = lambda: None

    with TestClient(fastapi_app, raise_server_exceptions=False) as client:
        res_list = client.get("/api/v1/admin/inbound/receipts")
        assert res_list.status_code == 403

        payload = {
            "batch_name": "Lô không hợp lệ",
            "items": [{"variant_id": 1, "quantity": 1, "unit_cost_vnd": 100000}],
        }
        res_create = client.post(
            "/api/v1/admin/inbound/receipts",
            json=payload,
            headers={"Idempotency-Key": "idemp-unauth-1"},
        )
        assert res_create.status_code == 403

    fastapi_app.dependency_overrides.pop(get_current_customer, None)
    fastapi_app.dependency_overrides.pop(verify_csrf, None)


