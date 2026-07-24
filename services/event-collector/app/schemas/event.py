from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class WebEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: UUID
    event_name: Literal["session_start", "view_product", "add_to_cart", "begin_checkout"]
    schema_version: Literal[1, 2]
    event_time: datetime
    analytics_session_id: UUID
    customer_ref: str | None = Field(default=None, max_length=128)
    cart_ref: str | None = Field(default=None, max_length=128)
    product_ref: str | None = Field(default=None, max_length=128)
    variant_ref: str | None = Field(default=None, max_length=128)
    device_class: Literal["desktop", "mobile", "tablet", "other"]
    traffic_source: str | None = Field(default=None, max_length=128)
    request_id: str | None = Field(default=None, max_length=128)
    data_origin: Literal["manual", "synthetic"]
    payload: dict[str, Any] = Field(default_factory=dict)

    @field_validator("event_time")
    @classmethod
    def event_time_must_have_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("event_time must include timezone")
        return value

    @model_validator(mode="after")
    def validate_schema_version(self) -> "WebEvent":
        if self.schema_version == 1 and self.traffic_source is not None:
            raise ValueError("traffic_source is only supported from schema version 2")
        return self


class AcceptedEvent(BaseModel):
    event_id: UUID
    accepted: bool = True
    duplicate: bool = False
