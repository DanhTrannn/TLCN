from fastapi.testclient import TestClient

from app.main import app


def test_liveness() -> None:
    response = TestClient(app).get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}



def test_admin_requires_authentication() -> None:
    response = TestClient(app).get("/api/v1/admin/overview")
    assert response.status_code == 401


def test_logout_requires_csrf_token() -> None:
    response = TestClient(app).post("/api/v1/auth/logout")
    assert response.status_code == 403
