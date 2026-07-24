from datetime import UTC, datetime
from uuid import uuid4

from app.schemas.event import WebEvent


def test_event_schema_accepts_core_event() -> None:
    event = WebEvent(
        event_id=uuid4(),
        event_name="session_start",
        schema_version=1,
        event_time=datetime.now(UTC),
        analytics_session_id=uuid4(),
        device_class="desktop",
        data_origin="manual",
    )

    assert event.event_name == "session_start"
