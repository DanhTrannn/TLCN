import threading
import time
from collections import OrderedDict
from datetime import UTC, datetime
from uuid import UUID

from app.schemas.event import WebEvent
from app.writer.jsonl_writer import JsonlWriter


class EventIngestor:
    def __init__(
        self,
        writer: JsonlWriter,
        service_version: str,
        dedup_window_seconds: int,
        dedup_max_entries: int,
    ) -> None:
        self.writer = writer
        self.service_version = service_version
        self.dedup_window_seconds = dedup_window_seconds
        self.dedup_max_entries = dedup_max_entries
        self._seen: OrderedDict[UUID, float] = OrderedDict()
        self._lock = threading.Lock()

    def ingest(self, event: WebEvent) -> bool:
        now = time.monotonic()
        with self._lock:
            self._evict(now)
            if event.event_id in self._seen:
                return True
            record = event.model_dump(mode="json")
            record["collector_received_at"] = datetime.now(UTC).isoformat()
            record["collector_version"] = self.service_version
            self.writer.append(record)
            self._seen[event.event_id] = now
        return False

    def _evict(self, now: float) -> None:
        cutoff = now - self.dedup_window_seconds
        while self._seen:
            _, first_seen = next(iter(self._seen.items()))
            if first_seen >= cutoff and len(self._seen) < self.dedup_max_entries:
                break
            self._seen.popitem(last=False)
