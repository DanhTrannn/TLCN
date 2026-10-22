from unittest.mock import MagicMock

import app.models  # noqa: F401
import pytest
from app.core.ids import uuid7
from app.db.base import Base
from app.models.customer import Customer
from app.models.order import Order
from app.modules.analytics.service import (
    _get_marketing_metrics_oltp,
    get_marketing_metrics,
    get_role_metrics_data,
    get_sales_trend,
)
from app.modules.analytics.trino_client import TrinoClient
from sqlalchemy import create_engine, event
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session, sessionmaker
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
def in_memory_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def connect(dbapi_connection, connection_record):
        dbapi_connection.create_function("char_length", 1, lambda s: len(s) if s is not None else 0)

    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


def test_marketing_metrics_streaming_fact_web_events():
    """Verify get_marketing_metrics prioritizes real-time fact_web_events streaming table."""
    mock_trino = MagicMock(spec=TrinoClient)
    mock_trino.is_healthy.return_value = True
    mock_trino.execute_query.side_effect = [
        # Query on lakehouse.gold.fact_web_events
        [{
            "visitors_count": 250,
            "add_to_cart_count": 50,
            "checkouts_count": 25,
            "purchases_count": 10,
        }]
    ]

    res = get_marketing_metrics(trino_client=mock_trino)

    assert res.role == "marketing"
    assert res.total_visitors == 250
    assert res.total_purchases == 10
    assert res.conversion_rate_percent == 4.0
    assert len(res.funnel_steps) == 4

    steps = {s.step_name: (s.count, s.conversion_rate_percent) for s in res.funnel_steps}
    assert steps["Lượt xem sản phẩm (Product Views)"] == (250, 100.0)
    assert steps["Thêm vào giỏ (Add to Cart)"] == (50, 20.0)
    assert steps["Tiến hành thanh toán (Checkout)"] == (25, 10.0)
    assert steps["Đặt hàng thành công (Purchased)"] == (10, 4.0)

    # Verify query contained fact_web_events
    called_sql = mock_trino.execute_query.call_args[0][0]
    assert "lakehouse.gold.fact_web_events" in called_sql
    assert "ecommerce_action IN ('product_detail', 'catalog_search')" in called_sql


def test_marketing_metrics_empty_stream_uses_marked_oltp_fallback(in_memory_db: Session):
    """An empty stream must not be replaced by an all-time mart presented as 30-day data."""
    customer = Customer(
        customer_id=902,
        public_id=uuid7(),
        display_name="Fallback Tester",
        role="customer",
        status="active",
    )
    in_memory_db.add(customer)
    in_memory_db.commit()

    mock_trino = MagicMock(spec=TrinoClient)
    mock_trino.is_healthy.return_value = True
    mock_trino.execute_query.return_value = [{
        "visitors_count": 0,
        "add_to_cart_count": 0,
        "checkouts_count": 0,
        "purchases_count": 0,
    }]

    res = get_marketing_metrics(db=in_memory_db, trino_client=mock_trino)

    assert mock_trino.execute_query.call_count == 1
    assert res.data_source == "oltp_fallback"
    assert res.is_degraded is True
    assert res.total_visitors == 1
    assert res.total_purchases == 0
    assert res.funnel_window_days == 30


def test_get_marketing_metrics_oltp_no_fake_multiplier(in_memory_db: Session):
    """Verify OLTP fallback never multiplies add_to_cart by 3 and never injects fake 100."""
    customer = Customer(
        customer_id=901,
        public_id=uuid7(),
        display_name="Marketing Tester",
        role="customer",
        status="active",
    )
    in_memory_db.add(customer)
    in_memory_db.commit()

    res = _get_marketing_metrics_oltp(in_memory_db)

    # With 1 customer and 0 orders, visitors must be 1 (NOT 100, and NOT * 3)
    assert res.total_visitors == 1
    assert res.total_purchases == 0
    assert res.conversion_rate_percent == 0.0

    steps = {s.step_name: s.count for s in res.funnel_steps}
    assert steps["Lượt xem sản phẩm (Product Views)"] == 1
    assert steps["Thêm vào giỏ (Add to Cart)"] == 0
    assert steps["Tiến hành thanh toán (Checkout)"] == 0
    assert steps["Đặt hàng thành công (Purchased)"] == 0


def test_get_metrics_fails_fast_when_trino_unhealthy(in_memory_db: Session):
    """Verify get_executive_metrics throws error directly when Trino is offline, no OLTP fallback."""
    from app.core.errors import AppError
    from app.modules.analytics.service import get_executive_metrics, get_sales_metrics

    mock_trino = MagicMock(spec=TrinoClient)
    mock_trino.is_healthy.return_value = False
    mock_trino.base_url = "http://trino:8080"

    with pytest.raises(AppError) as exc_info:
        get_executive_metrics(db=in_memory_db, trino_client=mock_trino)

    assert "Không thể kết nối đến Trino DWH Coordinator" in str(exc_info.value.message)

    with pytest.raises(AppError) as exc_info_sales:
        get_sales_metrics(db=in_memory_db, trino_client=mock_trino)

    assert "Không thể kết nối đến Trino DWH Coordinator" in str(exc_info_sales.value.message)


