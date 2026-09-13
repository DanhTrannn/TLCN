from pydantic import BaseModel


class CityResponse(BaseModel):
    code: str
    name: str
    store_count: int


class StoreResponse(BaseModel):
    code: str
    name: str
    address: str
    phone: str


class StoreStock(BaseModel):
    store_code: str
    store_name: str
    variant_public_id: str
    sku: str
    size_code: str
    color_code: str
    price_vnd: int
    on_hand: int


class VariantAvailability(BaseModel):
    variant_public_id: str
    sku: str
    size_code: str
    color_code: str
    price_vnd: int
    total_on_hand: int
    in_stock: bool
    stores: list[StoreStock]


class ProductAvailabilityResponse(BaseModel):
    product_slug: str
    product_name: str
    variants: list[VariantAvailability]
