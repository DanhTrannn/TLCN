"""Async Kafka producer singleton for access log streaming.

Lifecycle is managed via FastAPI lifespan. The producer is started on app
startup and gracefully stopped on shutdown. All send calls are fire-and-forget
so a Kafka outage never impacts API response latency.
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("ecommerce_api.kafka")

_KAFKA_ENABLED: bool = os.getenv("KAFKA_ENABLED", "true").lower() == "true"
_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
_ACCESS_LOG_TOPIC: str = os.getenv("KAFKA_ACCESS_LOG_TOPIC", "ecommerce.access_logs")
_DLQ_FILE_PATH: str = os.getenv("KAFKA_DLQ_FILE_PATH", "data/events/dlq_access_logs.jsonl")

_producer = None  # AIOKafkaProducer instance, lazily created
_dropped_events_count: int = 0


def get_dropped_events_count() -> int:
    """Return the total number of events dropped or routed to DLQ."""
    return _dropped_events_count


def reset_dropped_events_count() -> None:
    """Reset the dropped events counter (for testing/monitoring)."""
    global _dropped_events_count
    _dropped_events_count = 0


def record_dropped_event(event: dict[str, Any], reason: str) -> None:
    """Increment drop counter and append event to local Dead-Letter Queue file."""
    global _dropped_events_count
    _dropped_events_count += 1

    dlq_path = os.getenv("KAFKA_DLQ_FILE_PATH", _DLQ_FILE_PATH)
    try:
        os.makedirs(os.path.dirname(os.path.abspath(dlq_path)), exist_ok=True)
        payload = {
            **event,
            "_dlq_reason": reason,
            "_dlq_timestamp": datetime.now(timezone.utc).isoformat(),
        }
        with open(dlq_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, default=str) + "\n")
    except Exception as dlq_err:
        logger.error("kafka_producer.dlq_write_failed: %s", dlq_err)


async def start_producer() -> None:
    """Start the AIOKafkaProducer. Called once at app startup."""
    global _producer
    if not _KAFKA_ENABLED:
        logger.info("kafka_producer.disabled – KAFKA_ENABLED=false, skipping startup")
        return
    try:
        from aiokafka import AIOKafkaProducer  # noqa: PLC0415

        _producer = AIOKafkaProducer(
            bootstrap_servers=_BOOTSTRAP_SERVERS,
            # Serialize Python dicts as UTF-8 JSON bytes
            value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
            # Linger up to 5 ms to allow micro-batching without blocking requests
            linger_ms=5,
            # Retry up to 3 times on transient send errors
            request_timeout_ms=5_000,
            retry_backoff_ms=100,
        )
        await _producer.start()
        logger.info(
            "kafka_producer.started",
            extra={"bootstrap_servers": _BOOTSTRAP_SERVERS, "topic": _ACCESS_LOG_TOPIC},
        )
    except Exception:
        logger.exception("kafka_producer.start_failed – Kafka unavailable, continuing with DLQ fallback")
        _producer = None


async def stop_producer() -> None:
    """Gracefully stop the AIOKafkaProducer. Called once at app shutdown."""
    global _producer
    if _producer is not None:
        try:
            await _producer.stop()
            logger.info("kafka_producer.stopped")
        except Exception:
            logger.exception("kafka_producer.stop_error")
        finally:
            _producer = None


def send_access_event(event: dict[str, Any]) -> None:
    """Fire-and-forget: enqueue event to Kafka or route to Dead-Letter Queue.

    This is intentionally *not* an async function so it can be called from
    synchronous or async middleware code alike. If the Kafka producer is
    offline or the event loop is unavailable, the event is saved to DLQ.
    """
    if _producer is None:
        record_dropped_event(event, reason="producer_offline")
        return
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Schedule the coroutine as a background task – no await needed
            loop.create_task(_safe_send(event))
        else:
            record_dropped_event(event, reason="event_loop_not_running")
    except Exception as exc:
        record_dropped_event(event, reason=f"loop_error: {exc}")
        logger.debug("kafka_producer.send_skipped – event routed to DLQ")


async def _safe_send(event: dict[str, Any]) -> None:
    """Internal coroutine that performs the actual produce call with DLQ fallback."""
    if _producer is None:
        record_dropped_event(event, reason="producer_offline")
        return
    try:
        await _producer.send(_ACCESS_LOG_TOPIC, event)
    except Exception as exc:
        record_dropped_event(event, reason=f"send_failed: {exc}")
        logger.warning("kafka_producer.send_failed – routed to DLQ", exc_info=True)

