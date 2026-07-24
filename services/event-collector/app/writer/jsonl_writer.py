import hashlib
import json
import os
import threading
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TextIO
from uuid import uuid4


class JsonlWriter:
    def __init__(self, directory: Path, max_bytes: int, max_age_seconds: int) -> None:
        self.directory = directory
        self.max_bytes = max_bytes
        self.max_age_seconds = max_age_seconds
        self._lock = threading.Lock()
        self._stream: TextIO | None = None
        self._active_path: Path | None = None
        self._opened_at = 0.0
        self._record_count = 0
        self.directory.mkdir(parents=True, exist_ok=True)

    def append(self, record: dict[str, Any]) -> None:
        line = json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"
        with self._lock:
            self._ensure_open()
            if self._should_rotate(len(line.encode("utf-8"))):
                self._close_current()
                self._ensure_open()
            if self._stream is None:
                raise RuntimeError("event stream is not open")
            self._stream.write(line)
            self._stream.flush()
            self._record_count += 1

    def close(self) -> None:
        with self._lock:
            self._close_current()

    def _ensure_open(self) -> None:
        if self._stream is not None:
            return
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
        self._active_path = self.directory / f"events-{stamp}-{uuid4().hex}.active"
        self._stream = self._active_path.open("a", encoding="utf-8")
        self._opened_at = time.monotonic()
        self._record_count = 0

    def _should_rotate(self, next_bytes: int) -> bool:
        if self._stream is None or self._active_path is None or self._record_count == 0:
            return False
        current_size = self._active_path.stat().st_size
        age = time.monotonic() - self._opened_at
        return current_size + next_bytes > self.max_bytes or age >= self.max_age_seconds

    def _close_current(self) -> None:
        if self._stream is None or self._active_path is None:
            return
        self._stream.flush()
        os.fsync(self._stream.fileno())
        self._stream.close()
        closed_path = self._active_path.with_suffix(".jsonl")
        os.replace(self._active_path, closed_path)
        self._write_metadata(closed_path, self._record_count)
        self._stream = None
        self._active_path = None
        self._record_count = 0

    def _write_metadata(self, closed_path: Path, record_count: int) -> None:
        checksum = hashlib.sha256(closed_path.read_bytes()).hexdigest()
        metadata = {
            "path": closed_path.name,
            "sha256": checksum,
            "size_bytes": closed_path.stat().st_size,
            "record_count": record_count,
            "closed_at": datetime.now(UTC).isoformat(),
        }
        temporary_path = closed_path.with_suffix(".meta.json.tmp")
        metadata_path = closed_path.with_suffix(".meta.json")
        temporary_path.write_text(json.dumps(metadata, ensure_ascii=False), encoding="utf-8")
        os.replace(temporary_path, metadata_path)

