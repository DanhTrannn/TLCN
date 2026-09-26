"""Integration tests for Backend Analytics Module with RBAC & Role Metrics (Gói 4 - Task 2)."""

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
from app.db.deps import get_current_admin, get_current_customer, get_current_staff, get_db, verify_csrf
import app.db.deps
import app.db.uow
from app.main import app as fastapi_app
import app.models  # noqa: F401
from app.models.catalog import Category, Product, ProductVariant
from app.models.customer import Customer
from app.models.multicity import City, Store, StoreInventory
from app.models.inventory import Inventory
from app.models.order import Order, OrderItem, Payment, Refund
from app.models.inbound import InboundReceipt, InboundReceiptItem
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
def setup_analytics_db(monkeypatch):
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

    # Cities & Stores
    city = City(city_id=1, code="HCM", name="TP. Hồ Chí Minh", is_active=True)
    store1 = Store(
        store_id=1,
        city_id=1,
        code="STR-HCM-001",
        name="Cửa hàng Quận 1",
        address="123 Lê Lợi, Q1",
        phone="02811112222",
        is_active=True,
    )
    store2 = Store(
        store_id=2,
        city_id=1,
        code="STR-HCM-002",
        name="Cửa hàng Quận 3",
        address="456 CMT8, Q3",
        phone="02833334444",
        is_active=True,
    )
    db.add_all([city, store1, store2])
    db.commit()

    # Users for each role
    admin_user = Customer(customer_id=10, public_id=uuid7(), role="admin", display_name="Admin Boss", status="active")
    store_user_1 = Customer(
        customer_id=20,
        public_id=uuid7(),
        role="store_manager",
        display_name="Store 1 Mgr",
        store_id=1,
        status="active",
    )
    store_user_2 = Customer(
        customer_id=21,
        public_id=uuid7(),
        role="store_manager",
        display_name="Store 2 Mgr",
        store_id=2,
        status="active",
    )
    sales_user = Customer(
        customer_id=30, public_id=uuid7(), role="sales_manager", display_name="Sales Head", status="active"
    )
    marketing_user = Customer(
        customer_id=40, public_id=uuid7(), role="marketing_manager", display_name="MKT Head", status="active"
    )
    inventory_user = Customer(
        customer_id=50, public_id=uuid7(), role="inventory_manager", display_name="WH Head", status="active"
    )
    operations_user = Customer(
        customer_id=60, public_id=uuid7(), role="operations_manager", display_name="Ops Head", status="active"
    )
    system_user = Customer(
        customer_id=70, public_id=uuid7(), role="system_admin", display_name="Sys Admin", status="active"
    )
    normal_customer = Customer(
        customer_id=80, public_id=uuid7(), role="customer", display_name="Buyer Joe", status="active"
    )

    db.add_all([
        admin_user,
        store_user_1,
        store_user_2,
        sales_user,
        marketing_user,
        inventory_user,
        operations_user,
        system_user,
        normal_customer,
    ])
    db.commit()

    # Catalog & Inventory
    cat = Category(category_id=1, public_id=uuid7(), code="AO-NAM", name="Áo Nam", is_active=True)
    prod = Product(
        product_id=1,
        public_id=uuid7(),
        category_id=1,
        slug="ao-polo",
        name="Áo Polo Nam",
        is_active=True,
    )
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
    inv1 = Inventory(variant_id=1, on_hand=50, opening_on_hand=50)
    store_inv1 = StoreInventory(store_inventory_id=1, store_id=1, variant_id=1, on_hand=10, opening_on_hand=10)
    store_inv2 = StoreInventory(store_inventory_id=2, store_id=2, variant_id=1, on_hand=4, opening_on_hand=5)

    db.add_all([cat, prod, var1, inv1, store_inv1, store_inv2])
    db.commit()

    # Orders, Payments, Inbound
    ord1 = Order(
        order_number="ORD-AN-001",
        customer_id=80,
        checkout_idempotency_key=f"chk-{uuid.uuid4().hex[:30]}",
        status="delivered",
        subtotal_vnd=300000,
        discount_amount_vnd=0,
        shipping_fee_vnd=0,
        total_vnd=300000,
        store_id=1,
        receiver_name="Người Nhận 1",
        receiver_phone="0901234567",
        shipping_address_text="123 Lê Lợi",
        created_at=now - timedelta(days=2),
    )
    db.add(ord1)
    db.flush()

    item1 = OrderItem(
        public_id=uuid7(),
        order_id=ord1.order_id,
        variant_id=1,
        product_public_id_snapshot=uuid7(),
        category_code_snapshot="AO-NAM",
        category_name_snapshot="Áo Nam",
        product_name_snapshot="Áo Polo Nam",
        sku_snapshot="APN-001",
        size_code_snapshot="L",
        color_code_snapshot="DEN",
        unit_price_vnd=300000,
        cost_price_vnd=100000,
        quantity=1,
        line_total_vnd=300000,
    )
    pay1 = Payment(
        payment_reference="PAY-ORD-AN-001",
        payment_idempotency_key=f"pay-{uuid.uuid4().hex[:30]}",
        order_id=ord1.order_id,
        amount_vnd=300000,
        status="succeeded",
        attempted_at=now - timedelta(days=2),
    )
    # Order created today for store 1 to verify today's metrics
    ord_today = Order(
        order_number="ORD-AN-TODAY",
        customer_id=80,
        checkout_idempotency_key=f"chk-{uuid.uuid4().hex[:30]}",
        status="completed",
        subtotal_vnd=300000,
        discount_amount_vnd=0,
        shipping_fee_vnd=0,
        total_vnd=300000,
        store_id=1,
        receiver_name="Người Nhận Hôm Nay",
        receiver_phone="0901234567",
        shipping_address_text="123 Lê Lợi",
        created_at=now,
    )
    db.add(ord_today)
    db.flush()

    item_today = OrderItem(
        public_id=uuid7(),
        order_id=ord_today.order_id,
        variant_id=1,
        product_public_id_snapshot=uuid7(),
        category_code_snapshot="AO-NAM",
        category_name_snapshot="Áo Nam",
        product_name_snapshot="Áo Polo Nam",
        sku_snapshot="APN-001",
        size_code_snapshot="L",
        color_code_snapshot="DEN",
        unit_price_vnd=300000,
        cost_price_vnd=100000,
        quantity=1,
        line_total_vnd=300000,
    )
    db.add_all([item1, pay1, item_today])
    db.commit()

    yield testing_session

    fastapi_app.dependency_overrides.pop(get_db, None)
    fastapi_app.dependency_overrides.pop(get_current_customer, None)
    fastapi_app.dependency_overrides.pop(get_current_admin, None)
    fastapi_app.dependency_overrides.pop(get_current_staff, None)
    fastapi_app.dependency_overrides.pop(verify_csrf, None)
    Base.metadata.drop_all(engine)


