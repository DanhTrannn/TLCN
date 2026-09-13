from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_cities_returns_200() -> None:
    response = client.get("/api/v1/locations/cities")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_stores_returns_200() -> None:
    response = client.get("/api/v1/locations/cities/HN/stores")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_stores_unknown_city_returns_404() -> None:
    response = client.get("/api/v1/locations/cities/NONEXISTENT/stores")
    assert response.status_code == 404


def test_availability_missing_city_code_returns_422() -> None:
    response = client.get("/api/v1/catalog/products/some-slug/availability")
    assert response.status_code == 422


def test_availability_unknown_product_returns_404() -> None:
    response = client.get(
        "/api/v1/catalog/products/nonexistent-slug/availability",
        params={"city_code": "HN"},
    )
    assert response.status_code == 404


def test_availability_unknown_city_returns_404() -> None:
    response = client.get(
        "/api/v1/catalog/products/some-slug/availability",
        params={"city_code": "NONEXISTENT"},
    )
    assert response.status_code == 404
