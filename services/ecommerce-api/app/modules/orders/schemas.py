from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class OrderListPreviewItem(BaseModel):
    product_name: str
    image_url: str | None
    sku: str
    size_code: str
    color_code: str
    quantity: int
    line_total_vnd: int


class OrderListItem(BaseModel):
    order_number: str
    status: str
    total_vnd: int
    item_count: int
    created_at: datetime
    preview_items: list[OrderListPreviewItem]


class OrderListResponse(BaseModel):
    items: list[OrderListItem]
    next_cursor: str | None = None


class OrderItemReviewResponse(BaseModel):
    public_id: str
    rating: int
    content: str | None
    status: str
    moderation_reason: str | None


class OrderItemResponse(BaseModel):
    public_id: str
    product_public_id: str
    image_url: str | None
    product_name: str
    sku: str
    size_code: str
    color_code: str
    unit_price_vnd: int
    quantity: int
    line_total_vnd: int
    review: OrderItemReviewResponse | None


class PaymentResponse(BaseModel):
    payment_reference: str
    status: str
    amount_vnd: int
    failure_code: str | None
    attempted_at: datetime


class RefundResponse(BaseModel):
    public_id: str
    status: str
    amount_vnd: int
    reason: str
    created_at: datetime
    completed_at: datetime | None


class StatusHistoryResponse(BaseModel):
    from_status: str | None
    to_status: str
    transition_source: str
    reason: str | None
    transitioned_at: datetime


class OrderDetailResponse(BaseModel):
    order_number: str
    status: str
    currency_code: str
    subtotal_vnd: int
    coupon_code: str | None
    discount_amount_vnd: int
    shipping_fee_vnd: int
    total_vnd: int
    receiver_name: str
    receiver_phone: str
    shipping_address_text: str
    created_at: datetime
    paid_at: datetime | None
    confirmed_at: datetime | None
    completed_at: datetime | None
    cancelled_at: datetime | None
    items: list[OrderItemResponse]
    payment: PaymentResponse | None
    refund: RefundResponse | None
    status_history: list[StatusHistoryResponse]


class CancelOrderRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    reason: str = Field(min_length=3, max_length=500)


class OrderTransitionResponse(BaseModel):
    order_number: str
    status: str
    refunded_amount_vnd: int | None = None
