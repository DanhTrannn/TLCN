import app.db.deps
import app.db.uow
import pytest
from app.core.ids import uuid7
from app.db.base import Base
from app.models.inventory import Inventory
from app.models.inventory_tx import InventoryTransaction
from app.modules.checkout.allocation import deduct_inventory
from sqlalchemy import create_engine, event, func, select
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
def ledger_db(monkeypatch):
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
    inv = Inventory(variant_id=1, on_hand=100, opening_on_hand=100, version=1)
    db.add(inv)
    db.commit()
    yield db
    db.close()


def test_checkout_deduct_inventory_creates_ledger(ledger_db):
    items = [{"variant_id": 1, "quantity": 5}]
    deduct_inventory(ledger_db, items, reference_code="ORD-ONLINE-100")
    ledger_db.commit()

    inv = ledger_db.scalar(select(Inventory).where(Inventory.variant_id == 1))
    assert inv.on_hand == 95

    tx = ledger_db.scalar(
        select(InventoryTransaction).where(InventoryTransaction.reference_code == "ORD-ONLINE-100")
    )
    assert tx is not None
    assert tx.movement_type == "outbound_order"
    assert tx.quantity_delta == -5
    assert tx.location_type == "central_warehouse"


def test_inventory_movement_pair_restores_balance(ledger_db):
    # Simulate outbound_order
    deduct_inventory(ledger_db, [{"variant_id": 1, "quantity": 10}], reference_code="ORD-1")

    # Simulate cancellation restoration
    inv = ledger_db.scalar(select(Inventory).where(Inventory.variant_id == 1))
    inv.on_hand += 10
    inv.version += 1
    ledger_db.add(
        InventoryTransaction(
            public_id=uuid7(),
            variant_id=1,
            location_type="central_warehouse",
            store_id=None,
            movement_type="order_cancellation",
            quantity_delta=+10,
            reference_code="ORD-1",
            notes="Hoàn kho do hủy đơn",
        )
    )
    ledger_db.commit()

    # The outbound and compensating cancellation movements net to zero. This
    # checks an operation pair, not a global opening-balance equation: inbound
    # receipts also expand opening_on_hand to preserve the stock ceiling.
    delta_sum = ledger_db.scalar(
        select(func.sum(InventoryTransaction.quantity_delta)).where(
            InventoryTransaction.variant_id == 1
        )
    )
    assert delta_sum == 0
    assert inv.opening_on_hand + delta_sum == inv.on_hand
