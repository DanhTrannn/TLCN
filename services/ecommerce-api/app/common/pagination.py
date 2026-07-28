import base64
import json
from datetime import datetime
from typing import Any

from app.core.errors import VALIDATION_ERROR, AppError


def encode_cursor(created_at: datetime, internal_id: int) -> str:
    raw = json.dumps({"t": created_at.isoformat(), "i": internal_id}).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii")


def decode_cursor(cursor: str) -> tuple[datetime, int]:
    try:
        raw = base64.urlsafe_b64decode(cursor.encode("ascii"))
        data: dict[str, Any] = json.loads(raw)
        return datetime.fromisoformat(data["t"]), int(data["i"])
    except (ValueError, KeyError, TypeError) as error:
        raise AppError(VALIDATION_ERROR, "Cursor không hợp lệ.", status_code=400) from error
