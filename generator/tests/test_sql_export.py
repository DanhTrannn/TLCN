import hashlib
import re
import tempfile
import unittest
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID
from zoneinfo import ZoneInfo

from argon2 import PasswordHasher

from generator.config import DEFAULT_DISTRIBUTIONS, GeneratorConfig, PriceBand
from generator.sql_export import (
    DEMO_PASSWORD,
    FAMILY_NAMES,
    FEMALE_GIVEN_NAMES,
    MALE_GIVEN_NAMES,
    PRODUCT_IMAGE_URL,
    SYNTHETIC_COUPON_ARCHIVE_REASON,
    SYNTHETIC_PRODUCT_ARCHIVE_REASON,
    export_sql,
)


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
            self.assertEqual(str(UUID(self.config.logical_identity)), self.config.logical_identity)
            self.assertEqual(
                str(UUID(first_summary.generation_run_id)),
                first_summary.generation_run_id,
            )

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
            self.assertIn("UUID_TO_BIN(", sql)
            self.assertIn("-- identifier_strategy: uuid5-deterministic-v1", sql)
            self.assertNotIn("UNHEX(", sql)

            if "'cancelled'" in "".join(_table_blocks(sql, "orders")):
                self.assertIn("INSERT INTO `refunds`", sql)

            uuid_pattern = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
            order_blocks = _table_blocks(sql, "orders")
            checkout_keys = [
                value
                for block in order_blocks
                for value in re.findall(
                    rf"^  \(\d+, '[^']+', \d+, \d+, '({uuid_pattern})',",
                    block,
                    re.MULTILINE,
                )
            ]
            self.assertEqual(len(checkout_keys), first_summary.orders)
            self.assertEqual(len(checkout_keys), len(set(checkout_keys)))

            payment_identifiers = [
                pair
                for block in _table_blocks(sql, "payments")
                for pair in re.findall(
                    rf"^  \(\d+, '({uuid_pattern})', \d+, '({uuid_pattern})',",
                    block,
                    re.MULTILINE,
                )
            ]
            self.assertEqual(len(payment_identifiers), first_summary.orders)
            self.assertEqual(
                len({value for pair in payment_identifiers for value in pair}),
                first_summary.orders * 2,
            )

            transition_keys = [
                value
                for block in _table_blocks(sql, "order_status_history")
                for value in re.findall(
                    rf"^  \(\d+, \d+, (?:NULL|'[^']+'), '[^']+', '[^']+', "
                    rf"(?:NULL|'[^']*'), '({uuid_pattern})',",
                    block,
                    re.MULTILINE,
                )
            ]
            self.assertGreaterEqual(len(transition_keys), first_summary.orders)
            self.assertEqual(len(transition_keys), len(set(transition_keys)))

            password_hash_start = sql.index("$argon2id$")
            password_hash_end = sql.index("'", password_hash_start)
            PasswordHasher().verify(sql[password_hash_start:password_hash_end], DEMO_PASSWORD)

    def test_customer_names_are_vietnamese_structured(self) -> None:
        config = replace(
            self.config,
            scale={"customers": 120, "products": 40, "variants": 120, "orders": 800},
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "names.sql"
            export_sql(config, path)
            sql = path.read_text(encoding="utf-8")

            self.assertNotIn("Khách hàng tổng hợp", sql)
            self.assertIn("Kiểm duyệt viên dữ liệu tổng hợp", sql)

            names = []
            for block in _table_blocks(sql, "customers"):
                names.extend(
                    re.findall(
                        r"^  \(\d+, UUID_TO_BIN\('[0-9a-f-]{36}'\), 'customer', '([^']+)',",
                        block,
                        re.MULTILINE,
                    )
                )
            self.assertEqual(len(names), config.scale["customers"])
            for name in names:
                parts = name.split(" ")
                self.assertEqual(len(parts), 3, name)
                self.assertIn(parts[0], FAMILY_NAMES)
                self.assertIn(parts[2], FEMALE_GIVEN_NAMES + MALE_GIVEN_NAMES)

    def test_customer_names_are_majority_female(self) -> None:
        config = replace(
            self.config,
            scale={"customers": 200, "products": 40, "variants": 120, "orders": 800},
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "names-female.sql"
            export_sql(config, path)
            sql = path.read_text(encoding="utf-8")

            female_count = 0
            for block in _table_blocks(sql, "customers"):
                for given in re.findall(
                    r"^  \(\d+, UUID_TO_BIN\('[0-9a-f-]{36}'\), 'customer', '[^']+ [^']+ ([^']+)',",
                    block,
                    re.MULTILINE,
                ):
                    if given in FEMALE_GIVEN_NAMES:
                        female_count += 1
            self.assertGreater(female_count / config.scale["customers"], 0.70)
            self.assertLess(female_count / config.scale["customers"], 0.95)

    def test_receiver_name_matches_customer_display_name(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "receivers.sql"
            export_sql(self.config, path)
            sql = path.read_text(encoding="utf-8")

            names_by_customer: dict[str, str] = {}
            for block in _table_blocks(sql, "customers"):
                names_by_customer.update(
                    {
                        customer_id: display_name
                        for customer_id, display_name in re.findall(
                            r"^  \((\d+), UUID_TO_BIN\('[0-9a-f-]{36}'\), 'customer', '([^']+)',",
                            block,
                            re.MULTILINE,
                        )
                    }
                )
            mismatches = 0
            checked = 0
            for block in _table_blocks(sql, "orders"):
                for customer_id, receiver_name in re.findall(
                    r"^  \(\d+, 'SYN[^']+', \d+, (\d+), '[^']+', '[^']+', 'VND', "
                    r"\d+, \d+, \d+, '([^']+)',",
                    block,
                    re.MULTILINE,
                ):
                    checked += 1
                    if names_by_customer.get(customer_id) != receiver_name:
                        mismatches += 1
            self.assertGreater(checked, 0)
            self.assertEqual(mismatches, 0)

    def test_receiver_address_matches_customer_address(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "addresses.sql"
            export_sql(self.config, path)
            sql = path.read_text(encoding="utf-8")

            self.assertNotIn("đường Dữ Liệu", sql)
            self.assertNotIn("phường Mẫu", sql)

            addresses_by_customer: dict[str, str] = {}
            for block in _table_blocks(sql, "orders"):
                for customer_id, address in re.findall(
                    r"^  \(\d+, 'SYN[^']+', \d+, (\d+), '[^']+', '[^']+', 'VND', "
                    r"\d+, \d+, \d+, '[^']+', '09\d+', '([^']+)',",
                    block,
                    re.MULTILINE,
                ):
                    addresses_by_customer[customer_id] = address
            self.assertGreater(len(addresses_by_customer), 0)
            for address in addresses_by_customer.values():
                self.assertIn("đường ", address)
                self.assertIn(", phường ", address)
                self.assertIn(", TP. Hồ Chí Minh", address)

            self.assertGreater(len(set(addresses_by_customer.values())), 1)

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
                r"^\s+\(\d+, UUID_TO_BIN\('[0-9a-f-]{36}'\), \d+, '[^']+', '[^']+', '[^']+', (\d+),",
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
                r"^\s+\(\d+, UUID_TO_BIN\('[0-9a-f-]{36}'\), \d+, '[^']+', '[^']+', '[^']+', (\d+),",
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
            order_ids = re.findall(r"^  \(\d+, UUID_TO_BIN\('[0-9a-f-]{36}'\), (\d+),", block, re.MULTILINE)
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
                r"'synthetic', '[0-9a-f-]{36}', '(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+)'",
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

            product_start = sql.index("INSERT INTO `products`")
            product_end = sql.index("\n\n", product_start)
            product_block = sql[product_start:product_end]
            archived_product_rows = [
                line
                for line in product_block.splitlines()
                if SYNTHETIC_PRODUCT_ARCHIVE_REASON in line
            ]
            self.assertEqual(len(archived_product_rows), 2)
            archived_product_ids: set[int] = set()
            for row in archived_product_rows:
                product_id_match = re.match(r"^  \((\d+),", row)
                self.assertIsNotNone(product_id_match)
                archived_product_ids.add(int(product_id_match.group(1)))
                self.assertIn(", 0, '2026-07-01 00:00:00.000000',", row)
                self.assertRegex(
                    row,
                    rf", \d+, '{re.escape(SYNTHETIC_PRODUCT_ARCHIVE_REASON)}',",
                )

            archived_coupon_rows = [
                line
                for line in coupon_block.splitlines()
                if SYNTHETIC_COUPON_ARCHIVE_REASON in line
            ]
            self.assertGreater(len(archived_coupon_rows), 0)
            archived_coupon_ids: set[int] = set()
            for row in archived_coupon_rows:
                coupon_id_match = re.match(r"^  \((\d+),", row)
                self.assertIsNotNone(coupon_id_match)
                archived_coupon_ids.add(int(coupon_id_match.group(1)))
                self.assertRegex(
                    row,
                    rf", 0, \d+, \d+, 0, '[^']+', \d+, "
                    rf"'{re.escape(SYNTHETIC_COUPON_ARCHIVE_REASON)}',",
                )

            redeemed_coupon_ids = {
                int(coupon_id)
                for block in _table_blocks(sql, "coupon_redemptions")
                for coupon_id in re.findall(r"^  \(\d+, (\d+),", block, re.MULTILINE)
            }
            self.assertTrue(archived_coupon_ids & redeemed_coupon_ids)

            self.assertGreater(_count_rows(sql, "coupon_redemptions"), 100)
            self.assertGreater(_count_rows(sql, "product_reviews"), 200)
            review_start = sql.index("INSERT INTO `product_reviews`")
            review_end = sql.index("\n\n", review_start)
            review_block = sql[review_start:review_end]
            for status in ("approved", "rejected"):
                self.assertIn(f"'{status}'", review_block)
            self.assertNotIn("'pending'", review_block)
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
                            r"^  \((\d+), UUID_TO_BIN\('[0-9a-f-]{36}'\), (\d+),",
                            block,
                            re.MULTILINE,
                        )
                    }
                )
            successful_orders: dict[int, tuple[int, str]] = {}
            for block in _table_blocks(sql, "orders"):
                for order_id, customer_id, status, created_at in re.findall(
                    r"^  \((\d+), '[^']+', \d+, (\d+), '[^']+', '([^']+)'.*?"
                    r"'synthetic', '[0-9a-f-]{36}', '([^']+)'",
                    block,
                    re.MULTILINE,
                ):
                    if status != "cancelled":
                        successful_orders[int(order_id)] = (int(customer_id), created_at)
            purchases: set[tuple[int, int, str]] = set()
            ordered_product_ids: set[int] = set()
            for block in _table_blocks(sql, "order_items"):
                for order_id, variant_id in re.findall(
                    r"^  \(\d+, UUID_TO_BIN\('[0-9a-f-]{36}'\), (\d+), (\d+),",
                    block,
                    re.MULTILINE,
                ):
                    ordered_product_ids.add(variants[int(variant_id)])
                    order = successful_orders.get(int(order_id))
                    if order is not None:
                        purchases.add((order[0], variants[int(variant_id)], order[1]))
            self.assertTrue(archived_product_ids & ordered_product_ids)
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
