import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.sql.elements import TextClause

from app.core.ids import uuid7
from app.db.base import Base
import app.db.uow
import app.models  # noqa: F401
from app.models.cart import Cart, CartItem
from app.models.catalog import Category, Product, ProductVariant
from app.models.customer import Customer
from app.models.inventory import Inventory
from app.models.multicity import City, Store, StoreInventory
from app.models.order import Order, OrderItem
from app.modules.checkout.schemas import CheckoutRequest
from app.modules.checkout.service import checkout
from app.modules.pos.schemas import POSTItemRequest, POSTransactionRequest
from app.modules.pos.service import create_pos_transaction


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

    # Seed City and Store
    city = City(city_id=1, code="HCM", name="TP Ho Chi Minh", is_active=True)
    store = Store(
        store_id=1,
        city_id=1,
        code="STR01",
        name="Store 1",
        address="123 Le Loi, Ben Nghe, Quan 1, TP Ho Chi Minh",
        phone="0901234567",
        is_active=True,
    )

    # Seed Catalog
    cat = Category(category_id=1, public_id=uuid7(), code="AO-NAM", name="Áo Nam", is_active=True)
    prod = Product(product_id=1, public_id=uuid7(), category_id=1, slug="ao-polo", name="Áo Polo Nam", is_active=True)
    var1 = ProductVariant(
        variant_id=1,
        public_id=uuid7(),
        product_id=1,
        sku="APN-001",
        size_code="L",
        color_code="DEN",
        price_vnd=300000,
        cost_price_vnd=150000,
        is_active=True,
    )
    var2 = ProductVariant(
        variant_id=2,
        public_id=uuid7(),
        product_id=1,
        sku="APN-002",
        size_code="M",
        color_code="TRANG",
        price_vnd=250000,
        cost_price_vnd=110000,
        is_active=True,
    )

    # Seed Inventory (central warehouse)
    inv1 = Inventory(variant_id=1, opening_on_hand=100, on_hand=100, version=1)
    inv2 = Inventory(variant_id=2, opening_on_hand=100, on_hand=100, version=1)

    # Seed StoreInventory
    store_inv1 = StoreInventory(store_inventory_id=1, store_id=1, variant_id=1, opening_on_hand=50, on_hand=50, version=1)
    store_inv2 = StoreInventory(store_inventory_id=2, store_id=1, variant_id=2, opening_on_hand=50, on_hand=50, version=1)

    # Seed Customers
    c1 = Customer(
        customer_id=1,
        public_id=uuid7(),
        role="customer",
        display_name="Danh Tran",
        status="active",
        is_cod_blocked=False,
        boom_count=0,
    )
    staff = Customer(
        customer_id=2,
        public_id=uuid7(),
        role="store_manager",
        display_name="Staff Nam",
        status="active",
        is_cod_blocked=False,
        boom_count=0,
    )

    db.add_all([city, store, cat, prod, var1, var2, inv1, inv2, store_inv1, store_inv2, c1, staff])
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


def create_cart_with_items(session, customer_id: int, items: list[tuple[int, int]]) -> Cart:
    cart = Cart(public_id=uuid7(), customer_id=customer_id, status="active")
    session.add(cart)
    session.flush()
    for variant_id, quantity in items:
        session.add(CartItem(cart_id=cart.cart_id, variant_id=variant_id, quantity=quantity, is_present=True))
    session.commit()
    return cart


def test_online_checkout_snapshots_cost_price_vnd(test_db):
    create_cart_with_items(test_db, customer_id=1, items=[(1, 2), (2, 1)])

    payload = CheckoutRequest(
        receiver_name="Danh Tran",
        receiver_phone="0912345678",
        shipping_address_text="123 Le Loi, Ben Nghe, Quan 1, TP Ho Chi Minh",
        payment_method="cod",
    )
    res = checkout(customer_id=1, idempotency_key="idemp-online-cogs-1", payload=payload)

    order = test_db.execute(select(Order).where(Order.order_number == res.order_number)).scalar_one()
    items = (
        test_db.execute(
            select(OrderItem).where(OrderItem.order_id == order.order_id).order_by(OrderItem.variant_id)
        )
        .scalars()
        .all()
    )

    assert len(items) == 2

    # Variant 1: cost_price_vnd = 150_000, unit_price_vnd = 300_000, quantity = 2
    assert items[0].variant_id == 1
    assert items[0].cost_price_vnd == 150000
    assert items[0].unit_price_vnd == 300000
    assert items[0].quantity == 2
    assert items[0].line_total_vnd == 600000

    # Variant 2: cost_price_vnd = 110_000, unit_price_vnd = 250_000, quantity = 1
    assert items[1].variant_id == 2
    assert items[1].cost_price_vnd == 110000
    assert items[1].unit_price_vnd == 250000
    assert items[1].quantity == 1
    assert items[1].line_total_vnd == 250000


def test_pos_checkout_snapshots_cost_price_vnd(test_db):
    request = POSTransactionRequest(
        store_id=1,
        items=[
            POSTItemRequest(variant_id=1, quantity=3),
            POSTItemRequest(variant_id=2, quantity=1),
        ],
        payment_method="cash",
    )
    res = create_pos_transaction(request=request, staff_id=2)

    order = test_db.execute(select(Order).where(Order.order_number == res["order_number"])).scalar_one()
    items = (
        test_db.execute(
            select(OrderItem).where(OrderItem.order_id == order.order_id).order_by(OrderItem.variant_id)
        )
        .scalars()
        .all()
    )

    assert len(items) == 2

    # Variant 1: cost_price_vnd = 150_000
    assert items[0].variant_id == 1
    assert items[0].cost_price_vnd == 150000
    assert items[0].unit_price_vnd == 300000
    assert items[0].quantity == 3
    assert items[0].line_total_vnd == 900000

    # Variant 2: cost_price_vnd = 110_000
    assert items[1].variant_id == 2
    assert items[1].cost_price_vnd == 110000
    assert items[1].unit_price_vnd == 250000
    assert items[1].quantity == 1
    assert items[1].line_total_vnd == 250000


