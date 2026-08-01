from __future__ import annotations

import hashlib
import random
import uuid
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import TextIO, TypeAlias

from argon2.low_level import Type, hash_secret

from tlcn_generator import __version__
from tlcn_generator.config import CATEGORY_NAMES, CustomerClass, DistributionConfig, GeneratorConfig, PriceBand, SaleEvent, TetWindow


DEMO_PASSWORD = "Demo@12345"
INSERT_BATCH_SIZE = 250
SIZES = ("XS", "S", "M", "L", "XL")
COLORS = ("BLACK", "WHITE", "RED", "GREEN", "BLUE", "YELLOW", "PINK", "PURPLE", "ORANGE", "BROWN", "GRAY", "BEIGE")
LEAF_CATEGORIES = tuple((code, name) for code, name in CATEGORY_NAMES.items())


@dataclass(frozen=True)
class SqlExpression:
    value: str


SqlValue: TypeAlias = str | int | bool | datetime | None | SqlExpression


@dataclass(frozen=True)
class CategoryRecord:
    category_id: int
    code: str
    name: str


@dataclass(frozen=True)
class ProductRecord:
    product_id: int
    public_id: uuid.UUID
    category: CategoryRecord
    slug: str
    name: str


@dataclass(frozen=True)
class VariantRecord:
    variant_id: int
    product: ProductRecord
    public_id: uuid.UUID
    sku: str
    size_code: str
    color_code: str
    price_vnd: int


@dataclass(frozen=True)
class DatasetSummary:
    sql_path: Path
    generation_run_id: str
    demo_email: str
    demo_password: str
    customers: int
    products: int
    variants: int
    orders: int


def _sql_literal(value: SqlValue) -> str:
    if isinstance(value, SqlExpression):
        return value.value
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, datetime):
        normalized = value.astimezone(UTC).replace(tzinfo=None)
        return f"'{normalized.strftime('%Y-%m-%d %H:%M:%S.%f')}'"
    escaped = value.replace("\\", "\\\\").replace("'", "''")
    return f"'{escaped}'"


def _binary_uuid(value: uuid.UUID) -> SqlExpression:
    return SqlExpression(f"UNHEX('{value.hex}')")


def _write_insert(
    stream: TextIO,
    table: str,
    columns: Sequence[str],
    rows: Sequence[Sequence[SqlValue]],
) -> None:
    if not rows:
        return
    column_sql = ", ".join(f"`{column}`" for column in columns)
    stream.write(f"INSERT INTO `{table}` ({column_sql}) VALUES\n")
    for index, row in enumerate(rows):
        suffix = ";\n\n" if index == len(rows) - 1 else ",\n"
        stream.write("  (" + ", ".join(_sql_literal(value) for value in row) + ")" + suffix)


def _chunks(values: Sequence[Sequence[SqlValue]], size: int = INSERT_BATCH_SIZE) -> Iterable[Sequence[Sequence[SqlValue]]]:
    for start in range(0, len(values), size):
        yield values[start : start + size]


def _write_batched(
    stream: TextIO,
    table: str,
    columns: Sequence[str],
    rows: Sequence[Sequence[SqlValue]],
) -> None:
    for batch in _chunks(rows):
        _write_insert(stream, table, columns, batch)


def _entity_uuid(namespace: uuid.UUID, entity: str, index: int) -> uuid.UUID:
    return uuid.uuid5(namespace, f"{entity}:{index}")


def _deterministic_password_hash(logical_identity: str) -> str:
    salt = hashlib.sha256(f"{logical_identity}:demo-password".encode()).digest()[:16]
    return hash_secret(
        secret=DEMO_PASSWORD.encode(),
        salt=salt,
        time_cost=3,
        memory_cost=65536,
        parallelism=4,
        hash_len=32,
        type=Type.ID,
    ).decode()


