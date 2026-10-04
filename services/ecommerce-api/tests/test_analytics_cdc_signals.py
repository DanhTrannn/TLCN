"""Tests for CDC real-time operational signal schemas and role metric endpoints."""

import pytest
from app.modules.analytics.schemas import (
    CashInTransitSignal,
    ChannelPaceComparisonSignal,
    CriticalStockoutSignal,
    DepletionVelocitySignal,
    ExecutiveMetricsResponse,
    FulfillmentBottleneckSignal,
    HourlyMarginPoint,
    HourlyRunRatePoint,
    InventoryMetricsResponse,
    MarginErosionSignal,
    MarketingMetricsResponse,
    NegativeReviewSpikeSignal,
    OperationsMetricsResponse,
    RegionalBoomRateSignal,
    SalesMetricsResponse,
    StoreMetricsResponse,
    StoreRunRateSignal,
    StoreStockoutSignal,
    ViralProductSignal,
    VoucherBurnRateSignal,
)


def test_marketing_metrics_schema_includes_cdc_signals():
    resp = MarketingMetricsResponse(
        role="marketing",
        voucher_burn_rate=VoucherBurnRateSignal(
            coupon_code="SALE50K",
            used_count=850,
            usage_limit=1000,
            burn_rate_per_minute=56.6,
            budget_warning=True,
            budget_burn_percent=85.0,
        ),
        negative_review_spikes=[
            NegativeReviewSpikeSignal(
                product_id=1,
                product_name="Áo Polo Nam",
                negative_count=6,
                window_minutes=45,
                warning_alert="Phát hiện 6 review 1 sao trong 45 phút!",
            )
        ],
    )
    assert resp.voucher_burn_rate is not None
    assert resp.voucher_burn_rate.budget_warning is True
    assert resp.voucher_burn_rate.coupon_code == "SALE50K"
    assert len(resp.negative_review_spikes) == 1
    assert resp.negative_review_spikes[0].negative_count == 6


def test_inventory_metrics_schema_includes_cdc_signals():
    resp = InventoryMetricsResponse(
        role="inventory",
        depletion_velocity=[
            DepletionVelocitySignal(
                variant_id=10,
                sku="POLO-BLK-L",
                product_name="Áo Polo Basic Đen L",
                on_hand=15,
                units_sold_last_hour=60,
                depletion_rate_per_min=1.0,
                estimated_minutes_to_stockout=15,
                alert_level="critical",
            )
        ],
        critical_stockout_alerts=[
            CriticalStockoutSignal(
                variant_id=12,
                sku="JEAN-SLIM-32",
                product_name="Quần Jean Slim 32",
                on_hand=0,
                overselling_prevented=True,
            )
        ],
    )
    assert len(resp.depletion_velocity) == 1
    assert resp.depletion_velocity[0].estimated_minutes_to_stockout == 15
    assert len(resp.critical_stockout_alerts) == 1
    assert resp.critical_stockout_alerts[0].on_hand == 0
    assert resp.critical_stockout_alerts[0].overselling_prevented is True


def test_operations_metrics_schema_includes_cdc_signals():
    resp = OperationsMetricsResponse(
        role="operations",
        regional_boom_rates=[
            RegionalBoomRateSignal(
                region="Bình Tân",
                total_cod_shipments=50,
                failed_cod_shipments=19,
                boom_rate_percent=38.0,
                alert_level="high",
            )
        ],
        fulfillment_bottleneck=FulfillmentBottleneckSignal(
            paid_unfulfilled_orders=250,
            stale_unfulfilled_orders=42,
            bottleneck_warning=True,
            average_waiting_hours=2.5,
        ),
    )
    assert len(resp.regional_boom_rates) == 1
    assert resp.regional_boom_rates[0].boom_rate_percent == 38.0
    assert resp.fulfillment_bottleneck is not None
    assert resp.fulfillment_bottleneck.bottleneck_warning is True


def test_store_metrics_schema_includes_cdc_signals():
    resp = StoreMetricsResponse(
        role="store",
        store_id=1,
        store_stockouts=[
            StoreStockoutSignal(
                variant_id=20,
                sku="JEAN-REG-32",
                product_name="Quần Jean Regular Fit 32",
                on_hand=0,
            )
        ],
        run_rate=StoreRunRateSignal(
            daily_target_vnd=15000000,
            current_revenue_vnd=4200000,
            achievement_percent=28.0,
            projected_revenue_vnd=10500000,
            pace_status="behind",
            hourly_points=[
                HourlyRunRatePoint(hour="10:00", hourly_revenue_vnd=1000000, cumulative_revenue_vnd=1000000, target_vnd=2000000),
                HourlyRunRatePoint(hour="14:00", hourly_revenue_vnd=3200000, cumulative_revenue_vnd=4200000, target_vnd=6000000),
            ],
        ),
    )
    assert len(resp.store_stockouts) == 1
    assert resp.run_rate is not None
    assert resp.run_rate.pace_status == "behind"
    assert len(resp.run_rate.hourly_points) == 2


