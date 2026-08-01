import random
import unittest
from datetime import UTC, date, datetime, timedelta

from tlcn_generator.config import DEFAULT_DISTRIBUTIONS, PriceBand, TetWindow
from tlcn_generator.sql_export import (
    _build_day_weights,
    _class_assignment,
    _event_day,
    _largest_remainder,
    _nth_weekday,
    _order_targets,
    _pick_base_datetime,
    _pick_category,
    _pick_product_price,
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

    def test_class_assignment_counts(self) -> None:
        rng = random.Random(9)
        assignment = _class_assignment(100, DEFAULT_DISTRIBUTIONS.customer_classes, rng)
        self.assertEqual(len(assignment), 100)
        self.assertEqual(assignment.count("loyal"), 15)
        self.assertEqual(assignment.count("regular"), 35)
        self.assertEqual(assignment.count("one_off"), 50)

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
        self.assertEqual(_sale_boost(date(2025, 11, 11), DEFAULT_DISTRIBUTIONS), 2.5)
        self.assertEqual(_sale_boost(date(2025, 11, 15), DEFAULT_DISTRIBUTIONS), 2.5)
        self.assertEqual(_sale_boost(date(2025, 11, 16), DEFAULT_DISTRIBUTIONS), 1.0)

    def test_nth_weekday_black_friday_2025(self) -> None:
        self.assertEqual(_nth_weekday(2025, 11, 4, 4), date(2025, 11, 28))

    def test_event_day_fixed_and_black_friday(self) -> None:
        self.assertEqual(_event_day(DEFAULT_DISTRIBUTIONS.sales[0], 2025), date(2025, 11, 11))
        self.assertEqual(_event_day(DEFAULT_DISTRIBUTIONS.sales[3], 2025), date(2025, 11, 28))

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
            picked = _pick_base_datetime(rng, start, end, days, weights, DEFAULT_DISTRIBUTIONS.hour_of_day)
            self.assertGreaterEqual(picked, start)
            self.assertLessEqual(picked, end)
            self.assertEqual(picked.minute % 60 >= 0, True)

    def test_shape_hour_preserves_date(self) -> None:
        rng = random.Random(5)
        moment = datetime(2026, 3, 15, 10, 30, tzinfo=UTC)
        shaped = _shape_hour(rng, moment, DEFAULT_DISTRIBUTIONS.hour_of_day)
        self.assertEqual((shaped.year, shaped.month, shaped.day), (2026, 3, 15))
        self.assertTrue(0 <= shaped.hour <= 23)

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


if __name__ == "__main__":
    unittest.main()
