from pydantic import BaseModel, ConfigDict, Field


class CheckoutRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    receiver_name: str = Field(min_length=1, max_length=160)
    receiver_phone: str = Field(min_length=1, max_length=32)
    shipping_address_text: str = Field(min_length=1, max_length=1000)


class CheckoutResultResponse(BaseModel):
    order_number: str
    status: str
    payment_status: str
    failure_code: str | None
    subtotal_vnd: int
    shipping_fee_vnd: int
    total_vnd: int
