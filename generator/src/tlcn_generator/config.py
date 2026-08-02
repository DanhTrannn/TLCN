import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import yaml

from tlcn_generator import __version__


CATEGORY_NAMES = {
    "ao": "Áo nữ",
    "quan": "Quần nữ",
    "vay": "Váy",
    "dam": "Đầm",
    "khoac": "Áo khoác",
    "phu-kien": "Phụ kiện",
    "giay": "Giày dép",
    "tui-xach": "Túi xách",
}


@dataclass(frozen=True)
class TetWindow:
    month_start: int
    day_start: int
    month_end: int
    day_end: int
    peak: float


@dataclass(frozen=True)
class SaleEvent:
    name: str
    month: int
    boost: float
    after_days: int
    day: int | None = None
    weekday: int | None = None
    week_index: int | None = None


@dataclass(frozen=True)
class PriceBand:
    min_vnd: int
    max_vnd: int
    weight: int


@dataclass(frozen=True)
class CustomerClass:
    name: str
    share: float
    orders_min: int
    orders_max: int
    interval_min: int | None = None
    interval_max: int | None = None
    campaign_affinity: float = 0.4


@dataclass(frozen=True)
class CouponBehavior:
    base_usage_rate: float
    campaign_usage_rate: float
    midnight_usage_rate: float
    first_order_usage_rate: float
    customer_multipliers: tuple[tuple[str, float], ...]
    campaign_percentage_values: tuple[int, ...]
    midnight_fixed_values_vnd: tuple[int, ...]
    everyday_percentage: int
    welcome_fixed_vnd: int
    everyday_minimum_subtotal_vnd: int
    campaign_minimum_subtotal_vnd: int


@dataclass(frozen=True)
class ReviewBehavior:
    completed_order_rates: tuple[tuple[str, float], ...]
    rating_weights: tuple[int, ...]
    status_weights: tuple[tuple[str, int], ...]
    delay_days_min: int
    delay_days_max: int


@dataclass(frozen=True)
class CancellationBehavior:
    base_rate: float
    campaign_rate: float
    coupon_addon: float
    customer_addons: tuple[tuple[str, float], ...]
    reasons: tuple[tuple[str, float], ...]


@dataclass(frozen=True)
class DistributionConfig:
    business_timezone: str
    day_of_week: tuple[float, ...]
    hour_of_day: tuple[float, ...]
    campaign_hour_of_day: tuple[float, ...]
    tet: TetWindow
    sales: tuple[SaleEvent, ...]
    categories: tuple[tuple[str, float], ...]
    price_bands: tuple[PriceBand, ...]
    order_size: tuple[int, ...]
    quantity_per_item: tuple[int, ...]
    customer_classes: tuple[CustomerClass, ...]
    coupons: CouponBehavior
    reviews: ReviewBehavior
    cancellations: CancellationBehavior


_DOUBLE_DAY_SALES = tuple(
    SaleEvent(
        name=f"{month}-{month}",
        month=month,
        day=month,
        boost=4.8 if month in (9, 10, 11, 12) else 4.0,
        after_days=0,
    )
    for month in range(1, 13)
)

