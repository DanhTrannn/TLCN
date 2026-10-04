import json

import pytest
from app.core import kafka_producer


@pytest.fixture(autouse=True)
def reset_producer_state(tmp_path, monkeypatch):
    kafka_producer.reset_dropped_events_count()
    dlq_file = tmp_path / "test_dlq.jsonl"
    monkeypatch.setenv("KAFKA_DLQ_FILE_PATH", str(dlq_file))
    yield dlq_file
    kafka_producer.reset_dropped_events_count()


def test_send_event_routes_to_dlq_when_producer_offline(reset_producer_state):
    dlq_file = reset_producer_state
    event = {"event_id": "evt-123", "action": "product_view", "url": "/products/1"}

    # Producer is None (offline)
    kafka_producer.send_access_event(event)

    assert kafka_producer.get_dropped_events_count() == 1
    assert dlq_file.exists()

    content = dlq_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(content) == 1
    record = json.loads(content[0])
    assert record["event_id"] == "evt-123"
    assert record["_dlq_reason"] == "producer_offline"
    assert "_dlq_timestamp" in record


@pytest.mark.anyio
async def test_safe_send_failure_routes_to_dlq(reset_producer_state, monkeypatch):

    dlq_file = reset_producer_state
    event = {"event_id": "evt-456", "action": "checkout_start"}

    # Mock a failing producer
    class FailingProducer:
        async def send(self, topic, value):
            raise ConnectionError("Kafka cluster broker disconnected")

    monkeypatch.setattr(kafka_producer, "_producer", FailingProducer())

    await kafka_producer._safe_send(event)

    assert kafka_producer.get_dropped_events_count() == 1
    assert dlq_file.exists()

    content = dlq_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(content) == 1
    record = json.loads(content[0])
    assert record["event_id"] == "evt-456"
    assert "send_failed" in record["_dlq_reason"]
