import json

import pytest

from lakehouse.cursor import CURSOR_DIR, CursorState, cursor_object_path


def test_cursor_object_path():
    assert cursor_object_path("web-lakehouse", "orders") == "state/cursor/orders.json"


def test_to_json_round_trip():
    state = CursorState(cursor_at="2026-08-15T10:00:00.000000", cursor_pk=42,
                        updated_at_utc="2026-08-15T10:05:00Z")
    parsed = CursorState.from_json(state.to_json())
    assert parsed == state


def test_from_json_accepts_null_pk():
    state = CursorState.from_json(json.dumps(
        {"cursor_at": "2026-08-15T10:00:00.000000", "cursor_pk": None,
         "updated_at_utc": "2026-08-15T10:05:00Z"}))
    assert state.cursor_pk is None


def test_from_json_missing_field_raises():
    with pytest.raises(ValueError, match="cursor_at"):
        CursorState.from_json('{"cursor_pk": 1, "updated_at_utc": "x"}')


def test_from_json_bad_pk_raises():
    with pytest.raises(ValueError, match="cursor_pk"):
        CursorState.from_json('{"cursor_at": "x", "cursor_pk": "abc", "updated_at_utc": "y"}')


def test_cursor_dir_constant():
    assert CURSOR_DIR == "state/cursor"