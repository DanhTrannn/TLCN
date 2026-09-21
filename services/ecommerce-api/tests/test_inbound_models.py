import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import CheckConstraint, create_engine, event, select
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.sql.elements import TextClause

from app.core.ids import uuid7
from app.db.base import Base
import app.models  # noqa: F401
from app.models.catalog import Category, Product, ProductVariant
from app.models.customer import Customer
from app.models.inbound import InboundReceipt, InboundReceiptItem


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
def db_session():
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
    db = testing_session()

    yield db
    db.close()
    engine.dispose()


@pytest.fixture()
def test_staff_user(db_session):
    staff = Customer(
        customer_id=1,
        public_id=str(uuid7()),
        role="admin",
        display_name="Admin Staff",
        status="active",
    )
    db_session.add(staff)
    db_session.commit()
    return staff


@pytest.fixture()
def test_variant(db_session):
    cat = Category(
        category_id=1,
        public_id=str(uuid7()),
        code="CAT-01",
        name="Category 1",
        is_active=True,
    )
    db_session.add(cat)
    db_session.flush()

    prod = Product(
        product_id=1,
        public_id=str(uuid7()),
        category_id=cat.category_id,
        slug="dam-thu-dong",
        name="Đầm Thu Đông",
        is_active=True,
    )
    db_session.add(prod)
    db_session.flush()

    variant = ProductVariant(
        variant_id=1,
        public_id=str(uuid7()),
        product_id=prod.product_id,
        sku="DAM-TD-RED-M",
        size_code="M",
        color_code="RED",
        price_vnd=250000,
        cost_price_vnd=0,
        is_active=True,
    )
    db_session.add(variant)
    db_session.commit()
    return variant


def test_inbound_receipt_and_item_creation(db_session, test_staff_user, test_variant):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    receipt = InboundReceipt(
        public_id=uuid.uuid4(),
        receipt_code="INB-20260921-000001",
        batch_name="Lô đầm Thu Đông đợt 1",
        status="completed",
        total_items_count=100,
        total_cost_vnd=12000000,
        notes="Kiểm đếm đầy đủ",
        created_by_customer_id=test_staff_user.customer_id,
        created_at=now,
        updated_at=now,
    )
    db_session.add(receipt)
    db_session.flush()

    item = InboundReceiptItem(
        public_id=uuid.uuid4(),
        receipt_id=receipt.receipt_id,
        variant_id=test_variant.variant_id,
        quantity=100,
        unit_cost_vnd=120000,
        total_cost_vnd=12000000,
        previous_cost_price_vnd=0,
        new_cost_price_vnd=120000,
        created_at=now,
    )
    db_session.add(item)
    db_session.commit()

    saved = db_session.scalar(
        select(InboundReceipt).where(InboundReceipt.receipt_id == receipt.receipt_id)
    )
    assert saved is not None
    assert saved.receipt_code == "INB-20260921-000001"
    assert len(saved.items) == 1
    assert saved.items[0].quantity == 100
    assert saved.items[0].new_cost_price_vnd == 120000


def test_inbound_receipt_table_invariants():
    table = InboundReceipt.__table__
    indexes = {index.name: index for index in table.indexes}
    assert indexes["uq_inbound_receipts_public_id"].unique is True
    assert indexes["uq_inbound_receipts_code"].unique is True
    assert "ix_inbound_receipts_created_at_id" in indexes

    check_names = {c.name for c in table.constraints if isinstance(c, CheckConstraint)}
    assert any("status" in name for name in check_names)
    assert any("items_count" in name for name in check_names)
    assert any("total_cost" in name for name in check_names)


def test_inbound_receipt_item_table_invariants():
    table = InboundReceiptItem.__table__
    indexes = {index.name: index for index in table.indexes}
    assert indexes["uq_inbound_items_public_id"].unique is True
    assert "ix_inbound_items_receipt_id" in indexes
    assert "ix_inbound_items_variant_id" in indexes

    check_names = {c.name for c in table.constraints if isinstance(c, CheckConstraint)}
    assert any("quantity" in name for name in check_names)
    assert any("unit_cost" in name for name in check_names)
    assert any("total_cost" in name for name in check_names)
