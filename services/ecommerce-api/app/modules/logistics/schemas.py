from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DeliveryStaffCreateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    full_name: str = Field(min_length=2, max_length=100)
    phone: str = Field(min_length=8, max_length=20)
    vehicle_plate: str | None = Field(default=None, max_length=30)


class DeliveryStaffUpdateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    full_name: str | None = Field(default=None, min_length=2, max_length=100)
    phone: str | None = Field(default=None, min_length=8, max_length=20)
    vehicle_plate: str | None = Field(default=None, max_length=30)
    is_active: bool | None = None


class DeliveryStaffResponse(BaseModel):
    staff_id: int
    public_id: str
    full_name: str
    phone: str
    vehicle_plate: str | None
    is_active: bool
    created_at: datetime


class ShipmentResponse(BaseModel):
    shipment_id: int
    shipment_code: str
    order_id: int
    order_number: str
    delivery_staff_id: int | None
    delivery_staff_name: str | None
    delivery_staff_phone: str | None
    status: str
    attempt_count: int
    cod_amount_vnd: int
    cod_collected_vnd: int
    dispatched_at: datetime | None
    delivered_at: datetime | None
    failed_at: datetime | None
    failure_reason: str | None
    notes: str | None