DEFAULT_DISTRIBUTIONS = DistributionConfig(
    business_timezone="Asia/Ho_Chi_Minh",
    day_of_week=(0.9, 0.95, 1.0, 1.05, 1.2, 1.5, 1.4),
    hour_of_day=(
        0.12, 0.04, 0.02, 0.02, 0.03, 0.05, 0.09, 0.14, 0.18, 0.20, 0.22, 0.30,
        0.38, 0.30, 0.24, 0.24, 0.27, 0.34, 0.50, 0.72, 0.95, 1.10, 1.00, 0.68,
    ),
    campaign_hour_of_day=(
        2.80, 1.20, 0.22, 0.08, 0.05, 0.06, 0.10, 0.16, 0.22, 0.28, 0.34, 0.55,
        1.35, 0.72, 0.36, 0.30, 0.36, 0.48, 0.72, 1.10, 1.65, 2.05, 1.80, 1.30,
    ),
    tet=TetWindow(month_start=1, day_start=25, month_end=2, day_end=18, peak=2.8),
    sales=_DOUBLE_DAY_SALES
    + (
        SaleEvent(
            name="black_friday",
            month=11,
            weekday=4,
            week_index=4,
            boost=3.2,
            after_days=2,
        ),
    ),
    categories=tuple(
        (code, float(weight))
        for code, weight in {
            "ao": 22,
            "dam": 18,
            "vay": 15,
            "quan": 14,
            "khoac": 12,
            "phu-kien": 9,
            "giay": 5,
            "tui-xach": 5,
        }.items()
    ),
    price_bands=(
        PriceBand(79_000, 199_000, 30),
        PriceBand(199_000, 399_000, 40),
        PriceBand(399_000, 699_000, 20),
        PriceBand(699_000, 2_500_000, 10),
    ),
    order_size=(55, 30, 12, 3),
    quantity_per_item=(70, 25, 5),
    customer_classes=(
        CustomerClass("loyal", 0.15, 4, 10, 20, 60, 0.72),
        CustomerClass("regular", 0.35, 2, 4, 45, 120, 0.48),
        CustomerClass("one_off", 0.50, 1, 1, campaign_affinity=0.38),
    ),
    coupons=CouponBehavior(
        base_usage_rate=0.14,
        campaign_usage_rate=0.64,
        midnight_usage_rate=0.82,
        first_order_usage_rate=0.42,
        customer_multipliers=(("loyal", 1.25), ("regular", 1.0), ("one_off", 0.8)),
        campaign_percentage_values=(10, 12, 15),
        midnight_fixed_values_vnd=(30_000, 50_000, 70_000),
        everyday_percentage=8,
        welcome_fixed_vnd=50_000,
        everyday_minimum_subtotal_vnd=299_000,
        campaign_minimum_subtotal_vnd=199_000,
    ),
    reviews=ReviewBehavior(
        completed_order_rates=(("loyal", 0.58), ("regular", 0.38), ("one_off", 0.24)),
        rating_weights=(2, 5, 13, 38, 42),
        status_weights=(("pending", 12), ("approved", 82), ("rejected", 6)),
        delay_days_min=1,
        delay_days_max=14,
    ),
    cancellations=CancellationBehavior(
        base_rate=0.035,
        campaign_rate=0.065,
        coupon_addon=0.012,
        customer_addons=(("loyal", -0.012), ("regular", 0.0), ("one_off", 0.018)),
        reasons=(
            ("Đặt nhầm size hoặc màu", 28),
            ("Muốn thay đổi địa chỉ nhận hàng", 18),
            ("Tìm thấy lựa chọn phù hợp hơn", 18),
            ("Áp nhầm mã giảm giá", 14),
            ("Không còn nhu cầu mua", 22),
        ),
    ),
)


def _parse_sale(raw_sale: dict[str, Any]) -> SaleEvent:
    return SaleEvent(
        name=str(raw_sale["name"]),
        month=int(raw_sale["month"]),
        day=int(raw_sale["day"]) if raw_sale.get("day") is not None else None,
        weekday=int(raw_sale["weekday"]) if raw_sale.get("weekday") is not None else None,
        week_index=int(raw_sale["week_index"]) if raw_sale.get("week_index") is not None else None,
        boost=float(raw_sale["boost"]),
        after_days=int(raw_sale["after_days"]),
    )


def _pairs(raw: dict[str, Any], cast: type = float) -> tuple[tuple[str, Any], ...]:
    return tuple((str(key), cast(value)) for key, value in raw.items())