def test_sales_metrics_schema_includes_cdc_signals():
    resp = SalesMetricsResponse(
        role="sales",
        viral_products=[
            ViralProductSignal(
                product_id=5,
                product_name="Áo Sơ Mi Oxford Màu Be",
                units_sold_recent=48,
                growth_velocity_multiple=8.0,
                viral_badge=True,
            )
        ],
        channel_pace=ChannelPaceComparisonSignal(
            online_growth_percent=180.0,
            store_growth_percent=-40.0,
            dominant_channel="online",
            pace_divergence_warning=True,
        ),
    )
    assert len(resp.viral_products) == 1
    assert resp.viral_products[0].growth_velocity_multiple == 8.0
    assert resp.channel_pace is not None
    assert resp.channel_pace.dominant_channel == "online"


def test_executive_metrics_schema_includes_cdc_signals():
    resp = ExecutiveMetricsResponse(
        role="executive",
        margin_erosion=MarginErosionSignal(
            baseline_margin_percent=52.0,
            current_margin_percent=9.5,
            erosion_drop_percent=42.5,
            erosion_warning=True,
            lowest_margin_hour="14:00",
            hourly_margins=[
                HourlyMarginPoint(hour="09:00", revenue_vnd=100000000, cogs_vnd=48000000, margin_percent=52.0),
                HourlyMarginPoint(hour="14:00", revenue_vnd=300000000, cogs_vnd=271500000, margin_percent=9.5),
            ],
        ),
        cash_in_transit=CashInTransitSignal(
            total_cod_amount_vnd=320000000,
            dispatched_shipments_count=65,
            carrier_breakdown={"GHN": 200000000, "GHTK": 120000000},
        ),
    )
    assert resp.margin_erosion is not None
    assert resp.margin_erosion.erosion_warning is True
    assert len(resp.margin_erosion.hourly_margins) == 2
    assert resp.cash_in_transit is not None
    assert resp.cash_in_transit.total_cod_amount_vnd == 320000000
    assert resp.cash_in_transit.carrier_breakdown["GHN"] == 200000000


# -----------------------------------------------------------------------------
# Integration Tests for CDC Signal Aggregations (OLTP & Hybrid)
# -----------------------------------------------------------------------------

