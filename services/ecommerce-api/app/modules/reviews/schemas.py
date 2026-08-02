from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CreateReviewRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    rating: int = Field(ge=1, le=5)
    content: str | None = Field(default=None, max_length=2000)


class ReviewResponse(BaseModel):
    public_id: str
    rating: int
    content: str | None
    customer_name: str
    created_at: datetime


class ReviewListResponse(BaseModel):
    items: list[ReviewResponse]
    total: int
    average_rating: float | None


class CustomerReviewResponse(BaseModel):
    public_id: str
    rating: int
    content: str | None
    status: str
    moderation_reason: str | None
    created_at: datetime
    updated_at: datetime


class AdminReviewResponse(BaseModel):
    public_id: str
    order_number: str
    product_name: str
    customer_name: str
    rating: int
    content: str | None
    status: str
    moderation_reason: str | None
    created_at: datetime
    updated_at: datetime


class ModerateReviewRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    status: str = Field(pattern=r"^(approved|rejected)$")
    reason: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def require_rejection_reason(self) -> "ModerateReviewRequest":
        if self.status == "rejected" and not self.reason:
            raise ValueError("Cần lý do khi từ chối đánh giá.")
        return self