def test_get_metrics_fails_fast_when_trino_query_fails(in_memory_db: Session):
    """Verify get_executive_metrics directly surfaces the exact Trino query error without fallback."""
    from app.core.errors import AppError
    from app.modules.analytics.service import get_executive_metrics

    mock_trino = MagicMock(spec=TrinoClient)
    mock_trino.is_healthy.return_value = True
    mock_trino.execute_query.side_effect = RuntimeError("Trino Query Error: Table 'lakehouse.gold.mart_sales_daily' not found")

    with pytest.raises(AppError) as exc_info:
        get_executive_metrics(db=in_memory_db, trino_client=mock_trino)

    assert "Lỗi truy vấn Trino DWH (Executive)" in str(exc_info.value.message)
    assert "Table 'lakehouse.gold.mart_sales_daily' not found" in str(exc_info.value.message)


def test_role_metrics_returns_explicit_oltp_degraded_mode(in_memory_db: Session):
    mock_trino = MagicMock(spec=TrinoClient)
    mock_trino.is_healthy.return_value = False
    mock_trino.base_url = "http://trino:8080"

    result = get_role_metrics_data(
        target_role="marketing",
        db=in_memory_db,
        trino_client=mock_trino,
    )

    assert result.role == "marketing"
    assert result.data_source == "oltp_fallback"
    assert result.is_degraded is True
    assert result.degraded_reason


def test_sales_trend_returns_explicit_oltp_degraded_mode(in_memory_db: Session):
    mock_trino = MagicMock(spec=TrinoClient)
    mock_trino.is_healthy.return_value = False
    mock_trino.base_url = "http://trino:8080"

    result = get_sales_trend(days=7, db=in_memory_db, trino_client=mock_trino)

    assert result.days == 7
    assert result.data_source == "oltp_fallback"
    assert result.is_degraded is True
    assert len(result.points) == 8


def test_marketing_funnel_uses_30_day_window():
    mock_trino = MagicMock(spec=TrinoClient)
    mock_trino.is_healthy.return_value = True
    mock_trino.execute_query.return_value = [{
        "visitors_count": 100,
        "add_to_cart_count": 20,
        "checkouts_count": 10,
        "purchases_count": 5,
    }]

    res = get_marketing_metrics(trino_client=mock_trino)

    called_sql = mock_trino.execute_query.call_args[0][0]
    assert "event_date >= current_date - INTERVAL '29' DAY" in called_sql
    assert res.funnel_window_days == 30


def test_marketing_metrics_marks_oltp_fallback_when_stream_empty(in_memory_db: Session):
    mock_trino = MagicMock(spec=TrinoClient)
    mock_trino.is_healthy.return_value = True
    mock_trino.execute_query.side_effect = [
        [{
            "visitors_count": 0,
            "add_to_cart_count": 0,
            "checkouts_count": 0,
            "purchases_count": 0,
        }],
        RuntimeError("Table 'lakehouse.gold.mart_marketing_funnel_daily' not found"),
    ]

    res = get_marketing_metrics(db=in_memory_db, trino_client=mock_trino)

    assert res.data_source == "oltp_fallback"
    assert res.is_degraded is True
    assert res.degraded_reason
    assert res.funnel_window_days == 30


def test_marketing_oltp_fallback_only_counts_last_30_days(in_memory_db: Session):
    from datetime import UTC, datetime, timedelta

    now = datetime.now(UTC).replace(tzinfo=None)
    old_customer = Customer(
        customer_id=903,
        public_id=uuid7(),
        display_name="Khách Cũ",
        role="customer",
        status="active",
        created_at=now - timedelta(days=40),
    )
    recent_customer = Customer(
        customer_id=904,
        public_id=uuid7(),
        display_name="Khách Mới",
        role="customer",
        status="active",
        created_at=now - timedelta(days=1),
    )
    in_memory_db.add_all([old_customer, recent_customer])
    in_memory_db.flush()

    for order_id, customer_id, created_at in (
        (201, 903, now - timedelta(days=40)),
        (202, 904, now - timedelta(days=1)),
    ):
        in_memory_db.add(
            Order(
                order_id=order_id,
                order_number=f"ORD-MKT-{order_id}",
                customer_id=customer_id,
                checkout_idempotency_key=f"chk-{uuid7()}",
                status="completed",
                subtotal_vnd=100000,
                discount_amount_vnd=0,
                shipping_fee_vnd=0,
                total_vnd=100000,
                receiver_name="Khách Marketing",
                receiver_phone="0901234567",
                shipping_address_text="Test",
                created_at=created_at,
            )
        )
    in_memory_db.commit()

    res = _get_marketing_metrics_oltp(in_memory_db)

    assert res.total_visitors == 1
    assert res.total_purchases == 1
    assert res.funnel_window_days == 30

