"""Integration tests for Comprehensive Seed & Demo Scenarios Script (Gói 4 - Task 4)."""

import uuid
from datetime import UTC, datetime, timedelta
import pytest
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.sql.elements import TextClause

from app.db.base import Base
import app.db.uow
import app.models  # noqa: F401
from app.models.catalog import ProductVariant
from app.models.customer import Customer, CustomerCredential
from app.models.inbound import InboundReceipt, InboundReceiptItem
from app.models.inventory import Inventory
from app.models.inventory_tx import InventoryTransaction
from app.models.logistics import Shipment
from app.models.multicity import Store
from app.models.order import Order, OrderItem, Payment, Refund
from app.models.promotion import Coupon, CouponRedemption
from app.models.returns import ReturnItem, ReturnRequest
from app.models.review import ProductReview
from app.modules.analytics.service import (
    get_executive_metrics,
    get_inventory_metrics,
    get_marketing_metrics,
    get_operations_metrics,
    get_sales_metrics,
    get_store_metrics,
    get_system_metrics,
)

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from database.seeds.seed_demo_scenarios import seed_demo_data


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
def test_db(monkeypatch):
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

    session = testing_session()
    try:
        yield session
    finally:
        session.close()


def test_seed_demo_data_populates_all_domains(test_db):
    """Calling seed_demo_data populates accounts, catalog, inbound, orders, logistics, returns, marketing."""
    counts = seed_demo_data(test_db)

    # 1. Verify summary dictionary structure
    expected_keys = {
        "customers",
        "inbound_receipts",
        "orders",
        "payments",
        "shipments",
        "returns",
        "refunds",
        "reviews",
        "coupons",
    }
    assert expected_keys.issubset(counts.keys())
    assert counts["customers"] >= 8
    assert counts["inbound_receipts"] >= 3
    assert counts["orders"] >= 25
    assert counts["payments"] >= 25
    assert counts["shipments"] >= 20
    assert counts["returns"] >= 2
    assert counts["refunds"] >= 1
    assert counts["reviews"] >= 2
    assert counts["coupons"] >= 1

    # 2. Verify Accounts: 7 demo staff roles + normal customers
    required_roles = {
        "admin",
        "sales_manager",
        "marketing_manager",
        "store_manager",
        "inventory_manager",
        "operations_manager",
        "system_admin",
    }
    db_roles = set(test_db.scalars(select(Customer.role)).all())
    assert required_roles.issubset(db_roles)
    assert "customer" in db_roles

    # Store manager must be linked to a store
    store_mgr = test_db.execute(
        select(Customer).where(Customer.role == "store_manager")
    ).scalars().first()
    assert store_mgr is not None
    assert store_mgr.store_id is not None
    assert test_db.get(Store, store_mgr.store_id) is not None

    # Credentials exist
    credentials_count = test_db.scalar(select(func.count()).select_from(CustomerCredential))
    assert credentials_count >= 8

    # 3. Verify Inbound & Costing
    inbound_receipts = test_db.scalars(select(InboundReceipt)).all()
    assert len(inbound_receipts) >= 3
    for receipt in inbound_receipts:
        assert receipt.status == "completed"
        assert receipt.total_items_count > 0
        assert receipt.total_cost_vnd > 0

    receipt_items = test_db.scalars(select(InboundReceiptItem)).all()
    assert len(receipt_items) >= 3
    for item in receipt_items:
        assert item.new_cost_price_vnd > 0

    # Variants have cost_price_vnd updated and > 0
    variants = test_db.scalars(select(ProductVariant)).all()
    assert len(variants) > 0
    assert any(v.cost_price_vnd > 0 for v in variants)

    # Inbound inventory transactions logged
    inbound_txs = test_db.scalars(
        select(InventoryTransaction).where(InventoryTransaction.movement_type == "inbound")
    ).all()
    assert len(inbound_txs) >= 3

    # DB constraint on inventory: on_hand <= opening_on_hand
    inventories = test_db.scalars(select(Inventory)).all()
    assert len(inventories) > 0
    for inv in inventories:
        assert inv.on_hand <= inv.opening_on_hand

    # 4. Verify Orders (25+ orders spanning past 14 days)
    orders = test_db.scalars(select(Order)).all()
    assert len(orders) >= 25

    # Delivered online orders
    delivered_orders = [o for o in orders if o.status == "delivered" and o.channel == "online"]
    assert len(delivered_orders) >= 15
    for order in delivered_orders:
        assert order.paid_at is not None
        # Order items have snapshotted cost_price_vnd > 0
        order_items = test_db.scalars(select(OrderItem).where(OrderItem.order_id == order.order_id)).all()
        assert len(order_items) > 0
        for oi in order_items:
            assert oi.cost_price_vnd > 0
            assert oi.line_total_vnd == oi.unit_price_vnd * oi.quantity

    # Completed POS store orders
    pos_orders = [o for o in orders if o.status == "completed" and o.channel == "pos"]
    assert len(pos_orders) >= 5
    for order in pos_orders:
        assert order.store_id is not None
        pos_items = test_db.scalars(select(OrderItem).where(OrderItem.order_id == order.order_id)).all()
        assert len(pos_items) > 0
        for oi in pos_items:
            assert oi.cost_price_vnd > 0

    # Failed delivery (boom) orders
    boom_orders = [o for o in orders if o.status == "failed_delivery"]
    assert len(boom_orders) >= 3
    for order in boom_orders:
        shipment = test_db.scalars(
            select(Shipment).where(Shipment.order_id == order.order_id)
        ).first()
        assert shipment is not None
        assert shipment.status == "failed"
        assert shipment.failure_reason is not None

    # Customer return requests
    returns = test_db.scalars(select(ReturnRequest)).all()
    assert len(returns) >= 2
    # 1 completed with passed inspection and refund succeeded
    completed_return = [r for r in returns if r.status == "completed"]
    assert len(completed_return) >= 1
    cr = completed_return[0]
    return_item = test_db.scalars(select(ReturnItem).where(ReturnItem.return_id == cr.return_id)).first()
    assert return_item is not None
    assert return_item.inspection_status == "passed"

    # Refund succeeded exists
    refund = test_db.scalars(select(Refund).where(Refund.status == "succeeded")).first()
    assert refund is not None
    assert refund.completed_at is not None
    assert refund.amount_vnd > 0

    # Payments exist with matching amounts
    payments = test_db.scalars(select(Payment)).all()
    assert len(payments) >= len(orders)
    for p in payments:
        matching_order = test_db.get(Order, p.order_id)
        assert matching_order is not None
        assert p.amount_vnd == matching_order.total_vnd

    # 5. Verify Marketing: Coupons & Reviews
    active_coupon = test_db.scalars(
        select(Coupon).where(Coupon.is_active == True)  # noqa: E712
    ).first()
    assert active_coupon is not None

    redemptions = test_db.scalars(select(CouponRedemption)).all()
    assert len(redemptions) >= 1

    reviews = test_db.scalars(select(ProductReview).where(ProductReview.status == "approved")).all()
    assert len(reviews) >= 2
    for rev in reviews:
        assert 1 <= rev.rating <= 5
        assert rev.order_item_id is not None
        assert rev.product_id is not None


