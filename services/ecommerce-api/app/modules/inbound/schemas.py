from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class InboundReceiptItemPayload(BaseModel):
    variant_id: int
    quantity: int = Field(ge=1)
    unit_cost_vnd: int = Field(ge=0)


class CreateInboundReceiptPayload(BaseModel):
    batch_name: str = Field(min_length=3, max_length=255)
    notes: str | None = Field(default=None, max_length=2000)
    items: list[InboundReceiptItemPayload] = Field(min_length=1, max_length=200)

    @field_validator("items")
    @classmethod
    def validate_unique_variants(cls, v: list[InboundReceiptItemPayload]):
        ids = [item.variant_id for item in v]
        if len(ids) != len(set(ids)):
            raise ValueError("Danh sách sản phẩm nhập không được chứa mã variant trùng lặp.")
        return v


class InboundReceiptItemDetailResponse(BaseModel):
    item_id: int
    variant_id: int
    product_name: str
    sku: str
    size_code: str
    color_code: str
    quantity: int
    unit_cost_vnd: int
    total_cost_vnd: int
    previous_cost_price_vnd: int
    new_cost_price_vnd: int


class InboundReceiptDetailResponse(BaseModel):
    receipt_id: int
    receipt_code: str
    batch_name: str
    status: str
    total_items_count: int
    total_cost_vnd: int
    notes: str | None = None
    created_by_name: str | None = None
    created_at: datetime
    items: list[InboundReceiptItemDetailResponse]


class InboundReceiptSummaryResponse(BaseModel):
    receipt_id: int
    receipt_code: str
    batch_name: str
    status: str
    total_items_count: int
    total_cost_vnd: int
    created_by_name: str | None = None
    created_at: datetime


class InboundReceiptListResponse(BaseModel):
    items: list[InboundReceiptSummaryResponse]
    total: int
    total_items_count: int = 0
    total_cost_vnd: int = 0
