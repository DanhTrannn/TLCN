from datetime import datetime

from pydantic import BaseModel


class OrderListItem(BaseModel):
    order_number: str
    status: str
    total_vnd: int
    item_count: int
    created_at: datetime


class OrderListResponse(BaseModel):
    items: list[OrderListItem]
    next_cursor: str | None = None


class OrderItemResponse(BaseModel):
    product_name: str
    sku: str
    size_code: str
    color_code: str
    unit_price_vnd: int
    quantity: int
    line_total_vnd: int


class PaymentResponse(BaseModel):
    payment_reference: str
    status: str
    amount_vnd: int
    failure_code: str | None
    attempted_at: datetime


class StatusHistoryResponse(BaseModel):
    from_status: str | None
    to_status: str
    transition_source: str
    transitioned_at: datetime


class OrderDetailResponse(BaseModel):
    order_number: str
    status: str
    currency_code: str
    subtotal_vnd: int
    shipping_fee_vnd: int
    total_vnd: int
    receiver_name: str
    receiver_phone: str
    shipping_address_text: str
    created_at: datetime
    paid_at: datetime | None
    completed_at: datetime | None
    items: list[OrderItemResponse]
    payment: PaymentResponse | None
    status_history: list[StatusHistoryResponse]
