from lakehouse.cursor import CursorState
from lakehouse.query import build_range_predicate


def test_no_cursor_no_watermark_returns_empty():
    pred = build_range_predicate("updated_at", "order_id", None, None, None)
    assert pred == ""


def test_first_run_upper_bound_only():
    pred = build_range_predicate(
        "updated_at", "order_id", None, "2026-08-15 10:00:00", 5
    )
    assert pred == (
        " WHERE (`updated_at` < '2026-08-15 10:00:00' OR "
        "(`updated_at` = '2026-08-15 10:00:00' AND `order_id` <= 5))"
    )


def test_incremental_window_lower_and_upper():
    committed = CursorState("2026-08-15 09:00:00", 3, "2026-08-15T09:05:00Z")
    pred = build_range_predicate(
        "updated_at", "order_id", committed, "2026-08-15 10:00:00", 5
    )
    assert pred == (
        " WHERE (`updated_at` > '2026-08-15 09:00:00' OR "
        "(`updated_at` = '2026-08-15 09:00:00' AND `order_id` > 3))"
        " AND (`updated_at` < '2026-08-15 10:00:00' OR "
        "(`updated_at` = '2026-08-15 10:00:00' AND `order_id` <= 5))"
    )


def test_committed_without_watermark_lower_bound_only():
    committed = CursorState("2026-08-15 09:00:00", 3, "2026-08-15T09:05:00Z")
    pred = build_range_predicate("updated_at", "order_id", committed, None, None)
    assert pred == (
        " WHERE (`updated_at` > '2026-08-15 09:00:00' OR "
        "(`updated_at` = '2026-08-15 09:00:00' AND `order_id` > 3))"
    )


def test_committed_null_pk_defaults_to_zero():
    committed = CursorState("2026-08-15 09:00:00", None, "2026-08-15T09:05:00Z")
    pred = build_range_predicate(
        "updated_at", "order_id", committed, "2026-08-15 10:00:00", None
    )
    assert "`order_id` > 0" in pred
    assert "`order_id` <= 0" in pred
