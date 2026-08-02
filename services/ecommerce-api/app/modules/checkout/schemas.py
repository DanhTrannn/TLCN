from pydantic import BaseModel, ConfigDict, Field, field_validator


class CheckoutRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    receiver_name: str = Field(min_length=1, max_length=160)
    receiver_phone: str = Field(min_length=1, max_length=32)
    shipping_address_text: str = Field(min_length=1, max_length=1000)
    coupon_code: str | None = Field(default=None, max_length=64)

    @field_validator("coupon_code")
    @classmethod
    def normalize_empty_code(cls, value: str | None) -> str | None:
        return value or None


class CheckoutResultResponse(BaseModel):
    order_number: str
    status: str
    payment_status: str
    failure_code: str | None
    coupon_code: str | None
    subtotal_vnd: int
    discount_amount_vnd: int
    shipping_fee_vnd: int
    total_vnd: int
