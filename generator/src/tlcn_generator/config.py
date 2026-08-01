import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


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


@dataclass(frozen=True)
class DistributionConfig:
    day_of_week: tuple[float, ...]
    hour_of_day: tuple[float, ...]
    tet: TetWindow
    sales: tuple[SaleEvent, ...]
    categories: tuple[tuple[str, float], ...]
    price_bands: tuple[PriceBand, ...]
    order_size: tuple[int, ...]
    quantity_per_item: tuple[int, ...]
    customer_classes: tuple[CustomerClass, ...]


DEFAULT_DISTRIBUTIONS = DistributionConfig(
    day_of_week=(0.9, 0.95, 1.0, 1.05, 1.2, 1.5, 1.4),
    hour_of_day=(
        0.05, 0.02, 0.02, 0.02, 0.03, 0.05, 0.09, 0.14, 0.18, 0.20, 0.22, 0.26,
        0.28, 0.26, 0.24, 0.24, 0.27, 0.34, 0.50, 0.72, 0.95, 1.10, 1.00, 0.60,
    ),
    tet=TetWindow(month_start=1, day_start=25, month_end=2, day_end=18, peak=2.8),
    sales=(
        SaleEvent(name="11-11", month=11, day=11, boost=2.5, after_days=4),
        SaleEvent(name="12-12", month=12, day=12, boost=2.5, after_days=4),
        SaleEvent(name="6-6", month=6, day=6, boost=2.2, after_days=3),
        SaleEvent(name="black_friday", month=11, weekday=4, week_index=4, boost=2.2, after_days=3),
    ),
    categories=tuple(
        (code, float(weight))
        for code, weight in {
            "ao": 22, "dam": 18, "vay": 15, "quan": 14, "khoac": 12,
            "phu-kien": 9, "giay": 5, "tui-xach": 5,
        }.items()
    ),
    price_bands=(
        PriceBand(79000, 199000, 30),
        PriceBand(199000, 399000, 40),
        PriceBand(399000, 699000, 20),
        PriceBand(699000, 2500000, 10),
    ),
    order_size=(55, 30, 12, 3),
    quantity_per_item=(70, 25, 5),
    customer_classes=(
        CustomerClass("loyal", 0.15, 4, 10, 20, 60),
        CustomerClass("regular", 0.35, 2, 4, 45, 120),
        CustomerClass("one_off", 0.50, 1, 1),
    ),
)


def _parse_sale(raw_sale: dict[str, Any]) -> SaleEvent:
    return SaleEvent(
        name=str(raw_sale["name"]),
        month=int(raw_sale["month"]),
        day=int(raw_sale["day"]) if "day" in raw_sale else None,
        weekday=int(raw_sale["weekday"]) if "weekday" in raw_sale else None,
        week_index=int(raw_sale["week_index"]) if "week_index" in raw_sale else None,
        boost=float(raw_sale["boost"]),
        after_days=int(raw_sale["after_days"]),
    )


def _parse_distributions(raw: dict[str, Any]) -> DistributionConfig:
    raw_seasonality = raw["seasonality"]
    raw_tet = raw_seasonality["tet"]
    raw_sales = raw_seasonality["sales"]
    raw_categories = raw["categories"]
    raw_bands = raw["price_bands"]
    raw_classes = raw["customers"]
    return DistributionConfig(
        day_of_week=tuple(float(value) for value in raw["day_of_week"]),
        hour_of_day=tuple(float(value) for value in raw["hour_of_day"]),
        tet=TetWindow(
            month_start=int(raw_tet["month_start"]),
            day_start=int(raw_tet["day_start"]),
            month_end=int(raw_tet["month_end"]),
            day_end=int(raw_tet["day_end"]),
            peak=float(raw_tet["peak"]),
        ),
        sales=tuple(_parse_sale(raw_sale) for raw_sale in raw_sales),
        categories=tuple((str(code), float(weight)) for code, weight in raw_categories.items()),
        price_bands=tuple(
            PriceBand(
                min_vnd=int(band["min_vnd"]),
                max_vnd=int(band["max_vnd"]),
                weight=int(band["weight"]),
            )
            for band in raw_bands
        ),
        order_size=tuple(int(value) for value in raw["order_size"]),
        quantity_per_item=tuple(int(value) for value in raw["quantity_per_item"]),
        customer_classes=tuple(
            CustomerClass(
                name=str(name),
                share=float(class_["share"]),
                orders_min=int(class_["orders_per_year"][0]),
                orders_max=int(class_["orders_per_year"][1]),
                interval_min=int(class_["interval_days"][0]) if "interval_days" in class_ else None,
                interval_max=int(class_["interval_days"][1]) if "interval_days" in class_ else None,
            )
            for name, class_ in raw_classes.items()
        ),
    )


def _validate_distributions(distributions: DistributionConfig) -> None:
    if len(distributions.day_of_week) != 7 or any(weight <= 0 for weight in distributions.day_of_week):
        raise ValueError("day_of_week must have exactly 7 positive values")
    if len(distributions.hour_of_day) != 24 or any(weight < 0 for weight in distributions.hour_of_day):
        raise ValueError("hour_of_day must have exactly 24 non-negative values")
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
    if sum(distributions.order_size) != 100 or any(value < 0 for value in distributions.order_size):
        raise ValueError("order_size must sum to 100")
    if sum(distributions.quantity_per_item) != 100 or any(value < 0 for value in distributions.quantity_per_item):
        raise ValueError("quantity_per_item must sum to 100")
    classes = distributions.customer_classes
    if not classes:
        raise ValueError("customer_classes must not be empty")
    if abs(sum(class_.share for class_ in classes) - 1.0) > 1e-6 or any(class_.share <= 0 for class_ in classes):
        raise ValueError("customer class shares must be positive and sum to 1")
    for class_ in classes:
        if class_.orders_min < 1 or class_.orders_min > class_.orders_max:
            raise ValueError(f"customer class {class_.name} has invalid orders range")
        if class_.orders_max > 1:
            if class_.interval_min is None or class_.interval_max is None:
                raise ValueError(f"customer class {class_.name} needs interval range")
            if class_.interval_min < 1 or class_.interval_min > class_.interval_max:
                raise ValueError(f"customer class {class_.name} has invalid interval range")
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