def make_client_for_user(customer: Customer) -> TestClient:
    fastapi_app.dependency_overrides[get_current_customer] = lambda: customer
    fastapi_app.dependency_overrides[verify_csrf] = lambda: None
    return TestClient(fastapi_app, raise_server_exceptions=False)


def test_admin_can_access_all_roles(setup_analytics_db):
    db = setup_analytics_db()
    admin = db.execute(select(Customer).where(Customer.role == "admin")).scalar_one()
    client = make_client_for_user(admin)

    role_expectations = {
        "executive": ("executive", ["gmv_vnd", "net_revenue_vnd", "gross_margin_percent"]),
        "admin": ("executive", ["gmv_vnd", "net_revenue_vnd", "gross_margin_percent"]),
        "sales": ("sales", ["top_selling_products", "store_contributions", "category_shares"]),
        "sales_manager": ("sales", ["top_selling_products", "store_contributions", "category_shares"]),
        "marketing": ("marketing", ["funnel_steps", "conversion_rate_percent"]),
        "marketing_manager": ("marketing", ["funnel_steps", "conversion_rate_percent"]),
        "store": ("store", ["store_revenue_today_vnd", "low_stock_at_store_count"]),
        "store_manager": ("store", ["store_revenue_today_vnd", "low_stock_at_store_count"]),
        "inventory": ("inventory", ["warehouse_stock_units", "total_inventory_value_vnd"]),
        "inventory_manager": ("inventory", ["warehouse_stock_units", "total_inventory_value_vnd"]),
        "operations": ("operations", ["pending_fulfillment_count", "boom_orders_count"]),
        "operations_manager": ("operations", ["pending_fulfillment_count", "boom_orders_count"]),
        "system": ("system", ["reconciliation_variance", "pipeline_status"]),
        "system_admin": ("system", ["reconciliation_variance", "pipeline_status"]),
    }

    for target_role, (expected_role, expected_fields) in role_expectations.items():
        res = client.get(f"/api/v1/admin/analytics/role-metrics?target_role={target_role}")
        assert res.status_code == 200, f"Admin failed to access role {target_role}: {res.text}"
        data = res.json()
        assert data["role"] == expected_role, f"Expected role {expected_role} for {target_role}, got {data['role']}"
        for field in expected_fields:
            assert field in data, f"Field {field} missing from {target_role} response: {data}"


