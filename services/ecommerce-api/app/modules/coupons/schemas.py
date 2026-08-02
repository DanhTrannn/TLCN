from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class CheckoutQuoteRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    coupon_code: str | None = Field(default=None, max_length=64)

    @field_validator("coupon_code")
    @classmethod
    def normalize_empty_code(cls, value: str | None) -> str | None:
        return value or None


class CheckoutQuoteResponse(BaseModel):
    coupon_code: str | None
    discount_type: str | None
    discount_value: int | None
    subtotal_vnd: int
    discount_amount_vnd: int
    shipping_fee_vnd: int
    total_vnd: int


class AvailableCouponResponse(BaseModel):
    code: str
    discount_type: Literal["percentage", "fixed_amount"]
    discount_value: int
    minimum_subtotal_vnd: int
    discount_amount_vnd: int
    ends_at: datetime
    remaining_uses: int | None


class AvailableCouponListResponse(BaseModel):
    subtotal_vnd: int
    items: list[AvailableCouponResponse]


class CouponResponse(BaseModel):
    public_id: str
    code: str
    discount_type: str
    discount_value: int
    minimum_subtotal_vnd: int
    starts_at: datetime
    ends_at: datetime
    is_active: bool
    total_usage_limit: int | None
    per_customer_usage_limit: int | None
    used_count: int
    created_at: datetime
    updated_at: datetime


class CreateCouponRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    code: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    discount_type: str = Field(pattern=r"^(percentage|fixed_amount)$")
    discount_value: int = Field(gt=0)
    minimum_subtotal_vnd: int = Field(default=0, ge=0)
    starts_at: datetime
    ends_at: datetime
    total_usage_limit: int | None = Field(default=None, gt=0)
    per_customer_usage_limit: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_coupon(self) -> "CreateCouponRequest":
        if self.discount_type == "percentage" and self.discount_value > 100:
            raise ValueError("Coupon phần trăm phải từ 1 đến 100.")
        if self.starts_at >= self.ends_at:
            raise ValueError("Thời điểm kết thúc phải sau thời điểm bắt đầu.")
        return self


class UpdateCouponRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_active: bool
