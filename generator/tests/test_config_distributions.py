import tempfile
import unittest
from pathlib import Path

import yaml

from tlcn_generator.config import DEFAULT_DISTRIBUTIONS, load_config


def _write_yaml(path: Path, body: dict) -> Path:
    path.write_text(yaml.safe_dump(body, sort_keys=False), encoding="utf-8")
    return path


def _base_body() -> dict:
    return {
        "scenario_id": "dist-test-v1",
        "dataset_size": "unit",
        "seed": 7,
        "anchor_time": "2026-07-01T00:00:00+00:00",
        "history_months": 12,
        "modes": ["seed_master"],
        "scale": {"customers": 10, "products": 5, "variants": 10, "orders": 20},
    }


def _valid_distributions() -> dict:
    return {
        "day_of_week": [1.0] * 7,
        "hour_of_day": [0.1] * 24,
        "seasonality": {
            "tet": {"month_start": 1, "day_start": 25, "month_end": 2, "day_end": 18, "peak": 2.5},
            "sales": [],
        },
        "categories": {code: 1.0 for code in ("ao", "quan", "vay", "dam", "khoac", "phu-kien", "giay", "tui-xach")},
        "price_bands": [{"min_vnd": 50000, "max_vnd": 100000, "weight": 1}],
        "order_size": [60, 30, 10, 0],
        "quantity_per_item": [80, 20, 0],
        "customers": {
            "loyal": {"share": 0.2, "orders_per_year": [3, 5], "interval_days": [20, 40]},
            "regular": {"share": 0.3, "orders_per_year": [2, 3], "interval_days": [50, 100]},
            "one_off": {"share": 0.5, "orders_per_year": [1, 1]},
        },
    }


class LoadConfigDistributionTest(unittest.TestCase):
    def test_defaults_when_distributions_missing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config = load_config(_write_yaml(Path(directory) / "config.yml", _base_body()))
        self.assertEqual(config.distributions, DEFAULT_DISTRIBUTIONS)

    def test_parses_distributions(self) -> None:
        body = _base_body()
        body["distributions"] = _valid_distributions()
        with tempfile.TemporaryDirectory() as directory:
            config = load_config(_write_yaml(Path(directory) / "config.yml", body))
        self.assertEqual(config.distributions.categories[0], ("ao", 1.0))
        self.assertEqual(config.distributions.order_size, (60, 30, 10, 0))
        self.assertEqual(config.distributions.customer_classes[-1].orders_max, 1)
        self.assertEqual(config.distributions.customer_classes[-1].interval_min, None)

    def test_logical_identity_changes_with_distributions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = load_config(_write_yaml(Path(directory) / "base.yml", _base_body()))
            body = _base_body()
            body["distributions"] = _valid_distributions()
            changed = load_config(_write_yaml(Path(directory) / "changed.yml", body))
        self.assertNotEqual(base.logical_identity, changed.logical_identity)

    def test_rejects_invalid_order_size_sum(self) -> None:
        body = _base_body()
        body["distributions"] = _valid_distributions()
        body["distributions"]["order_size"] = [50, 20, 10, 5]
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "order_size"):
                load_config(_write_yaml(Path(directory) / "bad.yml", body))

    def test_rejects_invalid_share_sum(self) -> None:
        body = _base_body()
        body["distributions"] = _valid_distributions()
        body["distributions"]["customers"]["one_off"]["share"] = 0.3
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "shares"):
                load_config(_write_yaml(Path(directory) / "bad.yml", body))

    def test_rejects_wrong_hour_count(self) -> None:
        body = _base_body()
        body["distributions"] = _valid_distributions()
        body["distributions"]["hour_of_day"] = [0.1] * 23
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "hour_of_day"):
                load_config(_write_yaml(Path(directory) / "bad.yml", body))

    def test_rejects_missing_category_code(self) -> None:
        body = _base_body()
        body["distributions"] = _valid_distributions()
        del body["distributions"]["categories"]["ao"]
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "categories"):
                load_config(_write_yaml(Path(directory) / "bad.yml", body))

    def test_rejects_sale_without_date(self) -> None:
        body = _base_body()
        body["distributions"] = _valid_distributions()
        body["distributions"]["seasonality"]["sales"] = [{"name": "x", "month": 11, "boost": 2.0, "after_days": 1}]
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "day or weekday"):
                load_config(_write_yaml(Path(directory) / "bad.yml", body))


if __name__ == "__main__":
    unittest.main()
