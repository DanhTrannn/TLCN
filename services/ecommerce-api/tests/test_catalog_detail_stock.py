from types import SimpleNamespace
from uuid import uuid4

from app.modules.catalog.service import get_product_detail


class Result:
    def __init__(self, *, first_value=None, rows=None):
        self._first_value = first_value
        self._rows = rows or []

    def first(self):
        return self._first_value

    def all(self):
        return self._rows


class Session:
    def __init__(self, results):
        self._results = iter(results)

    def execute(self, _statement):
        return next(self._results)


def test_product_detail_exposes_stock_quantity_per_variant() -> None:
    product = SimpleNamespace(
        public_id=uuid4(),
        product_id=10,
        slug="ao-so-mi-linen",
        name="Áo sơ mi linen",
        description="Thiết kế nhẹ và thoáng.",
        image_url="https://example.test/linen.jpg",
    )
    available_variant = SimpleNamespace(
        public_id=uuid4(),
        sku="LINEN-M-TRANG",
        size_code="M",
        color_code="Trắng",
        price_vnd=349_000,
    )
    sold_out_variant = SimpleNamespace(
        public_id=uuid4(),
        sku="LINEN-L-TRANG",
        size_code="L",
        color_code="Trắng",
        price_vnd=349_000,
    )
    session = Session(
        [
            Result(first_value=(product, "ao-nu", "Áo nữ")),
            Result(rows=[(available_variant, 12), (sold_out_variant, 0)]),
        ]
    )

    response = get_product_detail(session, "ao-so-mi-linen")

    assert response.variants[0].stock_quantity == 12
    assert response.variants[0].in_stock is True
    assert response.variants[1].stock_quantity == 0
    assert response.variants[1].in_stock is False
