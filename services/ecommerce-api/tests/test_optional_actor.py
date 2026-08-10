from types import SimpleNamespace

from starlette.requests import Request

from app.core.config import get_settings
from app.core.security import create_access_token
from app.db.deps import get_optional_customer


class _ScalarResult:
    def __init__(self, customer: SimpleNamespace | None) -> None:
        self.customer = customer

    def scalar_one_or_none(self) -> SimpleNamespace | None:
        return self.customer


class _Session:
    def __init__(self, customer: SimpleNamespace | None) -> None:
        self.customer = customer
        self.execute_calls = 0

    def execute(self, _statement: object) -> _ScalarResult:
        self.execute_calls += 1
        return _ScalarResult(self.customer)


def _request(token: str | None = None) -> Request:
    headers: list[tuple[bytes, bytes]] = []
    if token is not None:
        cookie_name = get_settings().auth_cookie_name
        headers.append((b"cookie", f"{cookie_name}={token}".encode()))
    return Request(
        {
            "type": "http",
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": "/api/v1/catalog/facets",
            "raw_path": b"/api/v1/catalog/facets",
            "query_string": b"",
            "headers": headers,
            "client": ("127.0.0.1", 1234),
            "server": ("testserver", 80),
        }
    )


def test_optional_actor_enriches_valid_authenticated_customer() -> None:
    customer = SimpleNamespace(
        public_id="018f5d4d-347a-7abc-8abc-0123456789ab",
        role="customer",
        status="active",
    )
    session = _Session(customer)
    request = _request(create_access_token(customer.public_id))

    resolved = get_optional_customer(request, session)  # type: ignore[arg-type]

    assert resolved is customer
    assert session.execute_calls == 1
    assert request.state.actor_type == "customer"
    assert request.state.actor_key == customer.public_id


def test_optional_actor_keeps_public_request_anonymous_without_cookie() -> None:
    session = _Session(None)
    request = _request()
    request.state.actor_type = "anonymous"
    request.state.actor_key = None

    resolved = get_optional_customer(request, session)  # type: ignore[arg-type]

    assert resolved is None
    assert session.execute_calls == 0
    assert request.state.actor_type == "anonymous"
    assert request.state.actor_key is None


def test_optional_actor_rejects_invalid_or_inactive_identity_silently() -> None:
    invalid_session = _Session(None)
    invalid_request = _request("not-a-jwt")
    assert get_optional_customer(invalid_request, invalid_session) is None  # type: ignore[arg-type]
    assert invalid_session.execute_calls == 0

    inactive_customer = SimpleNamespace(
        public_id="018f5d4d-347a-7abc-8abc-0123456789ab",
        role="customer",
        status="inactive",
    )
    inactive_session = _Session(inactive_customer)
    inactive_request = _request(create_access_token(inactive_customer.public_id))
    assert get_optional_customer(inactive_request, inactive_session) is None  # type: ignore[arg-type]
    assert inactive_session.execute_calls == 1
