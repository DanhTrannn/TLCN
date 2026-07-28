import os
import secrets
import time
from datetime import UTC, datetime
from uuid import UUID


def uuid7() -> UUID:
    """Generate a time-ordered UUIDv7 (48-bit ms timestamp + random)."""
    unix_ms = int(time.time() * 1000)
    rand_a = secrets.randbits(12)
    rand_b = secrets.randbits(62)
    value = (unix_ms & 0xFFFFFFFFFFFF) << 80
    value |= 0x7 << 76
    value |= rand_a << 64
    value |= 0b10 << 62
    value |= rand_b
    return UUID(int=value)


def _timestamp_prefix() -> str:
    return datetime.now(UTC).strftime("%Y%m%d%H%M%S")


def new_order_number() -> str:
    return f"OD{_timestamp_prefix()}{secrets.token_hex(4).upper()}"


def new_payment_reference() -> str:
    return f"PM{_timestamp_prefix()}{secrets.token_hex(4).upper()}"


def new_request_id() -> str:
    return uuid7().hex
