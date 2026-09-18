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


def test_refill_inventory_success():
    from app.modules.admin.schemas import RefillInventoryRequest
    mock_db = MagicMock()
    mock_store = MagicMock()
    mock_inv = MagicMock()
    mock_inv.on_hand = 100
    mock_inv.version = 1
    mock_store_inv = MagicMock()
    mock_store_inv.on_hand = 10

    mock_db.execute.return_value.scalar_one_or_none.side_effect = [mock_store, mock_inv, mock_store_inv]

    payload = RefillInventoryRequest(variant_id=1, store_id=7, quantity=20)

    from app.modules.admin.router import refill_inventory
    mock_admin = MagicMock(role="admin")
    mock_admin.store_id = None
    result = refill_inventory(payload, mock_admin, None, mock_db)
    assert result.status_code == 204
    assert mock_inv.on_hand == 80
    assert mock_store_inv.on_hand == 30


def test_refill_inventory_insufficient_stock():
    from app.modules.admin.schemas import RefillInventoryRequest
    mock_db = MagicMock()
    mock_inv = MagicMock()
    mock_inv.on_hand = 5

    mock_db.execute.return_value.scalar_one_or_none.return_value = mock_inv

    payload = RefillInventoryRequest(variant_id=1, store_id=7, quantity=20)

    from app.modules.admin.router import refill_inventory
    mock_admin = MagicMock(role="admin")
    try:
        refill_inventory(payload, mock_admin, None, mock_db)
        assert False, "Should have raised"
    except AppError as e:
        assert e.code == "OUT_OF_STOCK"


def test_refill_inventory_quantity_not_positive():
    from app.modules.admin.schemas import RefillInventoryRequest
    mock_db = MagicMock()

    for q in (0, -5):
        payload = RefillInventoryRequest(variant_id=1, store_id=7, quantity=q)

        from app.modules.admin.router import refill_inventory
        mock_admin = MagicMock(role="admin")
        try:
            refill_inventory(payload, mock_admin, None, mock_db)
            assert False, f"Should have raised for quantity={q}"
        except AppError as e:
            assert e.code == "VALIDATION_ERROR"
