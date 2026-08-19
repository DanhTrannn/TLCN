from __future__ import annotations

import gzip
import hashlib
import json
import math
import random
import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any, Sequence
from zoneinfo import ZoneInfo

from generator import __version__
from generator.config import CATEGORY_NAMES, DistributionConfig, GeneratorConfig, SaleEvent, TetWindow


SCHEMA_NAME = "ecommerce.access"
SCHEMA_VERSION = "1.0.0"
WINDOW_MINUTES = 15
_LOG_IDENTITY_NAMESPACE = uuid.uuid5(
    uuid.NAMESPACE_URL,
    "https://d-and-k.local/data-generator/access-log-identity",
)


@dataclass(frozen=True)
class RouteScenario:
    method: str
    route: str
    action: str
    ordinary_weight: float
    campaign_weight: float
    latency_ms: float
    actor_policy: str = "mixed"


ROUTES = (
    RouteScenario("GET", "/api/v1/categories", "category_list", 5, 5, 25),
    RouteScenario("GET", "/api/v1/catalog/facets", "catalog_facets", 5, 7, 45),
    RouteScenario("GET", "/api/v1/products", "catalog_search", 24, 29, 85),
    RouteScenario("GET", "/api/v1/products/{slug}", "product_detail", 30, 32, 70),
    RouteScenario("GET", "/api/v1/products/{slug}/reviews", "product_reviews", 4, 4, 65),
    RouteScenario("POST", "/api/v1/auth/login", "login", 2, 2, 130, "anonymous"),
    RouteScenario("GET", "/api/v1/auth/me", "auth_profile", 3, 2, 35, "mixed"),
    RouteScenario("GET", "/api/v1/wishlist", "wishlist_read", 2, 2, 55, "customer"),
    RouteScenario("PUT", "/api/v1/wishlist/products/{product_public_id}", "wishlist_add", 2, 3, 75, "customer"),
    RouteScenario("GET", "/api/v1/cart", "cart_read", 4, 5, 65, "customer"),
    RouteScenario("PUT", "/api/v1/cart/items/{variant_public_id}", "cart_item_set", 5, 7, 100, "customer"),
    RouteScenario("GET", "/api/v1/coupons/available", "coupon_available", 2, 5, 70, "customer"),
    RouteScenario("POST", "/api/v1/checkout/quote", "checkout_quote", 2, 4, 180, "customer"),
    RouteScenario("POST", "/api/v1/checkout", "checkout_submit", 1, 3, 320, "customer"),
    RouteScenario("GET", "/api/v1/orders", "order_list", 2, 2, 90, "customer"),
    RouteScenario("GET", "/api/v1/orders/{order_number}", "order_detail", 1, 1, 80, "customer"),
    RouteScenario("GET", "/health/ready", "health_ready", 6, 3, 8, "system"),
)

SEARCH_TERMS = (
    "áo sơ mi nữ",
    "đầm dự tiệc",
    "chân váy midi",
    "quần jeans ống rộng",
    "áo khoác nữ",
    "túi xách nữ",
    "giày nữ",
    "phụ kiện nữ",
    "đầm linen",
    "áo công sở",
)
USER_AGENTS = (
    "Mozilla/5.0 Chrome/126 Mobile Safari/537.36",
    "Mozilla/5.0 Safari/605.1.15",
    "Mozilla/5.0 Chrome/126 Safari/537.36",
    "D&K-Android/1.0",
)


@dataclass(frozen=True)
class LogExportSummary:
    output_root: Path
    logical_identity: str
    expected_requests: int
    emitted_requests: int
    files: int
    manifests: int


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _entity_uuid(namespace: uuid.UUID, entity: str, index: int) -> uuid.UUID:
    return uuid.uuid5(namespace, f"{entity}:{index}")


def _event_day(event: SaleEvent, year: int) -> date | None:
    if event.day is not None:
        try:
            return datetime(year, event.month, event.day).date()
        except ValueError:
            return None
    if event.weekday is None or event.week_index is None:
        return None
    first = datetime(year, event.month, 1).date()
    offset = (event.weekday - first.weekday()) % 7
    return first + timedelta(days=offset + 7 * (event.week_index - 1))


