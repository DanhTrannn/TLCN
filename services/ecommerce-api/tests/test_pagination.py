from datetime import UTC, datetime

import pytest

from app.common.pagination import decode_cursor, encode_cursor
from app.core.errors import AppError


def test_cursor_roundtrip():
    created = datetime(2026, 7, 24, 10, 30, tzinfo=UTC)
    cursor = encode_cursor(created, 42)
    decoded_t, decoded_i = decode_cursor(cursor)
    assert decoded_i == 42
    assert decoded_t == created


def test_invalid_cursor_raises_app_error():
    with pytest.raises(AppError):
        decode_cursor("!!!not-base64!!!")