import uuid
from datetime import UTC, datetime, timedelta
from app.core.ids import uuid7
from app.db.base import Base
from app.models.catalog import Category, Product, ProductVariant
from app.models.customer import Customer
from app.models.inventory import Inventory
from app.models.logistics import Shipment
from app.models.multicity import City, Store, StoreInventory
from app.models.order import Order, OrderItem
from app.models.promotion import Coupon, CouponRedemption
from app.models.review import ProductReview
from app.modules.analytics.service import (
    _get_executive_metrics_oltp,
    _get_inventory_metrics_oltp,
    _get_marketing_metrics_oltp,
    _get_operations_metrics_oltp,
    _get_sales_metrics_oltp,
    _get_store_metrics_oltp,
    get_role_metrics_data,
)
from sqlalchemy import create_engine, event
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
def cdc_session():
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
    db = session_factory()

    now = datetime.now(UTC).replace(tzinfo=None)

    # 1. Base Master Data
    city = City(city_id=1, code="HCM", name="TP. Hồ Chí Minh", is_active=True)
    store = Store(
        store_id=1,
        city_id=1,
        code="STR-001",
        name="Flagship Q1",
        address="123 Lê Lợi, Q1",
        phone="02812345678",
        is_active=True,
    )
    cat = Category(
        category_id=1,
        public_id=uuid.uuid4(),
        code="CAT-AO-NAM",
        name="Áo Nam",
        is_active=True,
    )
    prod = Product(
        product_id=1,
        public_id=uuid.uuid4(),
        category_id=1,
        slug="ao-polo",
        name="Áo Polo Thể Thao",
        is_active=True,
    )
    variant1 = ProductVariant(
        variant_id=1,
        public_id=uuid.uuid4(),
        product_id=1,
        sku="POLO-BLK-M",
        size_code="M",
        color_code="Black",
        cost_price_vnd=100000,
        price_vnd=250000,
        is_active=True,
    )
    variant2 = ProductVariant(
        variant_id=2,
        public_id=uuid.uuid4(),
        product_id=1,
        sku="POLO-BLK-L",
        size_code="L",
        color_code="Black",
        cost_price_vnd=100000,
        price_vnd=250000,
        is_active=True,
    )
    customer = Customer(
        customer_id=1,
        public_id=uuid7(),
        display_name="Nguyễn Văn A",
        role="customer",
        status="active",
    )
    db.add_all([city, store, cat, prod, variant1, variant2, customer])
    db.commit()

    # 2. Inventory & Store Inventory
    wh_inv1 = Inventory(
        variant_id=1,
        on_hand=5,
        opening_on_hand=50,
    )
    wh_inv2 = Inventory(
        variant_id=2,
        on_hand=0,  # Critical stockout
        opening_on_hand=50,
    )
    st_inv = StoreInventory(
        store_inventory_id=1,
        store_id=1,
        variant_id=1,
        on_hand=0,  # Store stockout
        opening_on_hand=10,
    )
    db.add_all([wh_inv1, wh_inv2, st_inv])
    db.commit()

    # 3. Coupons & Redemptions (Marketing CDC)
    coupon = Coupon(
        coupon_id=1,
        public_id=uuid.uuid4(),
        code_normalized="SALE50K",
        discount_type="fixed_amount",
        discount_value=50000,
        minimum_subtotal_vnd=200000,
        starts_at=now - timedelta(days=1),
        ends_at=now + timedelta(days=1),
        total_usage_limit=1000,
        used_count=850,
        is_active=True,
    )
    db.add(coupon)
    db.commit()

    # 4. Orders, Items, Payments & Shipments (Operations, Executive, Sales CDC)
    order_online = Order(
        order_id=1,
        order_number="ORD-ONLINE-001",
        customer_id=1,
        checkout_idempotency_key=f"chk-{uuid.uuid4().hex[:30]}",
        store_id=None,
        channel="online",
        status="delivered",
        coupon_id=1,
        coupon_code_snapshot="SALE50K",
        coupon_type_snapshot="fixed_amount",
        coupon_value_snapshot=50000,
        subtotal_vnd=500000,
        discount_amount_vnd=50000,
        shipping_fee_vnd=30000,
        total_vnd=480000,
        receiver_name="Người Nhận 1",
        receiver_phone="0901234567",
        shipping_address_text="123 Đường Số 7, Bình Tân, TP. HCM",
        created_at=now - timedelta(hours=1),
    )
    order_pos = Order(
        order_id=2,
        order_number="ORD-POS-001",
        customer_id=1,
        checkout_idempotency_key=f"chk-{uuid.uuid4().hex[:30]}",
        store_id=1,
        channel="pos",
        status="completed",
        subtotal_vnd=250000,
        discount_amount_vnd=0,
        shipping_fee_vnd=0,
        total_vnd=250000,
        receiver_name="Người Nhận 2",
        receiver_phone="0901234567",
        shipping_address_text="Tại quầy",
        created_at=now - timedelta(hours=2),
    )
    order_stale = Order(
        order_id=3,
        order_number="ORD-STALE-001",
        customer_id=1,
        checkout_idempotency_key=f"chk-{uuid.uuid4().hex[:30]}",
        store_id=None,
        channel="online",
        status="paid",  # Waiting fulfillment > 2h
        subtotal_vnd=250000,
        discount_amount_vnd=0,
        shipping_fee_vnd=30000,
        total_vnd=280000,
        receiver_name="Người Nhận 3",
        receiver_phone="0901234567",
        shipping_address_text="456 Tên Lửa, Bình Tân, TP. HCM",
        created_at=now - timedelta(hours=3),
    )
    db.add_all([order_online, order_pos, order_stale])
    db.commit()

    item1 = OrderItem(
        order_item_id=1,
        public_id=uuid7(),
        order_id=1,
        variant_id=1,
        product_public_id_snapshot=uuid7(),
        category_code_snapshot="CAT-AO-NAM",
        category_name_snapshot="Áo Nam",
        product_name_snapshot="Áo Polo Thể Thao",
        sku_snapshot="POLO-BLK-M",
        size_code_snapshot="M",
        color_code_snapshot="Black",
        quantity=2,
        unit_price_vnd=250000,
        cost_price_vnd=100000,
        line_total_vnd=500000,
        created_at=now - timedelta(hours=1),
    )
    item2 = OrderItem(
        order_item_id=2,
        public_id=uuid7(),
        order_id=2,
        variant_id=1,
        product_public_id_snapshot=uuid7(),
        category_code_snapshot="CAT-AO-NAM",
        category_name_snapshot="Áo Nam",
        product_name_snapshot="Áo Polo Thể Thao",
        sku_snapshot="POLO-BLK-M",
        size_code_snapshot="M",
        color_code_snapshot="Black",
        quantity=1,
        unit_price_vnd=250000,
        cost_price_vnd=100000,
        line_total_vnd=250000,
        created_at=now - timedelta(hours=2),
    )
    db.add_all([item1, item2])
    db.commit()

    redemption = CouponRedemption(
        coupon_redemption_id=1,
        coupon_id=1,
        order_id=1,
        customer_id=1,
        status="redeemed",
        redeemed_at=now - timedelta(minutes=15),
    )
    db.add(redemption)

    # 5. Reviews (Marketing Review Spike)
    rev1 = ProductReview(
        review_id=1,
        public_id=uuid.uuid4(),
        order_item_id=1,
        customer_id=1,
        product_id=1,
        rating=1,
        content="Hàng lỗi chỉ may, chất lượng kém",
        status="approved",
        created_at=now - timedelta(minutes=30),
    )
    db.add(rev1)

    # 6. Shipments (Operations Boom Rate & Executive Cash-in-Transit)
    shipment_cod_transit = Shipment(
        shipment_id=1,
        public_id=uuid.uuid4(),
        shipment_code="SHIP-001",
        order_id=1,
        status="in_transit",
        cod_amount_vnd=480000,
        created_at=now - timedelta(hours=1),
    )
    shipment_failed_boom = Shipment(
        shipment_id=2,
        public_id=uuid.uuid4(),
        shipment_code="SHIP-002",
        order_id=3,
        status="failed",
        cod_amount_vnd=250000,
        created_at=now - timedelta(hours=2),
    )
    db.add_all([shipment_cod_transit, shipment_failed_boom])
    db.commit()

    yield db
    db.close()


