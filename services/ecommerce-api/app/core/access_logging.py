import os
import re
import unicodedata
from datetime import UTC, datetime
from typing import Any

from starlette.requests import Request

from app.core.config import get_settings


ACCESS_LOG_SCHEMA_NAME = "ecommerce.access"
ACCESS_LOG_SCHEMA_VERSION = "1.0.0"

_MAX_USER_AGENT_LENGTH = 512
_MAX_SEARCH_LENGTH = 100
_MAX_FILTER_VALUES = 10
_CONTROL_CHARACTERS = re.compile(r"[\x00-\x1f\x7f]")
_EMAIL_PATTERN = re.compile(r"\b[^\s@]+@[^\s@]+\.[^\s@]+\b", re.IGNORECASE)
_PHONE_PATTERN = re.compile(r"(?<!\d)(?:\+?84|0)\d{8,10}(?!\d)")
_CARD_PATTERN = re.compile(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)")
_JWT_PATTERN = re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}")
_SECRET_PATTERN = re.compile(
    r"\b(?:bearer|password|passwd|token|secret|api[_-]?key)\b\s*[:=]?\s*\S+",
    re.IGNORECASE,
)
_ADDRESS_PATTERN = re.compile(
    r"\b\d{1,5}\s+(?:đường|phố|hẻm|ngõ|street|road)\b",
    re.IGNORECASE,
)
_DIMENSION_VALUE_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
_SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_UUID_PATTERN = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-8][0-9a-fA-F]{3}-"
    r"[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
)

_ACTIONS: dict[tuple[str, str], str] = {
    ("POST", "/api/v1/auth/register"): "register",
    ("POST", "/api/v1/auth/login"): "login",
    ("POST", "/api/v1/auth/logout"): "logout",
    ("GET", "/api/v1/auth/me"): "auth_profile",
    ("GET", "/api/v1/categories"): "category_list",
    ("GET", "/api/v1/catalog/facets"): "catalog_facets",
    ("GET", "/api/v1/products"): "catalog_search",
    ("GET", "/api/v1/products/{slug}"): "product_detail",
    ("GET", "/api/v1/products/{slug}/reviews"): "product_reviews",
    ("GET", "/api/v1/wishlist"): "wishlist_read",
    ("PUT", "/api/v1/wishlist/products/{product_public_id}"): "wishlist_add",
    ("DELETE", "/api/v1/wishlist/products/{product_public_id}"): "wishlist_remove",
    ("GET", "/api/v1/cart"): "cart_read",
    ("PUT", "/api/v1/cart/items/{variant_public_id}"): "cart_item_set",
    ("DELETE", "/api/v1/cart/items/{variant_public_id}"): "cart_item_remove",
    ("GET", "/api/v1/coupons/available"): "coupon_available",
    ("POST", "/api/v1/checkout/quote"): "checkout_quote",
    ("POST", "/api/v1/checkout"): "checkout_submit",
    ("GET", "/api/v1/orders"): "order_list",
    ("GET", "/api/v1/orders/{order_number}"): "order_detail",
    ("POST", "/api/v1/orders/{order_number}/cancel"): "order_cancel",
    ("POST", "/api/v1/orders/{order_number}/complete"): "order_complete",
    (
        "POST",
        "/api/v1/orders/{order_number}/items/{order_item_public_id}/review",
    ): "review_create",
    ("POST", "/internal/v1/orders/{order_number}/confirm"): "order_confirm_internal",
    ("GET", "/api/v1/admin/overview"): "admin_overview",
    ("GET", "/api/v1/admin/products"): "admin_product_list",
    ("POST", "/api/v1/admin/products"): "admin_product_create",
    ("PATCH", "/api/v1/admin/products/{public_id}"): "admin_product_update",
    ("DELETE", "/api/v1/admin/products/{public_id}"): "admin_product_archive",
    ("PATCH", "/api/v1/admin/variants/{public_id}"): "admin_variant_update",
    ("GET", "/api/v1/admin/orders"): "admin_order_list",
    ("GET", "/api/v1/admin/orders/{order_number}"): "admin_order_detail",
    ("POST", "/api/v1/admin/orders/{order_number}/confirm"): "admin_order_confirm",
    ("POST", "/api/v1/admin/orders/{order_number}/cancel"): "admin_order_cancel",
    ("GET", "/api/v1/admin/customers"): "admin_customer_list",
    ("PATCH", "/api/v1/admin/customers/{public_id}"): "admin_customer_update",
    ("GET", "/api/v1/admin/reviews"): "admin_review_list",
    ("PATCH", "/api/v1/admin/reviews/{public_id}"): "admin_review_moderate",
    ("GET", "/api/v1/admin/coupons"): "admin_coupon_list",
    ("POST", "/api/v1/admin/coupons"): "admin_coupon_create",
    ("PATCH", "/api/v1/admin/coupons/{public_id}"): "admin_coupon_update",
    ("DELETE", "/api/v1/admin/coupons/{public_id}"): "admin_coupon_archive",
}


def utc_iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


def canonical_route(request: Request) -> str:
    route = request.scope.get("route")
    path = getattr(route, "path", None)
    if not isinstance(path, str) or not path.startswith("/") or len(path) > 240:
        return "__unmatched__"
    return path


def action_for(method: str, route: str) -> str:
    return _ACTIONS.get((method.upper(), route), "unknown")


_EXCLUDED_ROUTES = frozenset({("GET", "/health/live"), ("GET", "/health/ready")})