def _parse_distributions(raw: dict[str, Any]) -> DistributionConfig:
    raw_seasonality = raw["seasonality"]
    raw_tet = raw_seasonality["tet"]
    raw_classes = raw["customers"]
    raw_coupons = raw.get("coupons")
    raw_reviews = raw.get("reviews")
    raw_cancellations = raw.get("cancellations")

    default_classes = {item.name: item for item in DEFAULT_DISTRIBUTIONS.customer_classes}
    coupons = DEFAULT_DISTRIBUTIONS.coupons
    if raw_coupons is not None:
        coupons = CouponBehavior(
            base_usage_rate=float(raw_coupons["base_usage_rate"]),
            campaign_usage_rate=float(raw_coupons["campaign_usage_rate"]),
            midnight_usage_rate=float(raw_coupons["midnight_usage_rate"]),
            first_order_usage_rate=float(raw_coupons["first_order_usage_rate"]),
            customer_multipliers=_pairs(raw_coupons["customer_multipliers"]),
            campaign_percentage_values=tuple(
                int(value) for value in raw_coupons["campaign_percentage_values"]
            ),
            midnight_fixed_values_vnd=tuple(
                int(value) for value in raw_coupons["midnight_fixed_values_vnd"]
            ),
            everyday_percentage=int(raw_coupons["everyday_percentage"]),
            welcome_fixed_vnd=int(raw_coupons["welcome_fixed_vnd"]),
            everyday_minimum_subtotal_vnd=int(
                raw_coupons["everyday_minimum_subtotal_vnd"]
            ),
            campaign_minimum_subtotal_vnd=int(
                raw_coupons["campaign_minimum_subtotal_vnd"]
            ),
        )

    reviews = DEFAULT_DISTRIBUTIONS.reviews
    if raw_reviews is not None:
        reviews = ReviewBehavior(
            completed_order_rates=_pairs(raw_reviews["completed_order_rates"]),
            rating_weights=tuple(int(value) for value in raw_reviews["rating_weights"]),
            status_weights=_pairs(raw_reviews["status_weights"], int),
            delay_days_min=int(raw_reviews["delay_days"][0]),
            delay_days_max=int(raw_reviews["delay_days"][1]),
        )

    cancellations = DEFAULT_DISTRIBUTIONS.cancellations
    if raw_cancellations is not None:
        cancellations = CancellationBehavior(
            base_rate=float(raw_cancellations["base_rate"]),
            campaign_rate=float(raw_cancellations["campaign_rate"]),
            coupon_addon=float(raw_cancellations["coupon_addon"]),
            customer_addons=_pairs(raw_cancellations["customer_addons"]),
            reasons=_pairs(raw_cancellations["reasons"]),
        )

    return DistributionConfig(
        business_timezone=str(
            raw.get("business_timezone", DEFAULT_DISTRIBUTIONS.business_timezone)
        ),
        day_of_week=tuple(float(value) for value in raw["day_of_week"]),
        hour_of_day=tuple(float(value) for value in raw["hour_of_day"]),
        campaign_hour_of_day=tuple(
            float(value)
            for value in raw.get(
                "campaign_hour_of_day", DEFAULT_DISTRIBUTIONS.campaign_hour_of_day
            )
        ),
        tet=TetWindow(
            month_start=int(raw_tet["month_start"]),
            day_start=int(raw_tet["day_start"]),
            month_end=int(raw_tet["month_end"]),
            day_end=int(raw_tet["day_end"]),
            peak=float(raw_tet["peak"]),
        ),
        sales=tuple(_parse_sale(item) for item in raw_seasonality["sales"]),
        categories=tuple(
            (str(code), float(weight)) for code, weight in raw["categories"].items()
        ),
        price_bands=tuple(
            PriceBand(
                min_vnd=int(band["min_vnd"]),
                max_vnd=int(band["max_vnd"]),
                weight=int(band["weight"]),
            )
            for band in raw["price_bands"]
        ),
        order_size=tuple(int(value) for value in raw["order_size"]),
        quantity_per_item=tuple(int(value) for value in raw["quantity_per_item"]),
        customer_classes=tuple(
            CustomerClass(
                name=str(name),
                share=float(class_["share"]),
                orders_min=int(class_["orders_per_year"][0]),
                orders_max=int(class_["orders_per_year"][1]),
                interval_min=(
                    int(class_["interval_days"][0]) if "interval_days" in class_ else None
                ),
                interval_max=(
                    int(class_["interval_days"][1]) if "interval_days" in class_ else None
                ),
                campaign_affinity=float(
                    class_.get(
                        "campaign_affinity",
                        default_classes.get(str(name), CustomerClass(str(name), 1, 1, 1)).campaign_affinity,
                    )
                ),
            )
            for name, class_ in raw_classes.items()
        ),
        coupons=coupons,
        reviews=reviews,
        cancellations=cancellations,
    )