def test_oltp_marketing_metrics_returns_cdc_signals(cdc_session):
    resp = _get_marketing_metrics_oltp(cdc_session)
    assert resp.role == "marketing"
    assert resp.voucher_burn_rate is not None
    assert resp.voucher_burn_rate.coupon_code == "SALE50K"
    assert resp.voucher_burn_rate.used_count == 850
    assert resp.voucher_burn_rate.budget_burn_percent == 85.0
    assert resp.voucher_burn_rate.budget_warning is True
    assert isinstance(resp.negative_review_spikes, list)


def test_oltp_inventory_metrics_returns_cdc_signals(cdc_session):
    resp = _get_inventory_metrics_oltp(cdc_session)
    assert resp.role == "inventory"
    assert isinstance(resp.depletion_velocity, list)
    assert isinstance(resp.critical_stockout_alerts, list)
    # Variant 2 has on_hand == 0
    stockout_skus = [s.sku for s in resp.critical_stockout_alerts]
    assert "POLO-BLK-L" in stockout_skus


def test_oltp_operations_metrics_returns_cdc_signals(cdc_session):
    resp = _get_operations_metrics_oltp(cdc_session)
    assert resp.role == "operations"
    assert isinstance(resp.regional_boom_rates, list)
    assert resp.fulfillment_bottleneck is not None
    assert resp.fulfillment_bottleneck.stale_unfulfilled_orders >= 1


def test_oltp_store_metrics_returns_cdc_signals(cdc_session):
    resp = _get_store_metrics_oltp(cdc_session, store_id=1)
    assert resp.role == "store"
    assert isinstance(resp.store_stockouts, list)
    # Store inventory for variant 1 has on_hand == 0
    assert len(resp.store_stockouts) >= 1
    assert resp.run_rate is not None
    assert resp.run_rate.daily_target_vnd == 15000000


def test_oltp_sales_metrics_returns_cdc_signals(cdc_session):
    resp = _get_sales_metrics_oltp(cdc_session)
    assert resp.role == "sales"
    assert isinstance(resp.viral_products, list)
    assert resp.channel_pace is not None


def test_oltp_executive_metrics_returns_cdc_signals(cdc_session):
    resp = _get_executive_metrics_oltp(cdc_session)
    assert resp.role == "executive"
    assert resp.margin_erosion is not None
    assert resp.cash_in_transit is not None
    assert resp.cash_in_transit.dispatched_shipments_count >= 1


def test_get_role_metrics_data_router_with_enriched_cdc_signals(cdc_session):
    from unittest.mock import MagicMock
    mock_trino = MagicMock()
    mock_trino.is_healthy.return_value = True
    mock_trino.execute_query.return_value = []
    for role in ["marketing", "inventory", "operations", "store", "sales", "executive"]:
        resp = get_role_metrics_data(target_role=role, store_id=1, db=cdc_session, trino_client=mock_trino)
        assert resp.role == role