def test_cost_price_mutation_does_not_alter_existing_order_items(test_db):
    # 1. Place initial online order
    create_cart_with_items(test_db, customer_id=1, items=[(1, 1)])
    online_payload = CheckoutRequest(
        receiver_name="Danh Tran",
        receiver_phone="0912345678",
        shipping_address_text="123 Le Loi, Ben Nghe, Quan 1, TP Ho Chi Minh",
        payment_method="cod",
    )
    online_res = checkout(customer_id=1, idempotency_key="idemp-online-cogs-imm-1", payload=online_payload)

    # 2. Place initial POS order
    pos_req = POSTransactionRequest(
        store_id=1,
        items=[POSTItemRequest(variant_id=1, quantity=1)],
        payment_method="cash",
    )
    pos_res = create_pos_transaction(request=pos_req, staff_id=2)

    # Verify both snapshotted 150_000 initially
    online_order = test_db.execute(select(Order).where(Order.order_number == online_res.order_number)).scalar_one()
    online_item = test_db.execute(select(OrderItem).where(OrderItem.order_id == online_order.order_id)).scalar_one()
    assert online_item.cost_price_vnd == 150000

    pos_order = test_db.execute(select(Order).where(Order.order_number == pos_res["order_number"])).scalar_one()
    pos_item = test_db.execute(select(OrderItem).where(OrderItem.order_id == pos_order.order_id)).scalar_one()
    assert pos_item.cost_price_vnd == 150000

    # 3. Mutate variant cost_price_vnd
    variant1 = test_db.execute(select(ProductVariant).where(ProductVariant.variant_id == 1)).scalar_one()
    variant1.cost_price_vnd = 220000
    test_db.commit()

    # Verify variant updated in DB
    refreshed_variant = test_db.execute(select(ProductVariant).where(ProductVariant.variant_id == 1)).scalar_one()
    assert refreshed_variant.cost_price_vnd == 220000

    # 4. Verify historical order items are completely unchanged
    test_db.expire_all()
    past_online_item = test_db.execute(
        select(OrderItem).where(OrderItem.order_item_id == online_item.order_item_id)
    ).scalar_one()
    assert past_online_item.cost_price_vnd == 150000

    past_pos_item = test_db.execute(
        select(OrderItem).where(OrderItem.order_item_id == pos_item.order_item_id)
    ).scalar_one()
    assert past_pos_item.cost_price_vnd == 150000

    # 5. New online checkout uses the new cost_price_vnd
    create_cart_with_items(test_db, customer_id=1, items=[(1, 1)])
    new_online_res = checkout(customer_id=1, idempotency_key="idemp-online-cogs-imm-2", payload=online_payload)
    new_order = test_db.execute(select(Order).where(Order.order_number == new_online_res.order_number)).scalar_one()
    new_item = test_db.execute(select(OrderItem).where(OrderItem.order_id == new_order.order_id)).scalar_one()
    assert new_item.cost_price_vnd == 220000

    # 6. Past items still remain 150000
    test_db.expire_all()
    assert (
        test_db.execute(
            select(OrderItem.cost_price_vnd).where(OrderItem.order_item_id == online_item.order_item_id)
        ).scalar_one()
        == 150000
    )
    assert (
        test_db.execute(
            select(OrderItem.cost_price_vnd).where(OrderItem.order_item_id == pos_item.order_item_id)
        ).scalar_one()
        == 150000
    )


def test_checkout_with_zero_cost_price_vnd(test_db):
    # Set variant 2 cost_price_vnd to 0
    var2 = test_db.execute(select(ProductVariant).where(ProductVariant.variant_id == 2)).scalar_one()
    var2.cost_price_vnd = 0
    test_db.commit()

    # Online checkout with zero cost variant
    create_cart_with_items(test_db, customer_id=1, items=[(2, 1)])
    online_res = checkout(
        customer_id=1,
        idempotency_key="idemp-online-zero-cost",
        payload=CheckoutRequest(
            receiver_name="Danh Tran",
            receiver_phone="0912345678",
            shipping_address_text="123 Le Loi, Ben Nghe, Quan 1, TP Ho Chi Minh",
            payment_method="cod",
        ),
    )
    online_order = test_db.execute(select(Order).where(Order.order_number == online_res.order_number)).scalar_one()
    online_item = test_db.execute(select(OrderItem).where(OrderItem.order_id == online_order.order_id)).scalar_one()
    assert online_item.cost_price_vnd == 0

    # POS checkout with zero cost variant
    pos_res = create_pos_transaction(
        request=POSTransactionRequest(
            store_id=1,
            items=[POSTItemRequest(variant_id=2, quantity=1)],
            payment_method="cash",
        ),
        staff_id=2,
    )
    pos_order = test_db.execute(select(Order).where(Order.order_number == pos_res["order_number"])).scalar_one()
    pos_item = test_db.execute(select(OrderItem).where(OrderItem.order_id == pos_order.order_id)).scalar_one()
    assert pos_item.cost_price_vnd == 0