def test_admin_can_access_any_store(setup_analytics_db):
    db = setup_analytics_db()
    admin = db.execute(select(Customer).where(Customer.role == "admin")).scalar_one()
    client = make_client_for_user(admin)

    res1 = client.get("/api/v1/admin/analytics/role-metrics?target_role=store&store_id=1")
    assert res1.status_code == 200
    assert res1.json()["store_id"] == 1

    res2 = client.get("/api/v1/admin/analytics/role-metrics?target_role=store&store_id=2")
    assert res2.status_code == 200
    assert res2.json()["store_id"] == 2


def test_store_manager_access_executive_forbidden(setup_analytics_db):
    db = setup_analytics_db()
    store_mgr = db.execute(select(Customer).where(Customer.customer_id == 20)).scalar_one()
    client = make_client_for_user(store_mgr)

    res = client.get("/api/v1/admin/analytics/role-metrics?target_role=executive")
    assert res.status_code == 403
    assert "Bạn không có quyền truy cập" in res.text


def test_store_manager_access_own_store(setup_analytics_db):
    db = setup_analytics_db()
    store_mgr = db.execute(select(Customer).where(Customer.customer_id == 20)).scalar_one()
    client = make_client_for_user(store_mgr)

    # Explicit own store_id
    res = client.get("/api/v1/admin/analytics/role-metrics?target_role=store&store_id=1")
    assert res.status_code == 200
    data = res.json()
    assert data["store_id"] == 1
    assert data["store_revenue_today_vnd"] > 0
    assert data["store_orders_count"] > 0

    # Omitted store_id defaults to actor.store_id
    res_default = client.get("/api/v1/admin/analytics/role-metrics?target_role=store")
    assert res_default.status_code == 200
    data_default = res_default.json()
    assert data_default["store_id"] == 1
    assert data_default["store_revenue_today_vnd"] > 0
    assert data_default["store_orders_count"] > 0


def test_store_manager_access_other_store_forbidden(setup_analytics_db):
    db = setup_analytics_db()
    store_mgr = db.execute(select(Customer).where(Customer.customer_id == 20)).scalar_one()
    client = make_client_for_user(store_mgr)

    res = client.get("/api/v1/admin/analytics/role-metrics?target_role=store&store_id=2")
    assert res.status_code == 403
    assert "Bạn chỉ được phép xem dữ liệu cửa hàng do mình phụ trách" in res.text


def test_store_manager_without_store_id_forbidden(setup_analytics_db):
    db = setup_analytics_db()
    unassigned_mgr = Customer(
        customer_id=99,
        public_id=uuid7(),
        role="store_manager",
        display_name="Unassigned Store Mgr",
        store_id=None,
        status="active",
    )
    db.add(unassigned_mgr)
    db.commit()

    client = make_client_for_user(unassigned_mgr)

    # Omitting store_id -> 403 Forbidden
    res1 = client.get("/api/v1/admin/analytics/role-metrics?target_role=store")
    assert res1.status_code == 403
    assert "Bạn chỉ được phép xem dữ liệu cửa hàng do mình phụ trách" in res1.text

    # Passing explicit store_id -> 403 Forbidden
    res2 = client.get("/api/v1/admin/analytics/role-metrics?target_role=store&store_id=1")
    assert res2.status_code == 403
    assert "Bạn chỉ được phép xem dữ liệu cửa hàng do mình phụ trách" in res2.text