def _tet_factor(day: date, tet: TetWindow) -> float:
    start = datetime(day.year, tet.month_start, tet.day_start).date()
    end_year = day.year + 1 if tet.month_end < tet.month_start else day.year
    end = datetime(end_year, tet.month_end, tet.day_end).date()
    if not start <= day <= end:
        return 1.0
    center = start + (end - start) / 2
    half_span = max(1, (end - start).days // 2)
    distance = abs((day - center).days) / half_span
    return 1.0 + (tet.peak - 1.0) * max(0.0, 1.0 - distance)


def _sale_boost(day: date, distributions: DistributionConfig) -> float:
    boost = 1.0
    for event in distributions.sales:
        event_day = _event_day(event, day.year)
        if event_day is not None and event_day <= day <= event_day + timedelta(
            days=event.after_days
        ):
            boost *= event.boost
    return boost


def _window_floor(value: datetime) -> datetime:
    utc_value = value.astimezone(UTC)
    minute = utc_value.minute - utc_value.minute % WINDOW_MINUTES
    return utc_value.replace(minute=minute, second=0, microsecond=0)


def _poisson(randomizer: random.Random, expected: float) -> int:
    if expected <= 0:
        return 0
    if expected >= 30:
        return max(0, round(randomizer.gauss(expected, math.sqrt(expected))))
    threshold = math.exp(-expected)
    draws = 0
    product = 1.0
    while product > threshold:
        draws += 1
        product *= randomizer.random()
    return draws - 1


def _log_identity(config: GeneratorConfig, expected_requests: int) -> str:
    payload = json.dumps(
        {
            "generator_version": __version__,
            "oltp_logical_identity": config.logical_identity,
            "schema": {"name": SCHEMA_NAME, "version": SCHEMA_VERSION},
            "expected_requests": expected_requests,
            "window_minutes": WINDOW_MINUTES,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(payload.encode()).hexdigest()
    return str(uuid.uuid5(_LOG_IDENTITY_NAMESPACE, digest))


def _window_weight(window_start: datetime, config: GeneratorConfig) -> float:
    distribution = config.distributions
    local = window_start.astimezone(ZoneInfo(distribution.business_timezone))
    campaign = _sale_boost(local.date(), distribution)
    hour_weights = (
        distribution.campaign_hour_of_day
        if campaign > 1
        else distribution.hour_of_day
    )
    return (
        distribution.day_of_week[local.weekday()]
        * hour_weights[local.hour]
        * _tet_factor(local.date(), distribution.tet)
        * campaign
    )


def _weighted_choice(
    randomizer: random.Random,
    choices: tuple[RouteScenario, ...],
    *,
    campaign: bool,
) -> RouteScenario:
    weights = [item.campaign_weight if campaign else item.ordinary_weight for item in choices]
    return randomizer.choices(choices, weights=weights, k=1)[0]


def _actor(
    scenario: RouteScenario,
    randomizer: random.Random,
    namespace: uuid.UUID,
    active_customer_indices: tuple[int, ...],
) -> tuple[str, str | None]:
    if scenario.actor_policy == "system":
        return "system", "synthetic-health-check"
    if scenario.actor_policy == "anonymous":
        return "anonymous", None
    if scenario.actor_policy == "mixed" and randomizer.random() < 0.58:
        return "anonymous", None
    index = randomizer.choice(active_customer_indices)
    return "customer", str(_entity_uuid(namespace, "customer", index))


def _active_customer_indices(config: GeneratorConfig) -> tuple[int, ...]:
    """Replay the SQL exporter's customer-status random stream exactly."""
    randomizer = random.Random(config.seed)
    result: list[int] = []
    for customer_index in range(config.scale["customers"]):
        randomizer.randrange(1, 181)
        is_active = customer_index == 0 or randomizer.random() >= 0.04
        if is_active:
            result.append(customer_index)
    return tuple(result)


def _weighted_index(randomizer: random.Random, weights: Sequence[int | float]) -> int:
    total = sum(weights)
    target = randomizer.random() * total
    cumulative = 0.0
    for index, weight in enumerate(weights):
        cumulative += weight
        if target < cumulative:
            return index
    return len(weights) - 1


def _product_slugs(config: GeneratorConfig) -> tuple[str, ...]:
    """Replay the SQL exporter's product category/slug assignment stream."""
    randomizer = random.Random(config.seed)
    categories = config.distributions.categories
    weights = [weight for _, weight in categories]
    category_sequences = {code: 0 for code in CATEGORY_NAMES}
    slugs: list[str] = []
    for _ in range(config.scale["products"]):
        idx = _weighted_index(randomizer, weights)
        category_code = categories[idx][0]
        category_sequence = category_sequences[category_code]
        category_sequences[category_code] += 1
        slugs.append(f"syn-{config.logical_identity[:8]}-{category_code}-{category_sequence + 1:05d}")
    return tuple(slugs)


def _commerce_context(
    scenario: RouteScenario,
    randomizer: random.Random,
    namespace: uuid.UUID,
    product_slugs: tuple[str, ...],
    variant_count: int,
) -> dict[str, Any]:
    context: dict[str, Any] = {"action": scenario.action}
    product_count = len(product_slugs)
    if scenario.action in {"product_detail", "product_reviews"}:
        index = randomizer.randrange(product_count)
        context["product_key"] = product_slugs[index]
    elif scenario.action in {"wishlist_add", "wishlist_remove"}:
        index = randomizer.randrange(product_count)
        context["product_key"] = str(_entity_uuid(namespace, "product", index))
    if scenario.action == "cart_item_set":
        index = randomizer.randrange(variant_count)
        context["variant_key"] = str(_entity_uuid(namespace, "variant", index))
    if scenario.action == "catalog_search":
        if randomizer.random() < 0.62:
            context["search_query"] = randomizer.choice(SEARCH_TERMS)
        if randomizer.random() < 0.55:
            category = randomizer.choice(tuple(CATEGORY_NAMES))
            context["filters"] = {
                "category": category,
                "in_stock": randomizer.random() < 0.82,
                "sort": randomizer.choice(("newest", "price_asc", "price_desc")),
            }
    return context


def _outcome(
    scenario: RouteScenario,
    actor_type: str,
    randomizer: random.Random,
    *,
    campaign: bool,
) -> tuple[int, str | None, str | None]:
    if (
        scenario.actor_policy == "customer" or scenario.action == "auth_profile"
    ) and actor_type == "anonymous":
        return 401, "AUTH_REQUIRED", None

    five_xx_rate = 0.004 if not campaign else 0.009
    if randomizer.random() < five_xx_rate:
        return 500, "INTERNAL_ERROR", "SyntheticServiceError"

    four_xx_rate = 0.008
    error_code = "VALIDATION_ERROR"
    status = 422
    if scenario.action in {"checkout_quote", "checkout_submit"}:
        four_xx_rate = 0.045 if not campaign else 0.07
        error_code = randomizer.choice(("OUT_OF_STOCK", "COUPON_INVALID", "EMPTY_CART"))
        status = 409
    elif scenario.action in {"product_detail", "product_reviews", "order_detail"}:
        four_xx_rate = 0.012
        error_code = "RESOURCE_NOT_FOUND"
        status = 404
    elif scenario.action == "login":
        four_xx_rate = 0.07
        error_code = "INVALID_CREDENTIALS"
        status = 401

    if randomizer.random() < four_xx_rate:
        return status, error_code, None
    if scenario.method == "DELETE":
        return 204, None, None
    if scenario.action in {"checkout_submit", "register"}:
        return 201, None, None
    return 200, None, None


def _event(
    *,
    log_namespace: uuid.UUID,
    event_index: int,
    completed_at: datetime,
    scenario: RouteScenario,
    actor_type: str,
    actor_key: str | None,
    ecommerce: dict[str, Any],
    status_code: int,
    error_code: str | None,
    error_type: str | None,
    latency_randomizer: random.Random,
    user_agent_randomizer: random.Random,
    campaign: bool,
) -> dict[str, Any]:
    load_factor = 1.35 if campaign else 1.0
    latency_ms = latency_randomizer.lognormvariate(
        math.log(scenario.latency_ms * load_factor),
        0.48,
    )
    if status_code >= 500:
        latency_ms *= 1.8
    severity_text, severity_number = (
        ("ERROR", 17)
        if status_code >= 500
        else ("WARN", 13)
        if status_code >= 400
        else ("INFO", 9)
    )
    return {
        "schema": {"name": SCHEMA_NAME, "version": SCHEMA_VERSION},
        "timestamp": _iso(completed_at),
        "observed_timestamp": _iso(completed_at + timedelta(microseconds=100)),
        "severity_text": severity_text,
        "severity_number": severity_number,
        "request": {"id": uuid.uuid5(log_namespace, f"request:{event_index}").hex},
        "trace_id": None,
        "span_id": None,
        "service": {
            "name": "ecommerce-api",
            "version": "0.1.0",
            "environment": "synthetic",
            "instance_id": "synthetic-generator",
        },
        "event": {
            "name": "http.server.request",
            "category": "web",
            "kind": "event",
            "outcome": "failure" if status_code >= 400 else "success",
            "duration_ns": max(1, round(latency_ms * 1_000_000)),
        },
        "http": {
            "request_method": scenario.method,
            "route": scenario.route,
            "status_code": status_code,
        },
        "actor": {"type": actor_type, "key": actor_key},
        "client": {"user_agent": user_agent_randomizer.choice(USER_AGENTS)},
        "ecommerce": ecommerce,
        "error": {"code": error_code, "type": error_type},
        "data_origin": "synthetic",
    }


def _write_window(
    output_root: Path,
    log_identity: str,
    oltp_logical_identity: str,
    window_start: datetime,
    events: list[dict[str, Any]],
) -> tuple[Path, Path]:
    window_end = window_start + timedelta(minutes=WINDOW_MINUTES)
    directory = (
        output_root
        / "landing"
        / "logs"
        / f"date={window_start:%Y-%m-%d}"
        / f"hour={window_start:%H}"
        / "service=ecommerce-api"
    )
    directory.mkdir(parents=True, exist_ok=True)
    part_id = uuid.uuid5(uuid.UUID(log_identity), f"window:{_iso(window_start)}")
    data_path = directory / f"part-{part_id}.jsonl.gz"
    temporary_path = data_path.with_suffix(data_path.suffix + ".tmp")

    with temporary_path.open("wb") as raw_stream:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw_stream, mtime=0) as stream:
            for event in events:
                line = json.dumps(
                    event,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                stream.write(line.encode("utf-8") + b"\n")
    temporary_path.replace(data_path)

    compressed = data_path.read_bytes()
    timestamps = [event["timestamp"] for event in events]
    manifest = {
        "manifest_version": "1.0.0",
        "object_path": data_path.relative_to(output_root).as_posix(),
        "sha256": hashlib.sha256(compressed).hexdigest(),
        "compressed_bytes": len(compressed),
        "line_count": len(events),
        "window_start": _iso(window_start),
        "window_end": _iso(window_end),
        "min_event_timestamp": min(timestamps),
        "max_event_timestamp": max(timestamps),
        "service": "ecommerce-api",
        "instance": "synthetic-generator",
        "schema_versions": [SCHEMA_VERSION],
        "data_origins": ["synthetic"],
        "generator_version": __version__,
        "log_logical_identity": log_identity,
        "oltp_logical_identity": oltp_logical_identity,
    }
    manifest_path = data_path.with_suffix(".manifest.json")
    temporary_manifest = manifest_path.with_suffix(manifest_path.suffix + ".tmp")
    temporary_manifest.write_text(
        json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n",
        encoding="utf-8",
    )
    temporary_manifest.replace(manifest_path)
    return data_path, manifest_path


def export_logs(
    config: GeneratorConfig,
    output_root: Path,
    *,
    expected_requests: int,
) -> LogExportSummary:
    if expected_requests < 1:
        raise ValueError("expected_requests must be positive")
    customer_count = config.scale.get("customers", 0)
    product_count = config.scale.get("products", 0)
    variant_count = config.scale.get("variants", 0)
    if min(customer_count, product_count, variant_count) < 1:
        raise ValueError("customers, products, and variants must be positive")

    history_end = config.anchor_time.astimezone(UTC)
    history_start = history_end - timedelta(days=max(1, config.history_months) * 30)
    first_window = _window_floor(history_start)
    windows: list[datetime] = []
    cursor = first_window
    while cursor < history_end:
        windows.append(cursor)
        cursor += timedelta(minutes=WINDOW_MINUTES)
    weights = [_window_weight(window, config) for window in windows]
    base_rate = expected_requests / sum(weights)

    log_identity = _log_identity(config, expected_requests)
    log_namespace = uuid.UUID(log_identity)
    oltp_namespace = uuid.UUID(config.logical_identity)
    arrival_randomizer = random.Random(f"{config.seed}:log-arrivals")
    time_randomizer = random.Random(f"{config.seed}:log-times")
    route_randomizer = random.Random(f"{config.seed}:log-routes")
    actor_randomizer = random.Random(f"{config.seed}:log-actors")
    context_randomizer = random.Random(f"{config.seed}:log-commerce")
    outcome_randomizer = random.Random(f"{config.seed}:log-outcomes")
    latency_randomizer = random.Random(f"{config.seed}:log-latency")
    user_agent_randomizer = random.Random(f"{config.seed}:log-user-agents")
    business_zone = ZoneInfo(config.distributions.business_timezone)
    active_customer_indices = _active_customer_indices(config)
    product_slugs = _product_slugs(config)

    emitted = 0
    files = 0
    for window, weight in zip(windows, weights):
        window_end = min(window + timedelta(minutes=WINDOW_MINUTES), history_end)
        if window_end <= history_start:
            continue
        count = _poisson(arrival_randomizer, base_rate * weight)
        local_day = window.astimezone(business_zone).date()
        campaign = _sale_boost(local_day, config.distributions) > 1
        # Even tiny unit-test datasets retain evidence that each configured campaign
        # occurred; realistic datasets naturally contain many events in these windows.
        if campaign and window.astimezone(business_zone).hour == 0 and count == 0:
            count = 1
        if count == 0:
            continue

        span_microseconds = max(
            1,
            int((window_end - max(window, history_start)).total_seconds() * 1_000_000),
        )
        effective_start = max(window, history_start)
        events: list[dict[str, Any]] = []
        for _ in range(count):
            completed_at = effective_start + timedelta(
                microseconds=time_randomizer.randrange(span_microseconds)
            )
            scenario = _weighted_choice(route_randomizer, ROUTES, campaign=campaign)
            actor_type, actor_key = _actor(
                scenario,
                actor_randomizer,
                oltp_namespace,
                active_customer_indices,
            )
            ecommerce = _commerce_context(
                scenario,
                context_randomizer,
                oltp_namespace,
                product_slugs,
                variant_count,
            )
            status_code, error_code, error_type = _outcome(
                scenario,
                actor_type,
                outcome_randomizer,
                campaign=campaign,
            )
            events.append(
                _event(
                    log_namespace=log_namespace,
                    event_index=emitted,
                    completed_at=completed_at,
                    scenario=scenario,
                    actor_type=actor_type,
                    actor_key=actor_key,
                    ecommerce=ecommerce,
                    status_code=status_code,
                    error_code=error_code,
                    error_type=error_type,
                    latency_randomizer=latency_randomizer,
                    user_agent_randomizer=user_agent_randomizer,
                    campaign=campaign,
                )
            )
            emitted += 1
        events.sort(key=lambda item: (item["timestamp"], item["request"]["id"]))
        _write_window(
            output_root,
            log_identity,
            config.logical_identity,
            window,
            events,
        )
        files += 1

    return LogExportSummary(
        output_root=output_root,
        logical_identity=log_identity,
        expected_requests=expected_requests,
        emitted_requests=emitted,
        files=files,
        manifests=files,
    )
