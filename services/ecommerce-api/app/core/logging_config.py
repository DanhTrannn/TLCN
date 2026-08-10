import json
import logging
import os
from datetime import UTC, datetime
from typing import Any


_SAFE_FIELDS = (
    "request_id",
    "method",
    "route",
    "status",
    "latency_ms",
    "error_code",
    "operation",
    "event_id",
    "event_name",
    "duplicate",
)


class JsonLineFormatter(logging.Formatter):
    def __init__(self, service_name: str, service_version: str) -> None:
        super().__init__()
        self.service_name = service_name
        self.service_version = service_version

    def format(self, record: logging.LogRecord) -> str:
        access_event = getattr(record, "access_event", None)
        if isinstance(access_event, dict):
            return json.dumps(
                access_event,
                ensure_ascii=False,
                separators=(",", ":"),
                default=str,
            )
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat().replace("+00:00", "Z"),
            "service": self.service_name,
            "service_version": self.service_version,
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for field in _SAFE_FIELDS:
            value = getattr(record, field, None)
            if value is not None and value != "":
                payload[field] = value
        if record.exc_info and record.exc_info[0] is not None:
            payload["exception_type"] = record.exc_info[0].__name__
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), default=str)


def configure_logging(service_name: str, service_version: str) -> None:
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(JsonLineFormatter(service_name, service_version))

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        uvicorn_logger = logging.getLogger(logger_name)
        uvicorn_logger.handlers.clear()
        uvicorn_logger.propagate = True
        uvicorn_logger.disabled = logger_name == "uvicorn.access"
