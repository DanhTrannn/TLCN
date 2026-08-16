import os
from dataclasses import dataclass
from pathlib import Path

import yaml

MUTABLE_CURSOR = "updated_at"
APPEND_ONLY_CURSOR = "created_at"
SILVER_PREFIX = "silver_"

MUTABLE_TABLES = frozenset({
    "customers",
    "categories",
    "products",
    "product_variants",
    "carts",
    "cart_items",
    "wishlist_items",
    "orders",
    "inventory",
    "coupons",
    "coupon_redemptions",
    "product_reviews",
})

APPEND_ONLY_TABLES = frozenset({
    "order_items",
    "payments",
    "order_status_history",
    "refunds",
})

KNOWN_TABLES = MUTABLE_TABLES | APPEND_ONLY_TABLES
EXPECTED_CURSOR = {
    name: (MUTABLE_CURSOR if name in MUTABLE_TABLES else APPEND_ONLY_CURSOR)
    for name in KNOWN_TABLES
}


class ConfigError(Exception):
    pass


@dataclass(frozen=True)
class RunSpec:
    data_interval_minutes: int
    retries: int
    quarantine_max_rows: int
    max_parallel_tables: int


@dataclass(frozen=True)
class LandingSpec:
    oltp_prefix: str
    log_prefix: str
    manifest_version: str


@dataclass(frozen=True)
class TableSpec:
    name: str
    cursor_field: str
    pk: str
    mutability: str
    silver_table: str
    pseudonymize: tuple[str, ...] = ()


@dataclass(frozen=True)
class Config:
    run: RunSpec
    landing: LandingSpec
    tables: tuple[TableSpec, ...]

    def table(self, name: str) -> TableSpec | None:
        for table in self.tables:
            if table.name == name:
                return table
        return None

    @property
    def bucket(self) -> str:
        return os.environ["MINIO_LAKEHOUSE_BUCKET"]

    @property
    def jdbc_url(self) -> str:
        from lakehouse.spark import jdbc_url
        return jdbc_url()


def config_path() -> Path:
    env_path = os.environ.get("PIPELINE_CONFIG_PATH")
    if env_path:
        return Path(env_path)
    return Path(__file__).resolve().parents[2] / "config" / "default.yml"


def _validate(config: Config) -> None:
    names = [table.name for table in config.tables]
    if len(names) != len(set(names)):
        raise ConfigError(f"duplicate table names: {names}")

    unknown = set(names) - KNOWN_TABLES
    if unknown:
        raise ConfigError(f"unknown tables in catalogue: {sorted(unknown)}")

    missing = KNOWN_TABLES - set(names)
    if missing:
        raise ConfigError(f"catalogue phải khai đủ {len(KNOWN_TABLES)} bảng, thiếu: {sorted(missing)}")

    for table in config.tables:
        if not table.pk:
            raise ConfigError(f"{table.name}: pk bắt buộc")
        if table.mutability not in ("mutable", "append_only"):
            raise ConfigError(f"{table.name}: mutability phải là mutable/append_only, được '{table.mutability}'")
        expected = EXPECTED_CURSOR[table.name]
        if table.cursor_field != expected:
            raise ConfigError(f"{table.name}: cursor_field phải là {expected} cho mutability={table.mutability}, được '{table.cursor_field}'")
        if not table.silver_table.startswith(SILVER_PREFIX):
            raise ConfigError(f"{table.name}: silver_table phải có tiền tố '{SILVER_PREFIX}', được '{table.silver_table}'")

    silver_names = [table.silver_table for table in config.tables]
    if len(silver_names) != len(set(silver_names)):
        raise ConfigError(f"silver_table bị trùng: {silver_names}")


def load_config(path: str | Path | None = None) -> Config:
    file_path = Path(path) if path else config_path()
    if not file_path.is_file():
        raise ConfigError(f"config not found: {file_path}")
    raw = yaml.safe_load(file_path.read_text(encoding="utf-8"))

    try:
        run = RunSpec(**raw["run"])
        landing = LandingSpec(**raw["landing"])
        tables = tuple(
            TableSpec(**{**entry, "pseudonymize": tuple(entry.get("pseudonymize", []))})
            for entry in raw["tables"]
        )
    except (KeyError, TypeError) as exc:
        raise ConfigError(f"cấu trúc {file_path.name} không hợp lệ: {exc}") from exc

    config = Config(run=run, landing=landing, tables=tables)
    _validate(config)
    return config
