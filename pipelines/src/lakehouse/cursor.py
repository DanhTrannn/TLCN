import json
from dataclasses import asdict, dataclass

CURSOR_DIR = "state/cursor"


def cursor_object_path(bucket: str, table: str) -> str:
    return f"{CURSOR_DIR}/{table}.json"


@dataclass(frozen=True)
class CursorState:
    cursor_at: str
    cursor_pk: int | None
    updated_at_utc: str

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, text: str) -> "CursorState":
        raw = json.loads(text)
        if "cursor_at" not in raw:
            raise ValueError("cursor_at is required")
        pk = raw.get("cursor_pk")
        if pk is not None and not isinstance(pk, int):
            raise ValueError("cursor_pk must be an int or null")
        if "updated_at_utc" not in raw:
            raise ValueError("updated_at_utc is required")
        return cls(cursor_at=raw["cursor_at"], cursor_pk=pk, updated_at_utc=raw["updated_at_utc"])