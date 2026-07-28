import json
import logging

from app.core.logging_config import JsonLineFormatter


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
