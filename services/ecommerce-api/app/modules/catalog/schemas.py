from typing import Literal

from pydantic import BaseModel

ProductSort = Literal["newest", "price_asc", "price_desc"]


class CategoryResponse(BaseModel):
    public_id: str
    code: str
    name: str
    parent_code: str | None = None


class VariantResponse(BaseModel):
    public_id: str
    sku: str
    size_code: str
    color_code: str
    price_vnd: int
    stock_quantity: int
    in_stock: bool


class ProductListItem(BaseModel):
    public_id: str
    slug: str
    name: str
    image_url: str | None
    category_code: str
    min_price_vnd: int | None
    in_stock: bool


class ProductListResponse(BaseModel):
    items: list[ProductListItem]
    next_cursor: str | None = None


class CatalogFacetsResponse(BaseModel):
    sizes: list[str]
    colors: list[str]
    min_price_vnd: int | None
    max_price_vnd: int | None


class ProductDetailResponse(BaseModel):
    public_id: str
    slug: str
    name: str
    description: str | None
    image_url: str | None
    category_code: str
    category_name: str
    variants: list[VariantResponse]
