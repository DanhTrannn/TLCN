import random
import unittest
from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

from generator.config import CATEGORY_NAMES, DEFAULT_DISTRIBUTIONS
from generator.sql_export import (
    _build_day_weights,
    _campaign_instances,
    _class_assignment,
    _event_day,
    _largest_remainder,
    _nth_weekday,
    _order_targets,
    _pick_base_datetime,
    _pick_category,
    _pick_product_price,
    _product_copy,
    _sale_boost,
    _shape_hour,
    _tet_factor,
    _weighted_index,
)


class DistributionHelperTest(unittest.TestCase):
    def test_weighted_index_always_picks_only_positive(self) -> None:
        rng = random.Random(1)
        self.assertEqual(_weighted_index(rng, [0, 100]), 1)
        self.assertEqual(_weighted_index(rng, [100, 0]), 0)

    def test_largest_remainder_sums_exactly(self) -> None:
        self.assertEqual(sum(_largest_remainder([1 / 3] * 3, 1)), 1)
        self.assertEqual(_largest_remainder([0.5, 0.5], 3), [2, 1])

    def test_class_assignment_counts_and_demo_segment(self) -> None:
        rng = random.Random(9)
        assignment = _class_assignment(100, DEFAULT_DISTRIBUTIONS.customer_classes, rng)
        self.assertEqual(len(assignment), 100)
        self.assertEqual(assignment.count("loyal"), 15)
        self.assertEqual(assignment.count("regular"), 35)
        self.assertEqual(assignment.count("one_off"), 50)
        self.assertEqual(assignment[0], "loyal")

    def test_order_targets_sum_to_total(self) -> None:
        rng = random.Random(9)
        class_by_name = {class_.name: class_ for class_ in DEFAULT_DISTRIBUTIONS.customer_classes}
        assignment = _class_assignment(10, DEFAULT_DISTRIBUTIONS.customer_classes, random.Random(3))
        targets = _order_targets(assignment, class_by_name, demo_target=24, total_orders=50, randomizer=rng)
        self.assertEqual(sum(targets), 50)
        self.assertEqual(targets[0], 24)

    def test_order_targets_all_orders_to_demo_when_single_customer(self) -> None:
        rng = random.Random(9)
        class_by_name = {class_.name: class_ for class_ in DEFAULT_DISTRIBUTIONS.customer_classes}
        targets = _order_targets(["loyal"], class_by_name, demo_target=24, total_orders=50, randomizer=rng)
        self.assertEqual(targets, [50])

    def test_tet_factor_peaks_at_center(self) -> None:
        tet = DEFAULT_DISTRIBUTIONS.tet
        self.assertEqual(_tet_factor(date(2026, 7, 1), tet), 1.0)
        self.assertEqual(_tet_factor(date(2026, 2, 6), tet), 2.8)
        self.assertGreater(_tet_factor(date(2026, 2, 6), tet), _tet_factor(date(2026, 1, 25), tet))

    def test_sale_boost_window(self) -> None:
        self.assertEqual(_sale_boost(date(2025, 11, 11), DEFAULT_DISTRIBUTIONS), 4.8)
        self.assertEqual(_sale_boost(date(2025, 11, 12), DEFAULT_DISTRIBUTIONS), 1.0)
        self.assertEqual(_sale_boost(date(2025, 11, 28), DEFAULT_DISTRIBUTIONS), 3.2)
        self.assertEqual(_sale_boost(date(2025, 11, 30), DEFAULT_DISTRIBUTIONS), 3.2)
        self.assertEqual(_sale_boost(date(2025, 12, 1), DEFAULT_DISTRIBUTIONS), 1.0)

    def test_nth_weekday_black_friday_2025(self) -> None:
        self.assertEqual(_nth_weekday(2025, 11, 4, 4), date(2025, 11, 28))

    def test_event_day_fixed_and_black_friday(self) -> None:
        self.assertEqual(_event_day(DEFAULT_DISTRIBUTIONS.sales[0], 2025), date(2025, 1, 1))
        self.assertEqual(_event_day(DEFAULT_DISTRIBUTIONS.sales[10], 2025), date(2025, 11, 11))
        self.assertEqual(_event_day(DEFAULT_DISTRIBUTIONS.sales[-1], 2025), date(2025, 11, 28))

    def test_contains_all_monthly_double_days(self) -> None:
        fixed = [event for event in DEFAULT_DISTRIBUTIONS.sales if event.day is not None]
        self.assertEqual(
            [(event.month, event.day) for event in fixed],
            [(month, month) for month in range(1, 13)],
        )

    def test_campaign_instances_cover_history_window(self) -> None:
        start = datetime(2025, 7, 2, tzinfo=UTC)
        end = datetime(2026, 7, 1, tzinfo=UTC)
        instances = _campaign_instances(start, end, DEFAULT_DISTRIBUTIONS)
        business_zone = ZoneInfo(DEFAULT_DISTRIBUTIONS.business_timezone)
        dates = {moment.astimezone(business_zone).date() for _, moment in instances}
        self.assertIn(date(2025, 7, 7), dates)
        self.assertIn(date(2025, 11, 28), dates)
        self.assertIn(date(2026, 6, 6), dates)
        self.assertNotIn(date(2025, 1, 1), dates)

    def test_build_day_weights_covers_history(self) -> None:
        start = date(2025, 7, 2)
        end = date(2026, 7, 1)
        days, weights = _build_day_weights(start, end, DEFAULT_DISTRIBUTIONS)
        self.assertEqual(len(days), 365)
        self.assertEqual(days[0], start)
        self.assertEqual(days[-1], end)
        self.assertTrue(all(weight > 0 for weight in weights))

    def test_pick_base_datetime_within_history(self) -> None:
        rng = random.Random(11)
        start = datetime(2025, 7, 2, tzinfo=UTC)
        end = datetime(2026, 7, 1, tzinfo=UTC)
        days, weights = _build_day_weights(start.date(), end.date(), DEFAULT_DISTRIBUTIONS)
        for _ in range(50):
            picked = _pick_base_datetime(rng, start, end, days, weights, DEFAULT_DISTRIBUTIONS)
            self.assertGreaterEqual(picked, start)
            self.assertLessEqual(picked, end)
            self.assertEqual(picked.minute % 60 >= 0, True)

    def test_shape_hour_preserves_date(self) -> None:
        rng = random.Random(5)
        moment = datetime(2026, 3, 15, 10, 30, tzinfo=UTC)
        shaped = _shape_hour(rng, moment, DEFAULT_DISTRIBUTIONS)
        self.assertEqual((shaped.year, shaped.month, shaped.day), (2026, 3, 15))
        self.assertTrue(0 <= shaped.hour <= 23)

    def test_campaign_days_have_midnight_spike(self) -> None:
        campaign_rng = random.Random(5)
        normal_rng = random.Random(5)
        campaign = datetime(2026, 6, 6, 10, 30, tzinfo=UTC)
        normal = datetime(2026, 6, 7, 10, 30, tzinfo=UTC)
        sample_size = 5_000
        business_zone = ZoneInfo(DEFAULT_DISTRIBUTIONS.business_timezone)
        campaign_midnight = sum(
            _shape_hour(campaign_rng, campaign, DEFAULT_DISTRIBUTIONS)
            .astimezone(business_zone)
            .hour
            in (0, 1)
            for _ in range(sample_size)
        )
        normal_midnight = sum(
            _shape_hour(normal_rng, normal, DEFAULT_DISTRIBUTIONS)
            .astimezone(business_zone)
            .hour
            in (0, 1)
            for _ in range(sample_size)
        )
        self.assertGreater(campaign_midnight / sample_size, 0.20)
        self.assertGreater(campaign_midnight, normal_midnight * 3)

    def test_pick_product_price_within_union_rounded_to_thousands(self) -> None:
        rng = random.Random(21)
        for _ in range(50):
            price = _pick_product_price(rng, DEFAULT_DISTRIBUTIONS.price_bands)
            self.assertTrue(79000 <= price <= 2500000)
            self.assertEqual(price % 1000, 0)

    def test_pick_category_returns_known_code(self) -> None:
        rng = random.Random(4)
        for _ in range(50):
            code = _pick_category(rng, DEFAULT_DISTRIBUTIONS.categories)
            self.assertIn(code, {code for code, _ in DEFAULT_DISTRIBUTIONS.categories})

    def test_product_copy_is_realistic_unique_and_category_specific(self) -> None:
        for category_code in CATEGORY_NAMES:
            names = []
            for sequence in range(30):
                name, description = _product_copy(category_code, sequence)
                names.append(name)
                self.assertNotIn("Sản phẩm tổng hợp", name)
                self.assertLessEqual(len(name), 200)
                self.assertIn("D&K", description)
                self.assertIn("phiên bản sản phẩm", description)
            self.assertEqual(len(names), len(set(names)))


if __name__ == "__main__":
    unittest.main()