def _validate_rate(value: float, label: str) -> None:
    if not 0 <= value <= 1:
        raise ValueError(f"{label} must be in 0..1")


def _validate_distributions(distributions: DistributionConfig) -> None:
    try:
        ZoneInfo(distributions.business_timezone)
    except ZoneInfoNotFoundError as error:
        raise ValueError("business_timezone must be a valid IANA timezone") from error

    if len(distributions.day_of_week) != 7 or any(
        weight <= 0 for weight in distributions.day_of_week
    ):
        raise ValueError("day_of_week must have exactly 7 positive values")
    for label, weights in (
        ("hour_of_day", distributions.hour_of_day),
        ("campaign_hour_of_day", distributions.campaign_hour_of_day),
    ):
        if len(weights) != 24 or any(weight < 0 for weight in weights) or sum(weights) <= 0:
            raise ValueError(f"{label} must have exactly 24 non-negative values with positive sum")

    tet = distributions.tet
    if not (1 <= tet.month_start <= 12 and 1 <= tet.month_end <= 12):
        raise ValueError("tet months must be in 1..12")
    if not (1 <= tet.day_start <= 31 and 1 <= tet.day_end <= 31):
        raise ValueError("tet days must be in 1..31")
    if tet.peak <= 1:
        raise ValueError("tet peak must be greater than 1")

    codes = {code for code, _ in distributions.categories}
    if codes != set(CATEGORY_NAMES):
        raise ValueError(f"categories must cover exactly {sorted(CATEGORY_NAMES)}")
    if any(weight <= 0 for _, weight in distributions.categories):
        raise ValueError("category weights must be positive")
    if not distributions.price_bands:
        raise ValueError("price_bands must not be empty")
    for band in distributions.price_bands:
        if band.min_vnd < 0 or band.min_vnd > band.max_vnd or band.weight <= 0:
            raise ValueError("price band must satisfy 0 <= min <= max and positive weight")
    if sum(distributions.order_size) != 100 or any(
        value < 0 for value in distributions.order_size
    ):
        raise ValueError("order_size must sum to 100")
    if sum(distributions.quantity_per_item) != 100 or any(
        value < 0 for value in distributions.quantity_per_item
    ):
        raise ValueError("quantity_per_item must sum to 100")

    classes = distributions.customer_classes
    if not classes:
        raise ValueError("customer_classes must not be empty")
    class_names = {item.name for item in classes}
    if abs(sum(item.share for item in classes) - 1.0) > 1e-6 or any(
        item.share <= 0 for item in classes
    ):
        raise ValueError("customer class shares must be positive and sum to 1")
    for item in classes:
        if item.orders_min < 1 or item.orders_min > item.orders_max:
            raise ValueError(f"customer class {item.name} has invalid orders range")
        _validate_rate(item.campaign_affinity, f"customer class {item.name} campaign_affinity")
        if item.orders_max > 1:
            if item.interval_min is None or item.interval_max is None:
                raise ValueError(f"customer class {item.name} needs interval range")
            if item.interval_min < 1 or item.interval_min > item.interval_max:
                raise ValueError(f"customer class {item.name} has invalid interval range")

    for event in distributions.sales:
        if not (1 <= event.month <= 12):
            raise ValueError(f"sale {event.name} month must be in 1..12")
        if event.day is None and (event.weekday is None or event.week_index is None):
            raise ValueError(f"sale {event.name} must define day or weekday+week_index")
        if event.day is not None and not (1 <= event.day <= 31):
            raise ValueError(f"sale {event.name} day must be in 1..31")
        if event.boost <= 1:
            raise ValueError(f"sale {event.name} boost must be greater than 1")
        if event.after_days < 0:
            raise ValueError(f"sale {event.name} after_days must be >= 0")

    coupon = distributions.coupons
    for label, value in (
        ("coupons.base_usage_rate", coupon.base_usage_rate),
        ("coupons.campaign_usage_rate", coupon.campaign_usage_rate),
        ("coupons.midnight_usage_rate", coupon.midnight_usage_rate),
        ("coupons.first_order_usage_rate", coupon.first_order_usage_rate),
    ):
        _validate_rate(value, label)
    if {name for name, _ in coupon.customer_multipliers} != class_names:
        raise ValueError("coupon customer_multipliers must match customer classes")
    if any(value <= 0 for _, value in coupon.customer_multipliers):
        raise ValueError("coupon customer_multipliers must be positive")
    if not coupon.campaign_percentage_values or any(
        not 1 <= value <= 100 for value in coupon.campaign_percentage_values
    ):
        raise ValueError("campaign percentage values must be in 1..100")
    if not coupon.midnight_fixed_values_vnd or any(
        value <= 0 for value in coupon.midnight_fixed_values_vnd
    ):
        raise ValueError("midnight fixed values must be positive")
    if not 1 <= coupon.everyday_percentage <= 100 or coupon.welcome_fixed_vnd <= 0:
        raise ValueError("everyday/welcome coupon values are invalid")

    review = distributions.reviews
    if {name for name, _ in review.completed_order_rates} != class_names:
        raise ValueError("review completed_order_rates must match customer classes")
    for name, value in review.completed_order_rates:
        _validate_rate(value, f"review rate {name}")
    if len(review.rating_weights) != 5 or any(value < 0 for value in review.rating_weights):
        raise ValueError("review rating_weights must contain five non-negative values")
    if {name for name, _ in review.status_weights} != {"pending", "approved", "rejected"}:
        raise ValueError("review status_weights must contain pending/approved/rejected")
    if any(value < 0 for _, value in review.status_weights):
        raise ValueError("review status weights must be non-negative")
    if review.delay_days_min < 0 or review.delay_days_min > review.delay_days_max:
        raise ValueError("review delay_days is invalid")

    cancellation = distributions.cancellations
    for label, value in (
        ("cancellations.base_rate", cancellation.base_rate),
        ("cancellations.campaign_rate", cancellation.campaign_rate),
    ):
        _validate_rate(value, label)
    if cancellation.coupon_addon < 0:
        raise ValueError("cancellation coupon_addon must be non-negative")
    if {name for name, _ in cancellation.customer_addons} != class_names:
        raise ValueError("cancellation customer_addons must match customer classes")
    if not cancellation.reasons or any(weight <= 0 for _, weight in cancellation.reasons):
        raise ValueError("cancellation reasons must have positive weights")


