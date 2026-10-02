from unittest.mock import MagicMock
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.sql.elements import TextClause

from app.db.base import Base
from app.core.ids import uuid7
import app.models  # noqa: F401
from app.models.customer import Customer
from app.models.order import Order
from app.models.cart import Cart, CartItem
from app.modules.analytics.service import get_marketing_metrics, _get_marketing_metrics_oltp
from app.modules.analytics.trino_client import TrinoClient


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


def test_marketing_metrics_streaming_fallback_to_mart():
    """Verify fallback to mart_marketing_funnel_daily when fact_web_events is empty."""
    mock_trino = MagicMock(spec=TrinoClient)
    mock_trino.is_healthy.return_value = True
    mock_trino.execute_query.side_effect = [
        # fact_web_events returns 0
        [{
            "visitors_count": 0,
            "add_to_cart_count": 0,
            "checkouts_count": 0,
            "purchases_count": 0,
        }],
        # mart_marketing_funnel_daily returns daily rolled-up mart
        [{
            "visitors_count": 500,
            "add_to_cart_count": 150,
            "checkouts_count": 75,
            "purchases_count": 30,
        }],
    ]

    res = get_marketing_metrics(trino_client=mock_trino)

    assert res.total_visitors == 500
    assert res.total_purchases == 30
    assert res.conversion_rate_percent == 6.0


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
