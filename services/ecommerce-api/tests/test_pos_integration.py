from unittest.mock import MagicMock, patch

from app.modules.checkout.allocation import (
    parse_city_from_address,
    find_store_with_all_items,
    allocate_order_to_stores,
)


def test_parse_city_from_address():
    assert parse_city_from_address("123 Nguyễn Huệ, Bến Nghé, Thành phố Hồ Chí Minh") == "Hồ Chí Minh"
    assert parse_city_from_address("456 Lê Lợi, Quận 1, TP. Hà Nội") == "Hà Nội"
    assert parse_city_from_address("abc") is None


def test_allocate_order_store_found():
    mock_db = MagicMock()
    mock_store = MagicMock(store_id=7)

    mock_result = MagicMock()
    mock_result.rowcount = 1
    mock_db.execute.return_value = mock_result

    with patch("app.modules.checkout.allocation.find_stores_in_city", return_value=[mock_store]):
        with patch("app.modules.checkout.allocation.find_store_with_all_items", return_value=mock_store):
            with patch("app.modules.checkout.allocation.deduct_store_inventory"):
                result = allocate_order_to_stores(
                    mock_db,
                    order_id=1,
                    shipping_address="123 Nguyễn Huệ, Bến Nghé, Thành phố Hồ Chí Minh",
                    items=[{"variant_id": 10, "quantity": 2}],
                )
                assert result["store_id"] == 7
                assert result["source"] == "store"


def test_allocate_order_fallback_global():
    mock_db = MagicMock()

    with patch("app.modules.checkout.allocation.find_stores_in_city", return_value=[MagicMock()]):
        with patch("app.modules.checkout.allocation.find_store_with_all_items", return_value=None):
            result = allocate_order_to_stores(
                mock_db,
                order_id=1,
                shipping_address="123 Nguyễn Huệ, Bến Nghé, Thành phố Hồ Chí Minh",
                items=[{"variant_id": 10, "quantity": 2}],
            )
            assert result["store_id"] is None
            assert result["source"] == "global"


def test_allocate_order_no_city():
    mock_db = MagicMock()
    result = allocate_order_to_stores(mock_db, order_id=1, shipping_address="abc", items=[])
    assert result["source"] == "global"