def _validate_scale(config: GeneratorConfig) -> tuple[int, int, int, int]:
    required = ("customers", "products", "variants", "orders")
    missing = [key for key in required if key not in config.scale]
    if missing:
        raise ValueError(f"missing scale keys: {missing}")

    customer_count = config.scale["customers"]
    product_count = config.scale["products"]
    variant_count = config.scale["variants"]
    order_count = config.scale["orders"]
    if customer_count < 1 or product_count < 1 or order_count < 0:
        raise ValueError("customers/products must be positive and orders must be non-negative")
    if variant_count < product_count:
        raise ValueError("variants must be greater than or equal to products")
    if variant_count > product_count * len(SIZES) * len(COLORS):
        raise ValueError("variant scale exceeds unique size/color combinations")
    return customer_count, product_count, variant_count, order_count


def _timestamp_between(randomizer: random.Random, start: datetime, end: datetime) -> datetime:
    span_seconds = max(1, int((end - start).total_seconds()))
    return start + timedelta(seconds=randomizer.randrange(span_seconds))


def _weighted_index(randomizer: random.Random, weights: Sequence[int | float]) -> int:
    total = sum(weights)
    target = randomizer.random() * total
    cumulative = 0.0
    for index, weight in enumerate(weights):
        cumulative += weight
        if target < cumulative:
            return index
    return len(weights) - 1


def _largest_remainder(values: Sequence[float], total: int) -> list[int]:
    floors = [int(value) for value in values]
    remainder = total - sum(floors)
    ordered = sorted(range(len(values)), key=lambda i: values[i] - floors[i], reverse=True)
    for position in range(remainder):
        floors[ordered[position % len(ordered)]] += 1
    return floors


def _class_assignment(customer_count: int, classes: Sequence[CustomerClass], randomizer: random.Random) -> list[str]:
    counts = _largest_remainder([class_.share * customer_count for class_ in classes], customer_count)
    assignment: list[str] = []
    for class_, count in zip(classes, counts):
        assignment.extend([class_.name] * count)
    return assignment


def _order_targets(
    assignment: Sequence[str],
    class_by_name: dict[str, CustomerClass],
    demo_target: int,
    total_orders: int,
    randomizer: random.Random,
) -> list[int]:
    if len(assignment) == 1:
        return [total_orders]
    demo = min(demo_target, total_orders)
    remaining = total_orders - demo
    raw = []
    for name in assignment[1:]:
        class_ = class_by_name[name]
        raw.append(randomizer.randint(class_.orders_min, class_.orders_max))
    if remaining == 0:
        return [demo] + [0] * len(raw)
    raw_sum = sum(raw)
    scaled = [value * remaining / raw_sum for value in raw]
    return [demo] + _largest_remainder(scaled, remaining)


def _nth_weekday(year: int, month: int, weekday: int, week_index: int) -> date:
    first = date(year, month, 1)
    offset = (weekday - first.weekday()) % 7
    return first + timedelta(days=offset + 7 * (week_index - 1))


def _event_day(event: SaleEvent, year: int) -> date | None:
    if event.day is not None:
        try:
            return date(year, event.month, event.day)
        except ValueError:
            return None
    if event.weekday is not None and event.week_index is not None:
        return _nth_weekday(year, event.month, event.weekday, event.week_index)
    return None


