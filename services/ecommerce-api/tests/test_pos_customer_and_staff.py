import app.db.deps
import app.db.uow
import pytest
from app.core.errors import AppError
from app.core.ids import uuid7
from app.db.base import Base
from app.models.catalog import Category, Product, ProductVariant
from app.models.customer import Customer
from app.models.multicity import City, Store, StoreInventory
from app.models.order import Order
from app.modules.pos.schemas import POSTItemRequest, POSTransactionRequest
from app.modules.pos.service import create_pos_transaction
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
def pos_db(monkeypatch):
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

    db = session_factory()
    # Seed city & store
    city = City(city_id=1, code="SGN", name="Hồ Chí Minh")
    store = Store(store_id=1, city_id=1, code="STR-01", name="Store 1", address="123 Lê Lợi", phone="0901234567", is_active=True)
    db.add_all([city, store])

    # Seed staff & member customer
    staff = Customer(customer_id=10, public_id=uuid7(), role="store_manager", display_name="Cashier Staff", status="active")
    member = Customer(customer_id=20, public_id=uuid7(), role="customer", display_name="Member Customer", status="active")
    db.add_all([staff, member])

    # Seed catalog & store inventory
    cat = Category(category_id=1, public_id=uuid7(), code="AO", name="Áo", is_active=True)
    prod = Product(product_id=1, public_id=uuid7(), category_id=1, slug="ao-thun", name="Áo Thun", is_active=True)
    var = ProductVariant(variant_id=1, public_id=uuid7(), product_id=1, sku="AT-01", size_code="L", color_code="DEN", price_vnd=150000, is_active=True)
    store_inv = StoreInventory(store_inventory_id=1, store_id=1, variant_id=1, on_hand=50, opening_on_hand=50, version=1)
    db.add_all([cat, prod, var, store_inv])

    db.commit()
    yield db
    db.close()


def test_pos_walk_in_guest_order(pos_db):
    req = POSTransactionRequest(
        store_id=1,
        items=[POSTItemRequest(variant_id=1, quantity=2)],
        payment_method="cash",
        customer_id=None,
    )
    res = create_pos_transaction(req, staff_id=10)
    assert res["status"] == "completed"
    assert res["staff_id"] == 10
    assert res["customer_id"] is None

    order = pos_db.execute(select(Order).where(Order.order_number == res["order_number"])).scalar_one()
    assert order.channel == "pos"
    assert order.customer_id is None
    assert order.staff_id == 10
    assert order.receiver_name == "POS Customer"


def test_pos_member_customer_order(pos_db):
    req = POSTransactionRequest(
        store_id=1,
        items=[POSTItemRequest(variant_id=1, quantity=1)],
        payment_method="vietqr",
        customer_id=20,
    )
    res = create_pos_transaction(req, staff_id=10)
    assert res["status"] == "completed"
    assert res["staff_id"] == 10
    assert res["customer_id"] == 20

    order = pos_db.execute(select(Order).where(Order.order_number == res["order_number"])).scalar_one()
    assert order.channel == "pos"
    assert order.customer_id == 20
    assert order.staff_id == 10
    assert order.receiver_name == "Member Customer"


def test_pos_supports_card_payment(pos_db):
    req = POSTransactionRequest(
        store_id=1,
        items=[POSTItemRequest(variant_id=1, quantity=1)],
        payment_method="card",
        customer_id=None,
    )
    res = create_pos_transaction(req, staff_id=10)
    assert res["payment_method"] == "card"


def test_pos_rejects_unknown_member_customer(pos_db):
    req = POSTransactionRequest(
        store_id=1,
        items=[POSTItemRequest(variant_id=1, quantity=1)],
        payment_method="cash",
        customer_id=999,
    )

    with pytest.raises(AppError) as exc_info:
        create_pos_transaction(req, staff_id=10)

    assert exc_info.value.status_code == 404


def test_pos_rejects_staff_as_member_customer(pos_db):
    req = POSTransactionRequest(
        store_id=1,
        items=[POSTItemRequest(variant_id=1, quantity=1)],
        payment_method="cash",
        customer_id=10,
    )

    with pytest.raises(AppError) as exc_info:
        create_pos_transaction(req, staff_id=10)

    assert exc_info.value.status_code == 409


def test_pos_rejects_insufficient_cash(pos_db):
    req = POSTransactionRequest(
        store_id=1,
        items=[POSTItemRequest(variant_id=1, quantity=1)],
        payment_method="cash",
        amount_received_vnd=149999,
    )

    with pytest.raises(AppError) as exc_info:
        create_pos_transaction(req, staff_id=10)

    assert exc_info.value.status_code == 400
