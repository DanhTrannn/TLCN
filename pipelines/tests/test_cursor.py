import json

import pytest

from lakehouse.cursor import (
    CURSOR_DIR,
    CursorState,
    build_cursor_advancements,
    cursor_object_path,
    write_committed_cursor,
)


def test_cursor_object_path():
    assert cursor_object_path("lakehouse", "orders") == "state/cursor/orders.json"


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


class _FakeS3:
    def __init__(self):
        self.objects = {}

    def put_object(self, Bucket, Key, Body):
        self.objects[(Bucket, Key)] = Body
        return {"ETag": "x"}


def test_build_cursor_advancements_skips_empty_tables():
    watermarks = {
        "orders": {"at": "2026-08-15 10:00:00", "pk": 5},
        "payments": {"at": None, "pk": None},
    }
    states = build_cursor_advancements(
        watermarks, ["orders", "payments"], "2026-08-15T10:05:00Z"
    )
    assert list(states) == ["orders"]
    assert states["orders"] == CursorState(
        cursor_at="2026-08-15 10:00:00", cursor_pk=5,
        updated_at_utc="2026-08-15T10:05:00Z",
    )


def test_build_cursor_advancements_skips_missing_table():
    states = build_cursor_advancements(
        {"orders": {"at": "2026-08-15 10:00:00", "pk": 5}},
        ["orders", "missing_table"],
        "2026-08-15T10:05:00Z",
    )
    assert list(states) == ["orders"]


def test_write_committed_cursor_round_trip():
    s3 = _FakeS3()
    state = CursorState("2026-08-15 10:00:00", 5, "2026-08-15T10:05:00Z")
    write_committed_cursor(s3, "lakehouse", "orders", state)
    body = s3.objects[("lakehouse", "state/cursor/orders.json")]
    parsed = CursorState.from_json(body)
    assert parsed == state


def test_write_committed_cursor_key_uses_cursor_object_path():
    s3 = _FakeS3()
    state = CursorState("2026-08-15 10:00:00", 5, "2026-08-15T10:05:00Z")
    write_committed_cursor(s3, "lakehouse", "customers", state)
    assert list(s3.objects) == [("lakehouse", "state/cursor/customers.json")]