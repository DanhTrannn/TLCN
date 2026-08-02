from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator


class AdminOverviewResponse(BaseModel):
    active_products: int
    active_variants: int
    low_stock_variants: int
    customers: int
    paid_orders: int
    confirmed_orders: int
    completed_orders: int
    cancelled_orders: int
    pending_reviews: int
    active_coupons: int
    gross_revenue_vnd: int
    refunded_amount_vnd: int
    net_revenue_vnd: int


class AdminVariantResponse(BaseModel):
    public_id: str
    sku: str
    size_code: str
    color_code: str
    price_vnd: int
    is_active: bool
    on_hand: int


class AdminProductResponse(BaseModel):
    public_id: str
    category_code: str
    slug: str
    name: str
    description: str | None
    image_url: str | None
    is_active: bool
    variants: list[AdminVariantResponse]


class CreateVariantRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    sku: str = Field(min_length=1, max_length=64)
    size_code: str = Field(min_length=1, max_length=32)
    color_code: str = Field(min_length=1, max_length=64)
    price_vnd: int = Field(ge=0)
    opening_on_hand: int = Field(ge=0)


class CreateProductRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    category_code: str = Field(min_length=1, max_length=64)
    slug: str = Field(min_length=1, max_length=180, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    image_url: HttpUrl | None = None
    variants: list[CreateVariantRequest] = Field(min_length=1, max_length=50)

    @model_validator(mode="after")
    def validate_unique_variants(self) -> "CreateProductRequest":
        skus = [variant.sku.upper() for variant in self.variants]
        combinations = [
            (variant.size_code.lower(), variant.color_code.lower()) for variant in self.variants
        ]
        if len(skus) != len(set(skus)):
            raise ValueError("SKU trong sản phẩm không được trùng nhau.")
        if len(combinations) != len(set(combinations)):
            raise ValueError("Tổ hợp size và màu trong sản phẩm không được trùng nhau.")
        return self


class UpdateProductRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    category_code: str | None = Field(default=None, min_length=1, max_length=64)
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    image_url: HttpUrl | None = None
    is_active: bool | None = None

    @model_validator(mode="after")
    def validate_non_nullable_fields(self) -> "UpdateProductRequest":
        for field in ("category_code", "name", "is_active"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} không được là null.")
        return self


class UpdateVariantRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    price_vnd: int | None = Field(default=None, ge=0)
    is_active: bool | None = None

    @model_validator(mode="after")
    def require_change(self) -> "UpdateVariantRequest":
        if not self.model_fields_set:
            raise ValueError("Cần ít nhất một thay đổi cho biến thể.")
        return self


class AdminOrderResponse(BaseModel):
    order_number: str
    customer_name: str
    customer_email: str
    status: str
    total_vnd: int
    item_count: int
    created_at: datetime


class AdminCustomerResponse(BaseModel):
    public_id: str
    display_name: str
    email: str
    status: str
    role: str
    created_at: datetime


class UpdateCustomerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str = Field(pattern=r"^(active|inactive)$")