def should_emit_access_event(method: str, route: str) -> bool:
    return (method.upper(), route) not in _EXCLUDED_ROUTES


def _contains_pii(value: str) -> bool:
    return any(
        pattern.search(value)
        for pattern in (
            _EMAIL_PATTERN,
            _PHONE_PATTERN,
            _CARD_PATTERN,
            _JWT_PATTERN,
            _SECRET_PATTERN,
            _ADDRESS_PATTERN,
        )
    )


def normalize_search_query(value: str | None) -> tuple[str | None, bool]:
    if not value:
        return None, False
    normalized = unicodedata.normalize("NFKC", value)
    normalized = " ".join(normalized.strip().lower().split())[:_MAX_SEARCH_LENGTH]
    if not normalized:
        return None, False
    if _contains_pii(normalized):
        return None, True
    return normalized, False


def _bounded_values(values: list[str], max_length: int) -> list[str]:
    result: list[str] = []
    for value in values[:_MAX_FILTER_VALUES]:
        normalized = unicodedata.normalize("NFKC", value).strip()[:max_length]
        if (
            normalized
            and _DIMENSION_VALUE_PATTERN.fullmatch(normalized)
            and normalized not in result
        ):
            result.append(normalized)
    return result


def _catalog_filters(request: Request) -> dict[str, Any]:
    query = request.query_params
    filters: dict[str, Any] = {}
    category = query.get("category")
    if category and _DIMENSION_VALUE_PATTERN.fullmatch(category.strip()):
        filters["category"] = category.strip()
    sizes = _bounded_values(query.getlist("size"), 32)
    colors = _bounded_values(query.getlist("color"), 64)
    if sizes:
        filters["size"] = sizes
    if colors:
        filters["color"] = colors
    for source_key, target_key in (("min_price", "min_price_vnd"), ("max_price", "max_price_vnd")):
        raw_value = query.get(source_key)
        if raw_value and raw_value.isdigit():
            filters[target_key] = min(int(raw_value), 10_000_000_000)
    if query.get("in_stock") in ("true", "false"):
        filters["in_stock"] = query.get("in_stock") == "true"
    if query.get("sort") in ("newest", "price_asc", "price_desc"):
        filters["sort"] = query.get("sort")
    return filters


def ecommerce_context(request: Request, route: str) -> dict[str, Any]:
    action = action_for(request.method, route)
    context: dict[str, Any] = {"action": action}
    path_params = request.path_params

    if action in ("product_detail", "product_reviews"):
        product_key = path_params.get("slug")
        if product_key and _SLUG_PATTERN.fullmatch(str(product_key)[:180]):
            context["product_key"] = str(product_key)[:180]
    elif action in ("wishlist_add", "wishlist_remove"):
        product_key = path_params.get("product_public_id")
        if product_key and _UUID_PATTERN.fullmatch(str(product_key)):
            context["product_key"] = str(product_key).lower()
    elif action in ("cart_item_set", "cart_item_remove"):
        variant_key = path_params.get("variant_public_id")
        if variant_key and _UUID_PATTERN.fullmatch(str(variant_key)):
            context["variant_key"] = str(variant_key).lower()

    if action == "catalog_search":
        search_query, search_redacted = normalize_search_query(request.query_params.get("q"))
        if search_query is not None:
            context["search_query"] = search_query
        if search_redacted:
            context["search_redacted"] = True
        filters = _catalog_filters(request)
        if filters:
            context["filters"] = filters

    return context


def _client_context(request: Request) -> dict[str, str]:
    raw = request.headers.get("user-agent", "")
    user_agent = _CONTROL_CHARACTERS.sub("", raw).strip()[:_MAX_USER_AGENT_LENGTH]
    return {"user_agent": user_agent} if user_agent and not _contains_pii(user_agent) else {}


def build_access_event(
    request: Request,
    *,
    request_id: str,
    status_code: int,
    duration_ns: int,
    completed_at: datetime,
    exception_type: str | None = None,
) -> dict[str, Any]:
    settings = get_settings()
    route = canonical_route(request)
    actor_type = getattr(request.state, "actor_type", "anonymous")
    actor_key = getattr(request.state, "actor_key", None)
    error_code = getattr(request.state, "error_code", None)

    if status_code >= 500:
        severity_text, severity_number = "ERROR", 17
    elif status_code >= 400:
        severity_text, severity_number = "WARN", 13
    else:
        severity_text, severity_number = "INFO", 9

    return {
        "schema": {"name": ACCESS_LOG_SCHEMA_NAME, "version": ACCESS_LOG_SCHEMA_VERSION},
        "timestamp": utc_iso(completed_at),
        "observed_timestamp": utc_iso(datetime.now(UTC)),
        "severity_text": severity_text,
        "severity_number": severity_number,
        "request": {"id": request_id},
        "trace_id": None,
        "span_id": None,
        "service": {
            "name": settings.service_name,
            "version": settings.service_version,
            "environment": settings.environment,
            "instance_id": os.getenv("HOSTNAME", settings.service_name)[:128],
        },
        "event": {
            "name": "http.server.request",
            "category": "web",
            "kind": "event",
            "outcome": "failure" if status_code >= 400 else "success",
            "duration_ns": max(0, duration_ns),
        },
        "http": {
            "request_method": request.method.upper(),
            "route": route,
            "status_code": status_code,
        },
        "actor": {"type": actor_type, "key": actor_key},
        "client": _client_context(request),
        "ecommerce": ecommerce_context(request, route),
        "error": {"code": error_code, "type": exception_type},
        "data_origin": "observed",
    }
