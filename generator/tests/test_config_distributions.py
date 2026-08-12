import tempfile
import unittest
from pathlib import Path
from uuid import UUID

import yaml

from generator.config import DEFAULT_DISTRIBUTIONS, load_config


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
        "business_timezone": "Asia/Ho_Chi_Minh",
        "day_of_week": [1.0] * 7,
        "hour_of_day": [0.1] * 24,
        "campaign_hour_of_day": [0.2] * 24,
        "seasonality": {
            "tet": {"month_start": 1, "day_start": 25, "month_end": 2, "day_end": 18, "peak": 2.5},
            "sales": [],
        },
        "categories": {code: 1.0 for code in ("ao", "quan", "vay", "dam", "khoac", "phu-kien", "giay", "tui-xach")},
        "price_bands": [{"min_vnd": 50000, "max_vnd": 100000, "weight": 1}],
        "order_size": [60, 30, 10, 0],
        "quantity_per_item": [80, 20, 0],
        "customers": {
            "loyal": {
                "share": 0.2,
                "orders_per_year": [3, 5],
                "interval_days": [20, 40],
                "campaign_affinity": 0.8,
            },
            "regular": {
                "share": 0.3,
                "orders_per_year": [2, 3],
                "interval_days": [50, 100],
                "campaign_affinity": 0.5,
            },
            "one_off": {
                "share": 0.5,
                "orders_per_year": [1, 1],
                "campaign_affinity": 0.3,
            },
        },
        "coupons": {
            "base_usage_rate": 0.1,
            "campaign_usage_rate": 0.6,
            "midnight_usage_rate": 0.8,
            "first_order_usage_rate": 0.4,
            "customer_multipliers": {"loyal": 1.2, "regular": 1.0, "one_off": 0.8},
            "campaign_percentage_values": [10, 15],
            "midnight_fixed_values_vnd": [30000, 50000],
            "everyday_percentage": 8,
            "welcome_fixed_vnd": 50000,
            "everyday_minimum_subtotal_vnd": 299000,
            "campaign_minimum_subtotal_vnd": 199000,
        },
        "reviews": {
            "completed_order_rates": {"loyal": 0.6, "regular": 0.4, "one_off": 0.2},
            "rating_weights": [2, 5, 13, 38, 42],
            "status_weights": {"approved": 94, "rejected": 6},
            "delay_days": [1, 14],
        },
        "cancellations": {
            "base_rate": 0.03,
            "campaign_rate": 0.06,
            "coupon_addon": 0.01,
            "customer_addons": {"loyal": -0.01, "regular": 0.0, "one_off": 0.02},
            "reasons": {"Đặt nhầm size": 2, "Không còn nhu cầu": 1},
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
        self.assertEqual(config.distributions.business_timezone, "Asia/Ho_Chi_Minh")
        self.assertEqual(config.distributions.categories[0], ("ao", 1.0))
        self.assertEqual(config.distributions.order_size, (60, 30, 10, 0))
        self.assertEqual(config.distributions.customer_classes[-1].orders_max, 1)
        self.assertEqual(config.distributions.customer_classes[-1].interval_min, None)
        self.assertEqual(config.distributions.customer_classes[0].campaign_affinity, 0.8)
        self.assertEqual(config.distributions.campaign_hour_of_day, (0.2,) * 24)
        self.assertEqual(config.distributions.coupons.midnight_usage_rate, 0.8)
        self.assertEqual(config.distributions.reviews.rating_weights, (2, 5, 13, 38, 42))
        self.assertEqual(config.distributions.cancellations.reasons[0][0], "Đặt nhầm size")

    def test_logical_identity_changes_with_distributions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = load_config(_write_yaml(Path(directory) / "base.yml", _base_body()))
            body = _base_body()
            body["distributions"] = _valid_distributions()
            changed = load_config(_write_yaml(Path(directory) / "changed.yml", body))
        self.assertNotEqual(base.logical_identity, changed.logical_identity)
        self.assertEqual(str(UUID(base.logical_identity)), base.logical_identity)
        self.assertEqual(str(UUID(base.generation_run_id)), base.generation_run_id)

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

    def test_rejects_tet_peak_of_one(self) -> None:
        body = _base_body()
        body["distributions"] = _valid_distributions()
        body["distributions"]["seasonality"]["tet"]["peak"] = 1
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "peak"):
                load_config(_write_yaml(Path(directory) / "bad.yml", body))

    def test_rejects_empty_price_bands(self) -> None:
        body = _base_body()
        body["distributions"] = _valid_distributions()
        body["distributions"]["price_bands"] = []
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "price_bands"):
                load_config(_write_yaml(Path(directory) / "bad.yml", body))

    def test_rejects_quantity_per_item_sum_not_100(self) -> None:
        body = _base_body()
        body["distributions"] = _valid_distributions()
        body["distributions"]["quantity_per_item"] = [70, 20, 0]
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "quantity_per_item"):
                load_config(_write_yaml(Path(directory) / "bad.yml", body))

    def test_rejects_sale_weekday_without_week_index(self) -> None:
        body = _base_body()
        body["distributions"] = _valid_distributions()
        body["distributions"]["seasonality"]["sales"] = [
            {"name": "bf", "month": 11, "weekday": 4, "boost": 2.0, "after_days": 1}
        ]
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "week_index"):
                load_config(_write_yaml(Path(directory) / "bad.yml", body))

    def test_accepts_null_day_with_weekday_and_week_index(self) -> None:
        body = _base_body()
        body["distributions"] = _valid_distributions()
        body["distributions"]["seasonality"]["sales"] = [
            {"name": "bf", "month": 11, "day": None, "weekday": 4, "week_index": 4, "boost": 2.0, "after_days": 1}
        ]
        with tempfile.TemporaryDirectory() as directory:
            config = load_config(_write_yaml(Path(directory) / "ok.yml", body))
        sale = config.distributions.sales[0]
        self.assertIsNone(sale.day)
        self.assertEqual(sale.weekday, 4)
        self.assertEqual(sale.week_index, 4)

    def test_rejects_null_day_without_weekday(self) -> None:
        body = _base_body()
        body["distributions"] = _valid_distributions()
        body["distributions"]["seasonality"]["sales"] = [
            {"name": "x", "month": 11, "day": None, "boost": 2.0, "after_days": 1}
        ]
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "day or weekday"):
                load_config(_write_yaml(Path(directory) / "bad.yml", body))

    def test_rejects_wrong_campaign_hour_count(self) -> None:
        body = _base_body()
        body["distributions"] = _valid_distributions()
        body["distributions"]["campaign_hour_of_day"] = [0.2] * 23
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "campaign_hour_of_day"):
                load_config(_write_yaml(Path(directory) / "bad.yml", body))

    def test_rejects_invalid_review_rating_weights(self) -> None:
        body = _base_body()
        body["distributions"] = _valid_distributions()
        body["distributions"]["reviews"]["rating_weights"] = [10, 20, 30, 40]
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "rating_weights"):
                load_config(_write_yaml(Path(directory) / "bad.yml", body))

    def test_rejects_pending_review_status(self) -> None:
        body = _base_body()
        body["distributions"] = _valid_distributions()
        body["distributions"]["reviews"]["status_weights"] = {
            "pending": 10,
            "approved": 84,
            "rejected": 6,
        }
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "approved/rejected"):
                load_config(_write_yaml(Path(directory) / "bad.yml", body))

    def test_rejects_coupon_segments_not_matching_customer_classes(self) -> None:
        body = _base_body()
        body["distributions"] = _valid_distributions()
        del body["distributions"]["coupons"]["customer_multipliers"]["loyal"]
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "customer_multipliers"):
                load_config(_write_yaml(Path(directory) / "bad.yml", body))

    def test_rejects_invalid_business_timezone(self) -> None:
        body = _base_body()
        body["distributions"] = _valid_distributions()
        body["distributions"]["business_timezone"] = "Vietnam/Invalid"
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "business_timezone"):
                load_config(_write_yaml(Path(directory) / "bad.yml", body))


if __name__ == "__main__":
    unittest.main()
