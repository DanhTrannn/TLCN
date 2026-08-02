from datetime import datetime
from types import SimpleNamespace
from uuid import uuid4

from app.modules.orders.service import get_order_detail


class Result:
    def __init__(self, value=None, rows=None):
        self._value = value
        self._rows = rows or []

    def scalar_one_or_none(self):
        return self._value

    def scalars(self):
        return self

    def all(self):
        return self._rows


class Session:
    def __init__(self, results):
        self._results = iter(results)

    def execute(self, _statement):
        return next(self._results)


def test_order_detail_includes_current_product_image() -> None:
    created_at = datetime(2026, 8, 2, 3, 30)
    order = SimpleNamespace(
        order_id=20,
        customer_id=99,
        order_number="ORD-20260802-0001",
        status="paid",
        currency_code="VND",
        subtotal_vnd=349_000,
        coupon_code_snapshot=None,
        discount_amount_vnd=0,
        shipping_fee_vnd=30_000,
        total_vnd=379_000,
        receiver_name="Nguyễn An",
        receiver_phone="0900000000",
        shipping_address_text="Quận 1, TP. Hồ Chí Minh",
        created_at=created_at,
        paid_at=created_at,
        confirmed_at=None,
        completed_at=None,
        cancelled_at=None,
    )
    item = SimpleNamespace(
        order_item_id=30,
        public_id=uuid4(),
        product_public_id_snapshot=uuid4(),
        product_name_snapshot="Áo sơ mi linen",
        sku_snapshot="LINEN-M-TRANG",
        size_code_snapshot="M",
        color_code_snapshot="Trắng",
        unit_price_vnd=349_000,
        quantity=1,
        line_total_vnd=349_000,
    )
    image_url = "https://example.test/linen.jpg"
    session = Session(
        [
            Result(value=order),
            Result(rows=[(item, image_url)]),
            Result(rows=[]),
            Result(value=None),
            Result(rows=[]),
        ]
    )

    response = get_order_detail(session, customer_id=99, order_number=order.order_number)

    assert response.items[0].image_url == image_url
    assert response.items[0].product_name == "Áo sơ mi linen"
    assert response.items[0].sku == "LINEN-M-TRANG"
