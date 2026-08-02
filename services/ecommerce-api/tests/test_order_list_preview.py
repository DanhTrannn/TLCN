from datetime import datetime
from types import SimpleNamespace

from app.modules.orders.service import list_orders


class Result:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


class Session:
    def __init__(self, results):
        self._results = iter(results)
        self.execute_count = 0

    def execute(self, _statement):
        self.execute_count += 1
        return Result(next(self._results))


def order(order_id: int, order_number: str):
    return SimpleNamespace(
        order_id=order_id,
        order_number=order_number,
        status="paid",
        total_vnd=500_000,
        created_at=datetime(2026, 8, 2, 10, order_id),
    )


def preview(order_id: int, name: str):
    return SimpleNamespace(
        order_id=order_id,
        product_name=name,
        image_url=f"https://example.test/{order_id}.jpg",
        sku=f"SKU-{order_id}",
        size_code="M",
        color_code="Đen",
        quantity=1,
        line_total_vnd=250_000,
    )


def test_order_list_loads_all_previews_in_one_batch_query() -> None:
    orders = [(order(1, "ORD-1"), 4), (order(2, "ORD-2"), 1)]
    preview_rows = [preview(1, "Áo linen"), preview(1, "Chân váy"), preview(2, "Đầm midi")]
    session = Session([orders, preview_rows])

    response = list_orders(session, customer_id=99, cursor=None)

    assert session.execute_count == 2
    assert [item.order_number for item in response.items] == ["ORD-1", "ORD-2"]
    assert [item.product_name for item in response.items[0].preview_items] == ["Áo linen", "Chân váy"]
    assert response.items[0].item_count == 4
    assert response.items[1].preview_items[0].image_url == "https://example.test/2.jpg"


def test_empty_order_page_does_not_run_preview_query() -> None:
    session = Session([[]])

    response = list_orders(session, customer_id=99, cursor=None)

    assert session.execute_count == 1
    assert response.items == []
