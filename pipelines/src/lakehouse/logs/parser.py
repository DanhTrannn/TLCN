"""Parse access events independently of Kafka/Flink; all stored timestamps use UTC."""

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone


class InvalidAccessEvent(ValueError):
    """An event cannot be safely projected into the typed streaming tables."""


def _timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp must contain an explicit timezone")
    return parsed.astimezone(timezone.utc)


@dataclass(frozen=True)
class ParsedAccessEvent:
    event_id: str
    event_ts: str
    ingest_ts: str
    event_date: str
    observed_timestamp: str
    schema_name: str
    schema_version: str
    service_name: str
    service_version: str
    service_env: str
    service_instance_id: str
    severity_number: int
    severity_text: str
    trace_id: str
    span_id: str
    event_name: str
    event_category: str
    event_kind: str
    event_outcome: str
    duration_ns: int
    duration_ms: float
    http_method: str
    http_route: str
    http_status: int
    is_success: bool
    is_client_error: bool
    is_server_error: bool
    is_slow_request: bool
    actor_type: str
    actor_key: str
    client_user_agent: str
    action: str
    product_key: str
    variant_key: str
    search_query: str
    search_redacted: bool
    error_code: str
    error_type: str
    data_origin: str
    raw_payload: str


def parse_access_event(raw: str) -> ParsedAccessEvent:
    try:
        msg = json.loads(raw)
        if not isinstance(msg, dict):
            raise InvalidAccessEvent("event must be an object")
        for key in ("request", "http", "event"):
            if not isinstance(msg.get(key), dict):
                raise InvalidAccessEvent(f"{key} must be an object")
        for key in ("service", "actor", "client", "ecommerce", "error", "schema"):
            if key in msg and not isinstance(msg[key], dict):
                raise InvalidAccessEvent(f"{key} must be an object")
        if not re.fullmatch(r"[0-9a-f]{32}", str(msg["request"].get("id", ""))):
            raise InvalidAccessEvent("invalid request identity")
        if not isinstance(msg.get("timestamp"), str):
            raise InvalidAccessEvent("timestamp is required")
        status = msg["http"].get("status_code")
        if isinstance(status, bool) or not isinstance(status, int) or not 100 <= status <= 599:
            raise InvalidAccessEvent("invalid HTTP status")
        duration = msg["event"].get("duration_ns", 0)
        if isinstance(duration, bool) or not isinstance(duration, int) or not 0 <= duration <= 2**63 - 1:
            raise InvalidAccessEvent("invalid request duration")
        return _project(msg, raw)
    except (ValueError, TypeError, KeyError, AttributeError, OverflowError) as exc:
        raise InvalidAccessEvent(str(exc)) from exc


def _project(msg: dict, raw: str) -> ParsedAccessEvent:
    now_dt = datetime.now(timezone.utc)
    now_ts_str = now_dt.strftime("%Y-%m-%d %H:%M:%S.%f")

    # Parse event timestamp in Asia/Ho_Chi_Minh
    ts_str: str = msg.get("timestamp") or ""
    try:
        event_dt = _timestamp(ts_str)
    except ValueError as exc:
        raise InvalidAccessEvent("invalid timestamp") from exc
    event_ts_str = event_dt.strftime("%Y-%m-%d %H:%M:%S.%f")
    event_date_str = event_dt.strftime("%Y-%m-%d")

    # Observed timestamp in container
    obs_str: str = msg.get("observed_timestamp") or ts_str
    try:
        obs_dt = _timestamp(obs_str)
    except ValueError as exc:
        raise InvalidAccessEvent("invalid observed_timestamp") from exc
    obs_ts_str = obs_dt.strftime("%Y-%m-%d %H:%M:%S.%f")

    # Nested objects with safe defaults
    request = msg.get("request") or {}
    service = msg.get("service") or {}
    http = msg.get("http") or {}
    event = msg.get("event") or {}
    actor = msg.get("actor") or {}
    client = msg.get("client") or {}
    ecommerce = msg.get("ecommerce") or {}
    error = msg.get("error") or {}
    schema = msg.get("schema") or {}

    event_id: str = request["id"]
    schema_name: str = schema.get("name") or "ecommerce.access"
    schema_version: str = schema.get("version") or "1.0.0"
    service_name: str = service.get("name") or "ecommerce-api"
    service_version: str = service.get("version") or "0.1.0"
    service_env: str = service.get("environment") or "production"
    service_instance_id: str = service.get("instance_id") or service_name
    severity_number: int = int(msg.get("severity_number") or 9)
    severity_text: str = msg.get("severity_text") or "INFO"
    trace_id: str = msg.get("trace_id") or ""
    span_id: str = msg.get("span_id") or ""
    event_name: str = event.get("name") or "http.server.request"
    event_category: str = event.get("category") or "web"
    event_kind: str = event.get("kind") or "event"
    event_outcome: str = event.get("outcome") or "success"
    duration_ns: int = int(event.get("duration_ns") or 0)
    duration_ms: float = round(duration_ns / 1_000_000.0, 3)

    http_method: str = (http.get("request_method") or "UNKNOWN").upper()
    http_route: str = http.get("route") or "UNKNOWN"
    http_status: int = int(http.get("status_code") or 200)
    is_success: bool = http_status < 400
    is_client_error: bool = (http_status >= 400) and (http_status < 500)
    is_server_error: bool = http_status >= 500
    is_slow_request: bool = duration_ms >= 1000.0

    actor_type: str = actor.get("type") or "anonymous"
    actor_key: str = actor.get("key") or ""
    client_user_agent: str = client.get("user_agent") or ""
    action: str = ecommerce.get("action") or "unknown"
    product_key: str = ecommerce.get("product_key") or ""
    variant_key: str = ecommerce.get("variant_key") or ""
    search_query: str = ecommerce.get("search_query") or ""
    search_redacted: bool = bool(ecommerce.get("search_redacted") or False)

    error_code: str = error.get("code") or ""
    error_type: str = error.get("type") or ""
    data_origin: str = msg.get("data_origin") or "observed"
    return ParsedAccessEvent(
        event_id,
        event_ts_str,
        now_ts_str,
        event_date_str,
        obs_ts_str,
        schema_name,
        schema_version,
        service_name,
        service_version,
        service_env,
        service_instance_id,
        severity_number,
        severity_text,
        trace_id,
        span_id,
        event_name,
        event_category,
        event_kind,
        event_outcome,
        duration_ns,
        duration_ms,
        http_method,
        http_route,
        http_status,
        is_success,
        is_client_error,
        is_server_error,
        is_slow_request,
        actor_type,
        actor_key,
        client_user_agent,
        action,
        product_key,
        variant_key,
        search_query,
        search_redacted,
        error_code,
        error_type,
        data_origin,
        raw,
    )
