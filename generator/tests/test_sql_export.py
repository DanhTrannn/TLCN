import hashlib
import re
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

from argon2 import PasswordHasher

from tlcn_generator.config import GeneratorConfig
from tlcn_generator.sql_export import DEMO_PASSWORD, export_sql


def _count_rows(sql: str, table: str) -> int:
    marker = f"INSERT INTO `{table}`"
    if marker not in sql:
        return 0
    start = sql.index(marker)
    end = sql.index("\n\n", start)
    block = sql[start:end]
    return block.count(",\n  (") + 1


class SqlExportTest(unittest.TestCase):
    def setUp(self) -> None:
        self.config = GeneratorConfig(
            scenario_id="unit-sql-v1",
            dataset_size="unit",
            seed=42,
            anchor_time=datetime(2026, 7, 1, tzinfo=UTC),
            history_months=12,
            modes=("seed_master", "historical_transactions", "repurchase_history", "failure_fixtures"),
            scale={"customers": 8, "products": 6, "variants": 18, "orders": 30},
        )

    def test_export_is_deterministic_and_complete(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            first_path = Path(temporary_directory) / "first.sql"
            second_path = Path(temporary_directory) / "second.sql"
            first_summary = export_sql(self.config, first_path)
            second_summary = export_sql(self.config, second_path)

            first_bytes = first_path.read_bytes()
            second_bytes = second_path.read_bytes()
            self.assertEqual(hashlib.sha256(first_bytes).digest(), hashlib.sha256(second_bytes).digest())
            self.assertEqual(first_summary.generation_run_id, second_summary.generation_run_id)

            sql = first_bytes.decode()
            for table in (
                "customers",
                "customer_credentials",
                "categories",
                "products",
                "product_variants",
                "wishlist_items",
                "carts",
                "cart_items",
                "orders",
                "order_items",
                "payments",
                "order_status_history",
                "inventory",
            ):
                self.assertIn(f"INSERT INTO `{table}`", sql)
            self.assertIn("START TRANSACTION;", sql)
            self.assertIn("COMMIT;", sql)
            self.assertNotIn("FOREIGN_KEY_CHECKS", sql)
            self.assertIn(first_summary.demo_email, sql)
            self.assertEqual(first_summary.demo_password, DEMO_PASSWORD)

            password_hash_start = sql.index("$argon2id$")
            password_hash_end = sql.index("'", password_hash_start)
            PasswordHasher().verify(sql[password_hash_start:password_hash_end], DEMO_PASSWORD)

    def test_rejects_invalid_variant_scale(self) -> None:
        invalid = GeneratorConfig(
            scenario_id="invalid",
            dataset_size="unit",
            seed=1,
            anchor_time=datetime(2026, 7, 1, tzinfo=UTC),
            history_months=1,
            modes=("seed_master",),
            scale={"customers": 2, "products": 4, "variants": 3, "orders": 0},
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            with self.assertRaisesRegex(ValueError, "variants must"):
                export_sql(invalid, Path(temporary_directory) / "invalid.sql")

    def test_variant_prices_within_band_union(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "prices.sql"
            export_sql(self.config, path)
            sql = path.read_text()
            marker = "INSERT INTO `product_variants`"
            start = sql.index(marker)
            end = sql.index("\n\n", start)
            block = sql[start:end]
            prices = re.findall(
                r"^\s+\(\d+, UNHEX\('[0-9a-f]+'\), \d+, '[^']+', '[^']+', '[^']+', (\d+),",
                block,
                re.MULTILINE,
            )
            self.assertEqual(len(prices), self.config.scale["variants"])
            for raw in prices:
                self.assertTrue(79000 <= int(raw) <= 2500000)

    def test_export_order_count_matches_scale(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "orders.sql"
            summary = export_sql(self.config, path)
            sql = path.read_text()
            self.assertEqual(_count_rows(sql, "orders"), summary.orders)

    def test_export_order_times_within_history(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "orders.sql"
            summary = export_sql(self.config, path)
            sql = path.read_text()
            marker = "INSERT INTO `orders`"
            start = sql.index(marker)
            end = sql.index("\n\n", start)
            block = sql[start:end]
            datetimes = re.findall(r"'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+)'", block)
            history_start = self.config.anchor_time - timedelta(days=12 * 30)
            history_end = self.config.anchor_time
            self.assertGreaterEqual(len(datetimes), summary.orders)
            for raw in datetimes:
                parsed = datetime.strptime(raw, "%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=UTC)
                self.assertGreaterEqual(parsed, history_start)
                self.assertLessEqual(parsed, history_end)

    def test_export_every_order_has_items(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "orders.sql"
            summary = export_sql(self.config, path)
            sql = path.read_text()
            marker = "INSERT INTO `order_items`"
            start = sql.index(marker)
            end = sql.index("\n\n", start)
            block = sql[start:end]
            order_ids = re.findall(r"^  \(\d+, (\d+),", block, re.MULTILINE)
            self.assertEqual(len(set(order_ids)), summary.orders)

    def test_export_evening_hour_share(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "orders.sql"
            summary = export_sql(self.config, path)
            sql = path.read_text()
            marker = "INSERT INTO `orders`"
            start = sql.index(marker)
            end = sql.index("\n\n", start)
            block = sql[start:end]
            hours = [int(raw[11:13]) for raw in re.findall(r"'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+)'", block)]
            evening = sum(1 for hour in hours if hour in (19, 20, 21, 22))
            self.assertGreater(evening / len(hours), 0.25)


if __name__ == "__main__":
    unittest.main()