def test_seed_demo_data_is_idempotent(test_db):
    """Running seed_demo_data twice succeeds and does not cause integrity errors."""
    counts_1 = seed_demo_data(test_db)
    counts_2 = seed_demo_data(test_db)

    # Calling seed again must not duplicate orders, inbound batches, etc.
    assert counts_1["orders"] == counts_2["orders"]
    assert counts_1["inbound_receipts"] == counts_2["inbound_receipts"]
    assert counts_1["customers"] == counts_2["customers"]
    assert counts_1["coupons"] == counts_2["coupons"]


def test_seed_demo_data_analytics_dashboards_queryable(test_db):
    """Verify that all 7 role-based analytics metrics functions run successfully on the seeded data."""
    seed_demo_data(test_db)

    # Executive
    exec_metrics = get_executive_metrics(test_db)
    assert exec_metrics.role == "executive"
    assert exec_metrics.gmv_vnd > 0
    assert exec_metrics.cogs_vnd > 0
    assert exec_metrics.total_orders >= 25
    assert exec_metrics.boom_rate_percent > 0.0

    # Sales
    sales_metrics = get_sales_metrics(test_db)
    assert sales_metrics.role == "sales"
    assert len(sales_metrics.store_contributions) > 0
    assert len(sales_metrics.top_selling_products) > 0

    # Marketing
    mkt_metrics = get_marketing_metrics(test_db)
    assert mkt_metrics.role == "marketing"
    assert mkt_metrics.total_purchases >= 20

    # Store
    store_mgr = test_db.execute(
        select(Customer).where(Customer.role == "store_manager")
    ).scalars().first()
    store_metrics = get_store_metrics(test_db, store_mgr.store_id)
    assert store_metrics.role == "store"
    assert store_metrics.store_name is not None

    # Inventory
    inv_metrics = get_inventory_metrics(test_db)
    assert inv_metrics.role == "inventory"
    assert inv_metrics.total_inventory_value_vnd > 0
    assert inv_metrics.inbound_batches_count >= 3
    assert inv_metrics.warehouse_stock_units > 0

    # Operations
    ops_metrics = get_operations_metrics(test_db)
    assert ops_metrics.role == "operations"
    assert ops_metrics.boom_orders_count >= 3
    assert ops_metrics.return_requests_count >= 2

    # System
    sys_metrics = get_system_metrics(test_db)
    assert sys_metrics.role == "system"
    assert sys_metrics.pipeline_status == "healthy"
    assert len(sys_metrics.reconciliation_variance) >= 2
    orders_metric = next(m for m in sys_metrics.reconciliation_variance if m.metric_name == "total_orders")
    assert orders_metric.oltp_value >= 25
    rev_metric = next(m for m in sys_metrics.reconciliation_variance if m.metric_name == "gross_revenue_vnd")
    assert rev_metric.oltp_value > 0


def test_seed_demo_data_default_session_context_manager(monkeypatch):
    """Calling seed_demo_data() with session=None uses SessionLocal as a context manager."""
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
    monkeypatch.setattr("database.seeds.seed_demo_scenarios.SessionLocal", testing_session)

    counts = seed_demo_data()
    assert counts["orders"] >= 25
    assert counts["inbound_receipts"] >= 3
    assert counts["customers"] >= 8
