from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ReturnItemCreatePayload(BaseModel):
    order_item_id: int
    quantity: int = Field(ge=1)


class CreateReturnRequestPayload(BaseModel):
    customer_reason: str = Field(min_length=5, max_length=1000)
    bank_name: str = Field(min_length=2, max_length=100)
    bank_account_number: str = Field(min_length=4, max_length=50)
    bank_account_holder: str = Field(min_length=2, max_length=150)
    image_urls: list[str] = Field(default_factory=list)
    items: list[ReturnItemCreatePayload] = Field(min_length=1)


class ReturnItemDetailResponse(BaseModel):
    return_item_id: int
    order_item_id: int
    variant_id: int
    product_name: str | None = None
    variant_title: str | None = None
    sku: str | None = None
    quantity: int
    refund_amount_vnd: int
    inspection_status: str


class ReturnRequestDetailResponse(BaseModel):
    return_id: int
    return_code: str
    order_id: int
    order_number: str
    customer_name: str | None = None
    customer_phone: str | None = None
    customer_email: str | None = None
    action_type: str
    status: str
    customer_reason: str
    admin_note: str | None = None
    image_urls: list[str] = Field(default_factory=list)
    bank_info: dict | None = None
    total_refund_amount_vnd: int
    created_at: datetime
    reviewed_at: datetime | None = None
    resolved_at: datetime | None = None
    items: list[ReturnItemDetailResponse] = Field(default_factory=list)


class ReturnRequestSummaryResponse(BaseModel):
    return_id: int
    return_code: str
    order_number: str
    action_type: str
    status: str
    total_items_count: int
    total_refund_amount_vnd: int
    created_at: datetime


class ReturnRequestListResponse(BaseModel):
    items: list[ReturnRequestSummaryResponse]
    total: int


class AdminReviewReturnPayload(BaseModel):
    action: Literal["approved", "rejected"]
    admin_note: str | None = None


class AdminInspectItemPayload(BaseModel):
    return_item_id: int
    inspection_status: Literal["passed", "failed"]


class AdminInspectAndResolvePayload(BaseModel):
    items: list[AdminInspectItemPayload] = Field(min_length=1)
    admin_note: str | None = None


class AdminReturnListResponse(BaseModel):
    items: list[ReturnRequestDetailResponse]
    total: int