@dataclass(frozen=True)
class GeneratorConfig:
    scenario_id: str
    dataset_size: str
    seed: int
    anchor_time: datetime
    history_months: int
    modes: tuple[str, ...]
    scale: dict[str, int]
    distributions: DistributionConfig = DEFAULT_DISTRIBUTIONS

    @property
    def logical_identity(self) -> str:
        payload = json.dumps(
            {
                "generator_version": __version__,
                "scenario_id": self.scenario_id,
                "dataset_size": self.dataset_size,
                "seed": self.seed,
                "anchor_time": self.anchor_time.isoformat(),
                "history_months": self.history_months,
                "modes": self.modes,
                "scale": self.scale,
                "distributions": asdict(self.distributions),
            },
            sort_keys=True,
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def load_config(path: Path) -> GeneratorConfig:
    raw: dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8"))
    anchor_time = datetime.fromisoformat(str(raw["anchor_time"]).replace("Z", "+00:00"))
    if anchor_time.tzinfo is None:
        raise ValueError("anchor_time must include timezone")
    distributions = DEFAULT_DISTRIBUTIONS
    if "distributions" in raw:
        distributions = _parse_distributions(raw["distributions"])
    _validate_distributions(distributions)
    return GeneratorConfig(
        scenario_id=str(raw["scenario_id"]),
        dataset_size=str(raw["dataset_size"]),
        seed=int(raw["seed"]),
        anchor_time=anchor_time,
        history_months=int(raw["history_months"]),
        modes=tuple(str(mode) for mode in raw["modes"]),
        scale={str(key): int(value) for key, value in raw["scale"].items()},
        distributions=distributions,
    )
