from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.db.deps import get_db
from app.main import app


def _override_db(mock_db):
    app.dependency_overrides[get_db] = lambda: mock_db


def _reset_db():
    app.dependency_overrides.clear()


def test_cities_returns_200() -> None:
    mock_db = MagicMock()
    mock_db.execute.return_value.fetchall.return_value = []
    _override_db(mock_db)
    try:
        client = TestClient(app)
        response = client.get("/api/v1/locations/cities")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    finally:
        _reset_db()


def test_stores_unknown_city_returns_404() -> None:
    mock_db = MagicMock()
    mock_db.execute.return_value.scalar_one_or_none.return_value = None
    _override_db(mock_db)
    try:
        client = TestClient(app)
        response = client.get("/api/v1/locations/cities/NONEXISTENT/stores")
        assert response.status_code == 404
    finally:
        _reset_db()


def test_availability_missing_city_code_returns_422() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/catalog/products/some-slug/availability")
    assert response.status_code == 422


def test_availability_unknown_product_returns_404() -> None:
    mock_db = MagicMock()
    mock_db.execute.return_value.scalar_one_or_none.return_value = None
    _override_db(mock_db)
    try:
        client = TestClient(app)
        response = client.get(
            "/api/v1/catalog/products/nonexistent-slug/availability",
            params={"city_code": "HN"},
        )
        assert response.status_code == 404
    finally:
        _reset_db()


def test_availability_unknown_city_returns_404() -> None:
    mock_db = MagicMock()
    mock_db.execute.return_value.scalar_one_or_none.return_value = None
    _override_db(mock_db)
    try:
        client = TestClient(app)
        response = client.get(
            "/api/v1/catalog/products/some-slug/availability",
            params={"city_code": "NONEXISTENT"},
        )
        assert response.status_code == 404
    finally:
        _reset_db()
