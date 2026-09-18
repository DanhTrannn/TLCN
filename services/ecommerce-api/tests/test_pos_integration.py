from unittest.mock import MagicMock

from app.modules.checkout.allocation import parse_city_from_address, deduct_inventory
from app.core.errors import AppError


def test_parse_city_from_address():
    assert parse_city_from_address("123 Nguyễn Huệ, Bến Nghé, Thành phố Hồ Chí Minh") == "Hồ Chí Minh"
    assert parse_city_from_address("456 Lê Lợi, Quận 1, TP. Hà Nội") == "Hà Nội"
    assert parse_city_from_address("abc") is None


def test_deduct_inventory_success():
    mock_db = MagicMock()
    mock_inv = MagicMock()
    mock_inv.on_hand = 100
    mock_inv.version = 1
    mock_db.execute.return_value.scalar_one_or_none.return_value = mock_inv

    deduct_inventory(mock_db, [{"variant_id": 1, "quantity": 5}])
    assert mock_inv.on_hand == 95
    assert mock_inv.version == 2


def test_deduct_inventory_insufficient():
    mock_db = MagicMock()
    mock_inv = MagicMock()
    mock_inv.on_hand = 2
    mock_db.execute.return_value.scalar_one_or_none.return_value = mock_inv

    try:
        deduct_inventory(mock_db, [{"variant_id": 1, "quantity": 5}])
        assert False, "Should have raised"
    except AppError as e:
        assert e.code == "OUT_OF_STOCK"