def _tet_factor(day: date, tet: TetWindow) -> float:
    start = date(day.year, tet.month_start, tet.day_start)
    end = (
        date(day.year + 1, tet.month_end, tet.day_end)
        if tet.month_end < tet.month_start
        else date(day.year, tet.month_end, tet.day_end)
    )
    if not (start <= day <= end):
        return 1.0
    center = start + (end - start) / 2
    half_span = max(1, (end - start).days // 2)
    distance = abs((day - center).days) / half_span
    return 1.0 + (tet.peak - 1.0) * max(0.0, 1.0 - distance)


def _sale_boost(day: date, distributions: DistributionConfig) -> float:
    boost = 1.0
    for event in distributions.sales:
        event_day = _event_day(event, day.year)
        if event_day is None:
            continue
        if event_day <= day <= event_day + timedelta(days=event.after_days):
            boost *= event.boost
    return boost


def _build_day_weights(
    history_start: date,
    history_end: date,
    distributions: DistributionConfig,
) -> tuple[list[date], list[float]]:
    days: list[date] = []
    weights: list[float] = []
    current = history_start
    while current <= history_end:
        days.append(current)
        weight = distributions.day_of_week[current.weekday()]
        weight *= _tet_factor(current, distributions.tet)
        weight *= _sale_boost(current, distributions)
        weights.append(weight)
        current += timedelta(days=1)
    return days, weights


def _pick_base_datetime(
    randomizer: random.Random,
    history_start: datetime,
    history_end: datetime,
    days: Sequence[date],
    day_weights: Sequence[float],
    hour_of_day: Sequence[float],
) -> datetime:
    day = days[_weighted_index(randomizer, day_weights)]
    hour = _weighted_index(randomizer, hour_of_day)
    minute = randomizer.randrange(60)
    return min(
        history_start.replace(
            year=day.year, month=day.month, day=day.day, hour=hour, minute=minute, second=0, microsecond=0
        ),
        history_end,
    )


def _shape_hour(randomizer: random.Random, moment: datetime, hour_of_day: Sequence[float]) -> datetime:
    hour = _weighted_index(randomizer, hour_of_day)
    return moment.replace(hour=hour, minute=randomizer.randrange(60), second=0, microsecond=0)


def _pick_product_price(randomizer: random.Random, bands: Sequence[PriceBand]) -> int:
    band = bands[_weighted_index(randomizer, [band.weight for band in bands])]
    return randomizer.randrange(band.min_vnd, band.max_vnd + 1, 1000)


def _pick_category(randomizer: random.Random, categories: Sequence[tuple[str, float]]) -> str:
    return categories[_weighted_index(randomizer, [weight for _, weight in categories])][0]


def _write_header(
    stream: TextIO, config: GeneratorConfig, generation_run_id: str, demo_email: str
) -> None:
    stream.write(
        "-- TLCN deterministic MySQL dataset\n"
        f"-- generator_version: {__version__}\n"
        f"-- scenario_id: {config.scenario_id}\n"
        f"-- logical_identity: {config.logical_identity}\n"
        f"-- generation_run_id: {generation_run_id}\n"
        f"-- seed: {config.seed}\n"
        f"-- anchor_time: {config.anchor_time.isoformat()}\n"
        f"-- demo_login: {demo_email} / {DEMO_PASSWORD}\n"
        "-- Prerequisite: run Alembic migrations through revision 0004.\n"
        "-- Import is fail-fast; importing the same dataset twice is rejected by unique keys.\n\n"
        "SET NAMES utf8mb4;\n"
        "SET time_zone = '+00:00';\n"
        "SET autocommit = 0;\n"
        "START TRANSACTION;\n\n"
    )


def export_sql(config: GeneratorConfig, output_path: Path) -> DatasetSummary:
    customer_count, product_count, variant_count, order_count = _validate_scale(config)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    randomizer = random.Random(config.seed)
    namespace = uuid.uuid5(uuid.NAMESPACE_URL, f"tlcn-sql:{config.logical_identity}")
    generation_run_id = f"sql-{config.logical_identity}"
    demo_email = f"demo.{config.logical_identity[:8]}@tlcn.local"
    history_end = config.anchor_time.astimezone(UTC)
    history_start = history_end - timedelta(days=max(1, config.history_months) * 30)
    distribution = config.distributions
    max_price_vnd = max(band.max_vnd for band in distribution.price_bands)
    master_created_at = history_start - timedelta(days=30)

    block = 10_000_000 + (int(config.logical_identity[:8], 16) % 10_000) * 10_000_000
    customer_base = block
    category_base = block
    product_base = block
    variant_base = block
    cart_base = block
    cart_item_base = block
    wishlist_base = block
    order_base = block
    order_item_base = block
    payment_base = block
    history_base = block

    customer_ids = [customer_base + index + 1 for index in range(customer_count)]
    active_customer_indices: list[int] = []
    customer_rows: list[Sequence[SqlValue]] = []
    for customer_index, customer_id in enumerate(customer_ids):
        created_at = history_start - timedelta(days=randomizer.randrange(1, 181))
        is_active = customer_index == 0 or randomizer.random() >= 0.04
        if is_active:
            active_customer_indices.append(customer_index)
        updated_at = created_at if is_active else history_end - timedelta(days=randomizer.randrange(1, 61))
        customer_rows.append(
            (
                customer_id,
                _binary_uuid(_entity_uuid(namespace, "customer", customer_index)),
                "customer",
                f"Khách hàng tổng hợp {customer_index + 1:05d}",
                "active" if is_active else "inactive",
                "synthetic",
                generation_run_id,
                None,
                created_at,
                updated_at,
            )
        )

    credential_rows: list[Sequence[SqlValue]] = [
        (
            customer_ids[0],
            demo_email,
            _deterministic_password_hash(config.logical_identity),
            True,
            history_start,
            history_start,
            history_start,
        )
    ]

    root_category = CategoryRecord(category_base + 1, f"syn-{config.logical_identity[:8]}", "Thời trang tổng hợp")
    category_records = [
        CategoryRecord(category_base + index + 2, f"{root_category.code}-{code}", name)
        for index, (code, name) in enumerate(LEAF_CATEGORIES)
    ]
    category_rows: list[Sequence[SqlValue]] = [
        (
            root_category.category_id,
            _binary_uuid(_entity_uuid(namespace, "category", 0)),
            None,
            root_category.code,
            root_category.name,
            True,
            master_created_at,
            master_created_at,
        )
    ]
    category_rows.extend(
        (
            category.category_id,
            _binary_uuid(_entity_uuid(namespace, "category", index + 1)),
            root_category.category_id,
            category.code,
            category.name,
            True,
            master_created_at,
            master_created_at,
        )
        for index, category in enumerate(category_records)
    )

    category_by_code = {
        category.code.removeprefix(f"{root_category.code}-"): category for category in category_records
    }
    product_records: list[ProductRecord] = []
    product_rows: list[Sequence[SqlValue]] = []
    base_variants_per_product, extra_variants = divmod(variant_count, product_count)
    variant_records: list[VariantRecord] = []
    variant_rows: list[Sequence[SqlValue]] = []
    variant_index = 0
    combinations = [(size, color) for size in SIZES for color in COLORS]
    for product_index in range(product_count):
        category_code = _pick_category(randomizer, distribution.categories)
        category = category_by_code[category_code]
        product_price_vnd = _pick_product_price(randomizer, distribution.price_bands)
        product = ProductRecord(
            product_id=product_base + product_index + 1,
            public_id=_entity_uuid(namespace, "product", product_index),
            category=category,
            slug=f"syn-{config.logical_identity[:8]}-product-{product_index + 1:05d}",
            name=f"Sản phẩm tổng hợp {product_index + 1:05d}",
        )
        product_records.append(product)
        product_rows.append(
            (
                product.product_id,
                _binary_uuid(product.public_id),
                category.category_id,
                product.slug,
                product.name,
                f"Dữ liệu tổng hợp cho kịch bản {config.scenario_id}.",
                f"https://picsum.photos/seed/{product.slug}/600/600",
                True,
                master_created_at,
                master_created_at,
            )
        )
        product_variant_count = base_variants_per_product + (1 if product_index < extra_variants else 0)
        for combination_index in range(product_variant_count):
            size_code, color_code = combinations[combination_index]
            variant = VariantRecord(
                variant_id=variant_base + variant_index + 1,
                product=product,
                public_id=_entity_uuid(namespace, "variant", variant_index),
                sku=f"SYN-{config.logical_identity[:8].upper()}-{product_index + 1:05d}-{combination_index + 1:02d}",
                size_code=size_code,
                color_code=color_code,
                price_vnd=min(product_price_vnd + combination_index * 5_000, max_price_vnd),
            )
            variant_records.append(variant)
            variant_rows.append(
                (
                    variant.variant_id,
                    _binary_uuid(variant.public_id),
                    product.product_id,
                    variant.sku,
                    size_code,
                    color_code,
                    variant.price_vnd,
                    True,
                    master_created_at,
                    master_created_at,
                )
            )
            variant_index += 1

    wishlist_rows: list[Sequence[SqlValue]] = []
    wishlist_index = 0
    for customer_index, customer_id in enumerate(customer_ids):
        if randomizer.random() >= 0.55:
            continue
        wishlist_count = randomizer.randint(1, min(5, product_count))
        selected_products = randomizer.sample(product_records, wishlist_count)
        for product in selected_products:
            first_added_at = _timestamp_between(randomizer, history_start, history_end)
            last_added_at = first_added_at + timedelta(days=randomizer.randrange(0, 30))
            if last_added_at > history_end:
                last_added_at = history_end
            is_present = randomizer.random() >= 0.18
            removed_at = None if is_present else min(history_end, last_added_at + timedelta(days=randomizer.randrange(0, 15)))
            wishlist_rows.append(
                (
                    wishlist_base + wishlist_index + 1,
                    customer_id,
                    product.product_id,
                    is_present,
                    first_added_at,
                    last_added_at,
                    removed_at,
                    removed_at or last_added_at,
                )
            )
            wishlist_index += 1

    sold_quantities = {variant.variant_id: 0 for variant in variant_records}
    inventory_versions = {variant.variant_id: 0 for variant in variant_records}
    class_by_name = {class_.name: class_ for class_ in distribution.customer_classes}
    assignment = _class_assignment(customer_count, distribution.customer_classes, randomizer)
    days, day_weights = _build_day_weights(history_start.date(), history_end.date(), distribution)

    temporary_path = output_path.with_suffix(output_path.suffix + ".tmp")
    with temporary_path.open("w", encoding="utf-8", newline="\n") as stream:
        _write_header(stream, config, generation_run_id, demo_email)
        _write_batched(
            stream,
            "customers",
            (
                "customer_id",
                "public_id",
                "role",
                "display_name",
                "status",
                "data_origin",
                "generation_run_id",
                "anonymized_at",
                "created_at",
                "updated_at",
            ),
            customer_rows,
        )
        _write_batched(
            stream,
            "customer_credentials",
            (
                "customer_id",
                "email_normalized",
                "password_hash",
                "is_enabled",
                "password_changed_at",
                "created_at",
                "updated_at",
            ),
            credential_rows,
        )
        _write_batched(
            stream,
            "categories",
            ("category_id", "public_id", "parent_category_id", "code", "name", "is_active", "created_at", "updated_at"),
            category_rows,
        )
        _write_batched(
            stream,
            "products",
            ("product_id", "public_id", "category_id", "slug", "name", "description", "image_url", "is_active", "created_at", "updated_at"),
            product_rows,
        )
        _write_batched(
            stream,
            "product_variants",
            ("variant_id", "public_id", "product_id", "sku", "size_code", "color_code", "price_vnd", "is_active", "created_at", "updated_at"),
            variant_rows,
        )
        _write_batched(
            stream,
            "wishlist_items",
            ("wishlist_item_id", "customer_id", "product_id", "is_present", "first_added_at", "last_added_at", "removed_at", "updated_at"),
            wishlist_rows,
        )

        cart_item_index = 0
        order_item_index = 0
        history_index = 0
        demo_order_target = min(24, order_count)
        failure_enabled = "failure_fixtures" in config.modes

        cart_rows: list[Sequence[SqlValue]] = []
        cart_item_rows: list[Sequence[SqlValue]] = []
        order_rows: list[Sequence[SqlValue]] = []
        order_item_rows: list[Sequence[SqlValue]] = []
        payment_rows: list[Sequence[SqlValue]] = []
        history_rows: list[Sequence[SqlValue]] = []

        def flush_orders() -> None:
            _write_insert(stream, "carts", ("cart_id", "public_id", "customer_id", "status", "created_at", "updated_at", "checked_out_at"), cart_rows)
            _write_insert(stream, "cart_items", ("cart_item_id", "cart_id", "variant_id", "quantity", "is_present", "first_added_at", "removed_at", "updated_at"), cart_item_rows)
            _write_insert(
                stream,
                "orders",
                (
                    "order_id", "order_number", "cart_id", "customer_id", "checkout_idempotency_key", "status",
                    "currency_code", "subtotal_vnd", "shipping_fee_vnd", "total_vnd", "receiver_name",
                    "receiver_phone", "shipping_address_text", "data_origin", "generation_run_id", "created_at",
                    "updated_at", "paid_at", "completed_at",
                ),
                order_rows,
            )
            _write_insert(
                stream,
                "order_items",
                (
                    "order_item_id", "order_id", "variant_id", "product_public_id_snapshot",
                    "category_code_snapshot", "category_name_snapshot", "product_name_snapshot", "sku_snapshot",
                    "size_code_snapshot", "color_code_snapshot", "unit_price_vnd", "quantity", "line_total_vnd", "created_at",
                ),
                order_item_rows,
            )
            _write_insert(
                stream,
                "payments",
                ("payment_id", "payment_reference", "order_id", "payment_idempotency_key", "status", "currency_code", "amount_vnd", "failure_code", "attempted_at", "created_at"),
                payment_rows,
            )
            _write_insert(
                stream,
                "order_status_history",
                ("order_status_history_id", "order_id", "from_status", "to_status", "transition_source", "reason", "transition_idempotency_key", "transitioned_at", "created_at"),
                history_rows,
            )
            cart_rows.clear()
            cart_item_rows.clear()
            order_rows.clear()
            order_item_rows.clear()
            payment_rows.clear()
            history_rows.clear()

        targets = _order_targets(assignment, class_by_name, demo_order_target, order_count, randomizer)
        order_index = 0
        for customer_index, order_target in enumerate(targets):
            if order_target <= 0:
                continue
            customer_id = customer_ids[customer_index]
            if customer_index == 0:
                span_seconds = max(1, int((history_end - history_start).total_seconds()))
                base_times = [
                    _shape_hour(
                        randomizer,
                        history_start + timedelta(seconds=span_seconds * (position + 1) // (order_target + 1)),
                        distribution.hour_of_day,
                    )
                    for position in range(order_target)
                ]
            else:
                class_ = class_by_name[assignment[customer_index]]
                base_times = [
                    _pick_base_datetime(
                        randomizer, history_start, history_end, days, day_weights, distribution.hour_of_day
                    )
                ]
                for position in range(1, order_target):
                    remaining_orders = order_target - position
                    available_days = max(0, (history_end - base_times[-1]).days)
                    interval_cap = available_days // max(1, remaining_orders)
                    interval = randomizer.randint(class_.interval_min or 1, class_.interval_max or 1)
                    next_base = min(base_times[-1] + timedelta(days=min(interval, interval_cap)), history_end)
                    base_times.append(
                        min(
                            _shape_hour(
                                randomizer,
                                next_base,
                                distribution.hour_of_day,
                            ),
                            history_end,
                        )
                    )

            for base_time in base_times:
                order_time = base_time
                cart_id = cart_base + order_index + 1
                order_id = order_base + order_index + 1
                cart_created_at = order_time - timedelta(minutes=randomizer.randint(5, 10_080))
                item_count = 1 + _weighted_index(randomizer, distribution.order_size)
                selected_variants = randomizer.sample(variant_records, min(item_count, variant_count))
                selected_variants.sort(key=lambda variant: variant.variant_id)

                item_details: list[tuple[VariantRecord, int, int]] = []
                subtotal_vnd = 0
                for variant in selected_variants:
                    quantity = 1 + _weighted_index(randomizer, distribution.quantity_per_item)
                    line_total_vnd = variant.price_vnd * quantity
                    subtotal_vnd += line_total_vnd
                    item_details.append((variant, quantity, line_total_vnd))
                shipping_fee_vnd = 0 if subtotal_vnd >= 500_000 else 30_000
                total_vnd = subtotal_vnd + shipping_fee_vnd

                failed = failure_enabled and randomizer.random() < 0.04
                can_complete = order_time <= history_end - timedelta(days=4)
                completed = not failed and can_complete and randomizer.random() < 0.78
                status = "payment_failed" if failed else "completed" if completed else "paid"
                paid_at = None if failed else order_time
                completed_at = None
                if completed:
                    completed_at = min(history_end - timedelta(minutes=1), order_time + timedelta(hours=randomizer.randint(24, 96)))
                updated_at = completed_at or order_time
                checkout_key = f"sql:{config.logical_identity}:{order_index + 1}:checkout"

                cart_rows.append(
                    (
                        cart_id,
                        _binary_uuid(_entity_uuid(namespace, "cart", order_index)),
                        customer_id,
                        "checked_out",
                        cart_created_at,
                        order_time,
                        order_time,
                    )
                )
                for variant, quantity, line_total_vnd in item_details:
                    cart_item_index += 1
                    cart_item_rows.append(
                        (
                            cart_item_base + cart_item_index,
                            cart_id,
                            variant.variant_id,
                            quantity,
                            True,
                            cart_created_at,
                            None,
                            order_time,
                        )
                    )
                    order_item_index += 1
                    order_item_rows.append(
                        (
                            order_item_base + order_item_index,
                            order_id,
                            variant.variant_id,
                            _binary_uuid(variant.product.public_id),
                            variant.product.category.code,
                            variant.product.category.name,
                            variant.product.name,
                            variant.sku,
                            variant.size_code,
                            variant.color_code,
                            variant.price_vnd,
                            quantity,
                            line_total_vnd,
                            order_time,
                        )
                    )
                    if not failed:
                        sold_quantities[variant.variant_id] += quantity
                        inventory_versions[variant.variant_id] += 1

                order_rows.append(
                    (
                        order_id,
                        f"SYN{config.logical_identity[:8].upper()}{order_index + 1:08d}",
                        cart_id,
                        customer_id,
                        checkout_key,
                        status,
                        "VND",
                        subtotal_vnd,
                        shipping_fee_vnd,
                        total_vnd,
                        f"Khách hàng tổng hợp {customer_index + 1:05d}",
                        f"09{(customer_index + 1) % 100_000_000:08d}",
                        f"Số {customer_index % 300 + 1}, đường Dữ Liệu, phường Mẫu, TP. Hồ Chí Minh",
                        "synthetic",
                        generation_run_id,
                        order_time,
                        updated_at,
                        paid_at,
                        completed_at,
                    )
                )
                payment_rows.append(
                    (
                        payment_base + order_index + 1,
                        f"PAYSYN{config.logical_identity[:8].upper()}{order_index + 1:08d}",
                        order_id,
                        f"{checkout_key}:pay",
                        "failed" if failed else "succeeded",
                        "VND",
                        total_vnd,
                        "SYNTHETIC_DECLINED" if failed else None,
                        order_time,
                        order_time,
                    )
                )
                history_index += 1
                history_rows.append(
                    (
                        history_base + history_index,
                        order_id,
                        None,
                        "payment_failed" if failed else "paid",
                        "generator",
                        "Synthetic failure fixture" if failed else None,
                        f"{checkout_key}:initial",
                        order_time,
                        order_time,
                    )
                )
                if completed and completed_at is not None:
                    history_index += 1
                    history_rows.append(
                        (
                            history_base + history_index,
                            order_id,
                            "paid",
                            "completed",
                            "generator",
                            None,
                            f"{checkout_key}:completed",
                            completed_at,
                            completed_at,
                        )
                    )

                order_index += 1
                if len(order_rows) >= INSERT_BATCH_SIZE:
                    flush_orders()

        flush_orders()

        active_cart_rows: list[Sequence[SqlValue]] = []
        active_cart_item_rows: list[Sequence[SqlValue]] = []
        active_cart_count = max(1, len(active_customer_indices) * 3 // 10)
        selected_active_customers = randomizer.sample(active_customer_indices, min(active_cart_count, len(active_customer_indices)))
        for active_cart_index, customer_index in enumerate(selected_active_customers):
            cart_id = cart_base + order_count + active_cart_index + 1
            is_abandoned = randomizer.random() < 0.65
            updated_at = history_end - (
                timedelta(days=randomizer.randint(2, 20))
                if is_abandoned
                else timedelta(hours=randomizer.randint(1, 12))
            )
            created_at = updated_at - timedelta(hours=randomizer.randint(1, 72))
            active_cart_rows.append(
                (
                    cart_id,
                    _binary_uuid(_entity_uuid(namespace, "active-cart", active_cart_index)),
                    customer_ids[customer_index],
                    "active",
                    created_at,
                    updated_at,
                    None,
                )
            )
            selected_variants = randomizer.sample(variant_records, randomizer.randint(1, min(3, variant_count)))
            for variant in sorted(selected_variants, key=lambda value: value.variant_id):
                cart_item_index += 1
                active_cart_item_rows.append(
                    (
                        cart_item_base + cart_item_index,
                        cart_id,
                        variant.variant_id,
                        randomizer.randint(1, 3),
                        True,
                        created_at,
                        None,
                        updated_at,
                    )
                )
        _write_batched(stream, "carts", ("cart_id", "public_id", "customer_id", "status", "created_at", "updated_at", "checked_out_at"), active_cart_rows)
        _write_batched(stream, "cart_items", ("cart_item_id", "cart_id", "variant_id", "quantity", "is_present", "first_added_at", "removed_at", "updated_at"), active_cart_item_rows)

        inventory_rows: list[Sequence[SqlValue]] = []
        for variant in variant_records:
            sold_quantity = sold_quantities[variant.variant_id]
            buffer_quantity = 80 + randomizer.randrange(0, 121)
            opening_on_hand = sold_quantity + buffer_quantity
            inventory_rows.append(
                (
                    variant.variant_id,
                    opening_on_hand,
                    opening_on_hand - sold_quantity,
                    inventory_versions[variant.variant_id],
                    history_end,
                )
            )
        _write_batched(
            stream,
            "inventory",
            ("variant_id", "opening_on_hand", "on_hand", "version", "updated_at"),
            inventory_rows,
        )

        stream.write(
            "COMMIT;\n\n"
            "-- Verification summary for the imported generation run.\n"
            f"SELECT '{generation_run_id}' AS generation_run_id,\n"
            f"       (SELECT COUNT(*) FROM customers WHERE generation_run_id = '{generation_run_id}') AS customers,\n"
            f"       (SELECT COUNT(*) FROM orders WHERE generation_run_id = '{generation_run_id}') AS orders;\n"
        )

    temporary_path.replace(output_path)

    return DatasetSummary(
        sql_path=output_path,
        generation_run_id=generation_run_id,
        demo_email=demo_email,
        demo_password=DEMO_PASSWORD,
        customers=customer_count,
        products=product_count,
        variants=variant_count,
        orders=order_count,
    )
