import json
from dataclasses import asdict, dataclass
from typing import Iterable

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


def build_cursor_advancements(
    watermarks: dict[str, dict],
    table_names: Iterable[str],
    updated_at_utc: str,
) -> dict[str, CursorState]:
    """Advance the committed cursor of every table to its captured high watermark.

    Tables without a captured watermark (empty sources) are skipped so their
    next run still performs a full extract once data appears.
    """
    states: dict[str, CursorState] = {}
    for name in table_names:
        hw = watermarks.get(name)
        if hw is None or hw.get("at") is None:
            continue
        states[name] = CursorState(
            cursor_at=hw["at"], cursor_pk=hw.get("pk"), updated_at_utc=updated_at_utc
        )
    return states


def write_committed_cursor(s3, bucket: str, table: str, state: CursorState) -> None:
    s3.put_object(Bucket=bucket, Key=cursor_object_path(bucket, table), Body=state.to_json())