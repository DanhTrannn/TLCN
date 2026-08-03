from pydantic import BaseModel, ConfigDict, Field


class SetItemRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    quantity: int = Field(ge=1)


class CartItemResponse(BaseModel):
    variant_public_id: str
    product_name: str
    slug: str
    sku: str
    size_code: str
    color_code: str
    image_url: str | None
    unit_price_vnd: int
    quantity: int
    line_total_vnd: int
    in_stock: bool


class CartResponse(BaseModel):
    public_id: str | None
    items: list[CartItemResponse]
    subtotal_vnd: int
    shipping_fee_vnd: int
    free_shipping_threshold_vnd: int
    total_vnd: int
