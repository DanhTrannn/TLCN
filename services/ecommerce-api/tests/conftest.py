import os

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("API_SECRET_KEY", "test-secret-key-least-32-characters-long")
os.environ.setdefault("API_INTERNAL_SECRET", "test-internal-secret")

from app.main import app  # noqa: E402
from app.db.deps import get_db, get_current_customer  # noqa: E402


@pytest.fixture()
def client():
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def mock_staff_auth(client):
    mock_customer = MagicMock()
    mock_customer.customer_id = 1
    mock_customer.public_id = "staff-public-id"
    mock_customer.role = "store_manager"
    mock_customer.status = "active"
    app.dependency_overrides[get_current_customer] = lambda: mock_customer
    yield client
    app.dependency_overrides.clear()


@pytest.fixture()
def admin_token_headers():
    mock_admin = MagicMock()
    mock_admin.customer_id = 1
    mock_admin.public_id = "admin-public-id"
    mock_admin.role = "admin"
    mock_admin.status = "active"
    from app.db.deps import get_current_admin, verify_csrf
    app.dependency_overrides[get_current_admin] = lambda: mock_admin
    app.dependency_overrides[get_current_customer] = lambda: mock_admin
    app.dependency_overrides[verify_csrf] = lambda: None
    yield {"Authorization": "Bearer mock-admin-token"}
    app.dependency_overrides.pop(get_current_admin, None)
    app.dependency_overrides.pop(get_current_customer, None)
    app.dependency_overrides.pop(verify_csrf, None)


from unittest.mock import MagicMock  # noqa: E402

