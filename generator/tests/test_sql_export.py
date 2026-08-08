import hashlib
import re
import tempfile
import unittest
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from argon2 import PasswordHasher

from generator.config import DEFAULT_DISTRIBUTIONS, GeneratorConfig, PriceBand
from generator.sql_export import DEMO_PASSWORD, PRODUCT_IMAGE_URL, export_sql


def _table_blocks(sql: str, table: str) -> list[str]:
    return re.findall(rf"INSERT INTO `{table}` .*?;\n\n", sql, re.DOTALL)


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
            modes=("seed_master", "historical_transactions", "repurchase_history"),
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
                "coupons",
                "wishlist_items",
                "carts",
                "cart_items",
                "orders",
                "order_items",
                "payments",
                "order_status_history",
                "coupon_redemptions",
                "refunds",
                "product_reviews",
                "inventory",
            ):
                self.assertIn(f"INSERT INTO `{table}`", sql)
            self.assertIn("START TRANSACTION;", sql)
            self.assertIn("COMMIT;", sql)
            self.assertNotIn("FOREIGN_KEY_CHECKS", sql)
            self.assertIn(first_summary.demo_email, sql)
            self.assertEqual(first_summary.demo_password, DEMO_PASSWORD)
            self.assertNotIn("payment_failed", sql)
            self.assertNotIn("SYNTHETIC_DECLINED", sql)
            self.assertNotIn("Sản phẩm tổng hợp", sql)
            self.assertIn("D&K", sql)
            self.assertEqual(sql.count(PRODUCT_IMAGE_URL), self.config.scale["products"])
            self.assertRegex(sql, r"DK-(AO|QU|CV|DM|AK|PK|GI|TX)-\d{5}")

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

    def test_variant_prices_stay_within_single_narrow_band(self) -> None:
        narrow = replace(DEFAULT_DISTRIBUTIONS, price_bands=(PriceBand(100_000, 150_000, 1),))
        config = replace(self.config, distributions=narrow)
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "narrow.sql"
            export_sql(config, path)
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
            self.assertEqual(len(prices), config.scale["variants"])
            for raw in prices:
                self.assertTrue(100_000 <= int(raw) <= 150_000)

    def test_export_order_count_matches_scale(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "orders.sql"
            summary = export_sql(self.config, path)
            sql = path.read_text()
            self.assertEqual(_count_rows(sql, "orders"), summary.orders)

    def test_export_order_times_within_history(self) -> None:
        for seed in range(60):
            with tempfile.TemporaryDirectory() as temporary_directory:
                config = replace(self.config, seed=seed)
                path = Path(temporary_directory) / "orders.sql"
                summary = export_sql(config, path)
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
            order_ids = re.findall(r"^  \(\d+, UNHEX\('[^']+'\), (\d+),", block, re.MULTILINE)
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
            created_times = re.findall(
                r"'synthetic', 'sql-[^']+', '(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+)'",
                block,
            )
            business_zone = ZoneInfo(DEFAULT_DISTRIBUTIONS.business_timezone)
            hours = [
                datetime.strptime(raw, "%Y-%m-%d %H:%M:%S.%f")
                .replace(tzinfo=UTC)
                .astimezone(business_zone)
                .hour
                for raw in created_times
            ]
            evening = sum(1 for hour in hours if hour in (19, 20, 21, 22))
            self.assertEqual(len(hours), summary.orders)
            self.assertGreater(evening / len(hours), 0.25)

    def test_export_contains_vietnamese_marketplace_signals(self) -> None:
        config = replace(
            self.config,
            scale={"customers": 120, "products": 40, "variants": 120, "orders": 800},
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "vn-marketplace.sql"
            export_sql(config, path)
            sql = path.read_text(encoding="utf-8")

            coupon_start = sql.index("INSERT INTO `coupons`")
            coupon_end = sql.index("\n\n", coupon_start)
            coupon_block = sql[coupon_start:coupon_end]
            self.assertEqual(_count_rows(sql, "coupons"), 28)
            self.assertIn("'percentage'", coupon_block)
            self.assertIn("'fixed_amount'", coupon_block)
            self.assertIn("SALE1111", coupon_block)
            self.assertIn("0H1111", coupon_block)
            self.assertIn("'2025-11-10 17:00:00.000000'", coupon_block)

            self.assertGreater(_count_rows(sql, "coupon_redemptions"), 100)
            self.assertGreater(_count_rows(sql, "product_reviews"), 200)
            review_start = sql.index("INSERT INTO `product_reviews`")
            review_end = sql.index("\n\n", review_start)
            review_block = sql[review_start:review_end]
            for status in ("pending", "approved", "rejected"):
                self.assertIn(f"'{status}'", review_block)
            self.assertIn("Mua ", review_block)

            self.assertIn("Đặt nhầm size hoặc màu", sql)
            self.assertIn("Áp nhầm mã giảm giá", sql)
            self.assertIn("Không còn nhu cầu mua", sql)

            variants: dict[int, int] = {}
            for block in _table_blocks(sql, "product_variants"):
                variants.update(
                    {
                        int(variant_id): int(product_id)
                        for variant_id, product_id in re.findall(
                            r"^  \((\d+), UNHEX\('[0-9a-f]+'\), (\d+),",
                            block,
                            re.MULTILINE,
                        )
                    }
                )
            successful_orders: dict[int, tuple[int, str]] = {}
            for block in _table_blocks(sql, "orders"):
                for order_id, customer_id, status, created_at in re.findall(
                    r"^  \((\d+), '[^']+', \d+, (\d+), '[^']+', '([^']+)'.*?"
                    r"'synthetic', 'sql-[^']+', '([^']+)'",
                    block,
                    re.MULTILINE,
                ):
                    if status != "cancelled":
                        successful_orders[int(order_id)] = (int(customer_id), created_at)
            purchases: set[tuple[int, int, str]] = set()
            for block in _table_blocks(sql, "order_items"):
                for order_id, variant_id in re.findall(
                    r"^  \(\d+, UNHEX\('[0-9a-f]+'\), (\d+), (\d+),",
                    block,
                    re.MULTILINE,
                ):
                    order = successful_orders.get(int(order_id))
                    if order is not None:
                        purchases.add((order[0], variants[int(variant_id)], order[1]))
            wishlist_count = 0
            wishlist_conversions = 0
            for block in _table_blocks(sql, "wishlist_items"):
                for customer_id, product_id, removed_at in re.findall(
                    r"^  \(\d+, (\d+), (\d+), [01], '[^']+', '[^']+', (NULL|'[^']+')",
                    block,
                    re.MULTILINE,
                ):
                    wishlist_count += 1
                    if removed_at != "NULL" and (
                        int(customer_id),
                        int(product_id),
                        removed_at.strip("'"),
                    ) in purchases:
                        wishlist_conversions += 1
            self.assertGreater(wishlist_count, 0)
            self.assertGreater(wishlist_conversions / wishlist_count, 0.20)


if __name__ == "__main__":
    unittest.main()
