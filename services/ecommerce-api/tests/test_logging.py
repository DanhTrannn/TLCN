import json
import logging
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.requests import Request

from app.core.access_logging import action_for, build_access_event, normalize_search_query, should_emit_access_event
from app.core.logging_config import JsonLineFormatter
from app.core.middleware import RequestContextMiddleware


def _build_test_app() -> FastAPI:
    test_app = FastAPI()
    test_app.add_middleware(RequestContextMiddleware)

    @test_app.get("/health/ready")
    def ready() -> dict[str, str]:
        return {"status": "ok"}

    @test_app.get("/api/v1/products")
    def products() -> list[dict[str, int]]:
        return [{"id": 1}]

    return test_app


def test_json_line_formatter_keeps_only_safe_context() -> None:
    record = logging.LogRecord(
        name="ecommerce_api.access",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="request",
        args=(),
        exc_info=None,
    )
    record.request_id = "request-1"
    record.method = "GET"
    record.route = "/api/v1/products"
    record.status = 200
    record.latency_ms = 1.25
    record.email = "must-not-appear@example.com"

    payload = json.loads(JsonLineFormatter("ecommerce-api", "0.1.0").format(record))

    assert payload["service"] == "ecommerce-api"
    assert payload["request_id"] == "request-1"
    assert payload["status"] == 200
    assert "email" not in payload


def _request(
    path: str,
    route: str,
    *,
    method: str = "GET",
    query: str = "",
    path_params: dict[str, str] | None = None,
) -> Request:
    request = Request(
        {
            "type": "http",
            "http_version": "1.1",
            "method": method,
            "scheme": "http",
            "path": path,
            "raw_path": path.encode(),
            "query_string": query.encode(),
            "headers": [(b"user-agent", b"test-browser/1.0")],
            "client": ("127.0.0.1", 1234),
            "server": ("testserver", 80),
            "path_params": path_params or {},
            "route": SimpleNamespace(path=route),
        }
    )
    request.state.actor_type = "customer"
    request.state.actor_key = "customer-public-id"
    return request


def test_access_event_uses_route_template_and_allowlisted_catalog_context() -> None:
    request = _request(
        "/api/v1/products",
        "/api/v1/products",
        query=(
            "q=%C4%90%E1%BA%A7m%20%20Linen&category=dam&size=M&size=L&"
            "color=BLACK&min_price=100000&max_price=900000&in_stock=true&"
            "sort=price_asc&cursor=must-not-be-logged"
        ),
    )
    event = build_access_event(
        request,
        request_id="a" * 32,
        status_code=200,
        duration_ns=25_000_000,
        completed_at=datetime(2026, 8, 10, 3, 15, tzinfo=UTC),
    )

    assert event["schema"] == {"name": "ecommerce.access", "version": "1.0.0"}
    assert event["http"]["route"] == "/api/v1/products"
    assert event["event"]["duration_ns"] == 25_000_000
    assert event["actor"] == {"type": "customer", "key": "customer-public-id"}
    assert event["ecommerce"] == {
        "action": "catalog_search",
        "search_query": "đầm linen",
        "filters": {
            "category": "dam",
            "size": ["M", "L"],
            "color": ["BLACK"],
            "min_price_vnd": 100000,
            "max_price_vnd": 900000,
            "in_stock": True,
            "sort": "price_asc",
        },
    }
    assert "cursor" not in json.dumps(event)
    assert "127.0.0.1" not in json.dumps(event)


def test_access_event_never_keeps_raw_dynamic_path() -> None:
    request = _request(
        "/api/v1/orders/OD-PRIVATE-123",
        "/api/v1/orders/{order_number}",
        path_params={"order_number": "OD-PRIVATE-123"},
    )
    event = build_access_event(
        request,
        request_id="b" * 32,
        status_code=404,
        duration_ns=1,
        completed_at=datetime(2026, 8, 10, 3, 15, tzinfo=UTC),
    )

    encoded = json.dumps(event)
    assert event["http"]["route"] == "/api/v1/orders/{order_number}"
    assert event["severity_text"] == "WARN"
    assert "OD-PRIVATE-123" not in encoded


def test_search_query_with_pii_is_redacted() -> None:
    assert normalize_search_query(" customer@example.com ") == (None, True)
    assert normalize_search_query("token=eyJabcdefgh.abcdefgh") == (None, True)
    assert normalize_search_query("12 đường Nguyễn Huệ") == (None, True)
    assert normalize_search_query("  Đầm   Linen  ") == ("đầm linen", False)


def test_formatter_emits_access_event_without_wrapper() -> None:
    access_event = {"schema": {"name": "ecommerce.access", "version": "1.0.0"}}
    record = logging.LogRecord(
        name="ecommerce_api.access",
        level=logging.INFO,
        pathname=__file__,
        lineno=100,
        msg="http.server.request",
        args=(),
        exc_info=None,
    )
    record.access_event = access_event

    payload = json.loads(JsonLineFormatter("ecommerce-api", "0.1.0").format(record))

    assert payload == access_event
