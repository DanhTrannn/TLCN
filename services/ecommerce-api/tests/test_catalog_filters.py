from datetime import UTC, datetime

import pytest

from app.core.errors import AppError
from app.modules.catalog.service import (
    _decode_product_cursor,
    _encode_product_cursor,
    _normalize_values,
    _search_pattern,
)


def test_catalog_cursor_round_trips_for_newest_and_price() -> None:
    created_at = datetime.now(UTC)
    newest = _encode_product_cursor("newest", created_at, 42)
    price = _encode_product_cursor("price_asc", 199_000, 42)

    assert _decode_product_cursor(newest, "newest") == (created_at, 42)
    assert _decode_product_cursor(price, "price_asc") == (199_000, 42)


def test_catalog_cursor_rejects_different_sort() -> None:
    cursor = _encode_product_cursor("price_asc", 199_000, 42)

    with pytest.raises(AppError):
        _decode_product_cursor(cursor, "price_desc")


def test_filter_values_are_trimmed_deduplicated_and_bounded() -> None:
    assert _normalize_values([" M ", "M", "L"], "size") == ["M", "L"]

    with pytest.raises(AppError):
        _normalize_values([str(index) for index in range(11)], "size")


def test_search_pattern_escapes_wildcards() -> None:
    assert _search_pattern("50%_off") == "%50\\%\\_off%"