def test_department_managers_role_isolation(setup_analytics_db):
    db = setup_analytics_db()

    sales_mgr = db.execute(select(Customer).where(Customer.customer_id == 30)).scalar_one()
    mkt_mgr = db.execute(select(Customer).where(Customer.customer_id == 40)).scalar_one()
    inv_mgr = db.execute(select(Customer).where(Customer.customer_id == 50)).scalar_one()
    ops_mgr = db.execute(select(Customer).where(Customer.customer_id == 60)).scalar_one()
    sys_mgr = db.execute(select(Customer).where(Customer.customer_id == 70)).scalar_one()

    # Sales manager
    client_sales = make_client_for_user(sales_mgr)
    assert client_sales.get("/api/v1/admin/analytics/role-metrics?target_role=sales").status_code == 200
    assert client_sales.get("/api/v1/admin/analytics/role-metrics?target_role=marketing").status_code == 403
    assert client_sales.get("/api/v1/admin/analytics/role-metrics?target_role=executive").status_code == 403

    # Marketing manager
    client_mkt = make_client_for_user(mkt_mgr)
    assert client_mkt.get("/api/v1/admin/analytics/role-metrics?target_role=marketing").status_code == 200
    assert client_mkt.get("/api/v1/admin/analytics/role-metrics?target_role=sales").status_code == 403
    assert client_mkt.get("/api/v1/admin/analytics/role-metrics?target_role=executive").status_code == 403

    # Inventory manager
    client_inv = make_client_for_user(inv_mgr)
    assert client_inv.get("/api/v1/admin/analytics/role-metrics?target_role=inventory").status_code == 200
    assert client_inv.get("/api/v1/admin/analytics/role-metrics?target_role=store").status_code == 403
    assert client_inv.get("/api/v1/admin/analytics/role-metrics?target_role=executive").status_code == 403

    # Operations manager
    client_ops = make_client_for_user(ops_mgr)
    assert client_ops.get("/api/v1/admin/analytics/role-metrics?target_role=operations").status_code == 200
    assert client_ops.get("/api/v1/admin/analytics/role-metrics?target_role=system").status_code == 403
    assert client_ops.get("/api/v1/admin/analytics/role-metrics?target_role=executive").status_code == 403

    # System admin
    client_sys = make_client_for_user(sys_mgr)
    assert client_sys.get("/api/v1/admin/analytics/role-metrics?target_role=system").status_code == 200
    assert client_sys.get("/api/v1/admin/analytics/role-metrics?target_role=marketing").status_code == 403
    assert client_sys.get("/api/v1/admin/analytics/role-metrics?target_role=executive").status_code == 403


def test_customer_cannot_access_role_metrics(setup_analytics_db):
    db = setup_analytics_db()
    customer = db.execute(select(Customer).where(Customer.customer_id == 80)).scalar_one()
    client = make_client_for_user(customer)

    res = client.get("/api/v1/admin/analytics/role-metrics?target_role=executive")
    assert res.status_code == 403


def test_sales_trend_endpoint_rbac_and_data(setup_analytics_db):
    db = setup_analytics_db()
    admin = db.execute(select(Customer).where(Customer.role == "admin")).scalar_one()
    sales_mgr = db.execute(select(Customer).where(Customer.customer_id == 30)).scalar_one()
    mkt_mgr = db.execute(select(Customer).where(Customer.customer_id == 40)).scalar_one()

    # Admin access -> 200
    client_admin = make_client_for_user(admin)
    res_admin = client_admin.get("/api/v1/admin/analytics/sales-trend?days=30")
    assert res_admin.status_code == 200
    data = res_admin.json()
    assert "points" in data
    assert isinstance(data["points"], list)

    # Sales manager access -> 200
    client_sales = make_client_for_user(sales_mgr)
    res_sales = client_sales.get("/api/v1/admin/analytics/sales-trend?days=30")
    assert res_sales.status_code == 200

    # Marketing manager access -> 403
    client_mkt = make_client_for_user(mkt_mgr)
    res_mkt = client_mkt.get("/api/v1/admin/analytics/sales-trend?days=30")
    assert res_mkt.status_code == 403


def test_superset_config_endpoint_removed(setup_analytics_db):
    db = setup_analytics_db()
    admin = db.execute(select(Customer).where(Customer.role == "admin")).scalar_one()

    client_admin = make_client_for_user(admin)
    res = client_admin.get("/api/v1/admin/analytics/superset-config")
    assert res.status_code == 404


def test_overview_endpoint(setup_analytics_db):
    db = setup_analytics_db()
    admin = db.execute(select(Customer).where(Customer.role == "admin")).scalar_one()
    store_mgr = db.execute(select(Customer).where(Customer.customer_id == 20)).scalar_one()

    # Admin -> 200
    client_admin = make_client_for_user(admin)
    res_admin = client_admin.get("/api/v1/admin/analytics/overview")
    assert res_admin.status_code == 200
    assert "cogs_vnd" in res_admin.json()

    # Store manager -> 403
    client_store = make_client_for_user(store_mgr)
    assert client_store.get("/api/v1/admin/analytics/overview").status_code == 403


def test_invalid_target_role_returns_error(setup_analytics_db):
    db = setup_analytics_db()
    admin = db.execute(select(Customer).where(Customer.role == "admin")).scalar_one()
    client = make_client_for_user(admin)

    res = client.get("/api/v1/admin/analytics/role-metrics?target_role=nonexistent_role")
    assert res.status_code == 400
    assert "không hợp lệ" in res.text
