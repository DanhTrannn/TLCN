"""Async Kafka producer singleton for access log streaming.

Lifecycle is managed via FastAPI lifespan. The producer is started on app
startup and gracefully stopped on shutdown. All send calls are fire-and-forget
so a Kafka outage never impacts API response latency.
"""

import asyncio
import json
import logging
import os
from typing import Any

logger = logging.getLogger("ecommerce_api.kafka")

_KAFKA_ENABLED: bool = os.getenv("KAFKA_ENABLED", "true").lower() == "true"
_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
_ACCESS_LOG_TOPIC: str = os.getenv("KAFKA_ACCESS_LOG_TOPIC", "ecommerce.access_logs")

_producer = None  # AIOKafkaProducer instance, lazily created


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
        logger.exception("kafka_producer.start_failed – Kafka unavailable, continuing without it")
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
    """Fire-and-forget: enqueue event to Kafka without awaiting confirmation.

    This is intentionally *not* an async function so it can be called from
    synchronous or async middleware code alike. Any exception is swallowed
    to ensure Kafka issues never break API responses.
    """
    if _producer is None:
        return
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Schedule the coroutine as a background task – no await needed
            loop.create_task(_safe_send(event))
    except Exception:
        logger.debug("kafka_producer.send_skipped – no running event loop")


async def _safe_send(event: dict[str, Any]) -> None:
    """Internal coroutine that performs the actual produce call."""
    if _producer is None:
        return
    try:
        await _producer.send(_ACCESS_LOG_TOPIC, event)
    except Exception:
        logger.warning("kafka_producer.send_failed", exc_info=True)
