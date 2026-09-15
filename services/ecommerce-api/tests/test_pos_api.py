from unittest.mock import patch

from app.main import app
from app.db.deps import get_current_customer


def test_search_products_requires_auth(client):
    response = client.get("/api/v1/pos/products?store_id=1&search=APN")
    assert response.status_code == 401


def test_search_products_success(client, mock_staff_auth):
    with patch("app.modules.pos.router.search_products") as mock_search:
        mock_search.return_value = [
            {
                "variant_id": 1,
                "product_name": "Áo Polo Nam",
                "sku": "APN001",
                "size_code": "L",
                "color_code": "DEN",
                "price_vnd": 300000,
                "store_stock": 5,
                "global_stock": 20,
            }
        ]
        response = client.get(
            "/api/v1/pos/products?store_id=1&search=APN",
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["sku"] == "APN001"


def test_create_transaction_success(client, mock_staff_auth):
    with patch("app.modules.pos.router.create_pos_transaction") as mock_create:
        mock_create.return_value = {
            "order_number": "POS-001",
            "status": "completed",
            "channel": "pos",
            "store_id": 1,
            "payment_method": "cash",
            "items": [],
            "subtotal_vnd": 300000,
            "total_vnd": 300000,
            "created_at": "2026-09-15T10:00:00",
        }
        response = client.post(
            "/api/v1/pos/transactions",
            json={
                "store_id": 1,
                "items": [{"variant_id": 1, "quantity": 1}],
                "payment_method": "cash",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["channel"] == "pos"
        assert data["order_number"] == "POS-001"


def test_create_transaction_requires_auth(client):
    response = client.post(
        "/api/v1/pos/transactions",
        json={
            "store_id": 1,
            "items": [{"variant_id": 1, "quantity": 1}],
            "payment_method": "cash",
        },
    )
    assert response.status_code == 401
