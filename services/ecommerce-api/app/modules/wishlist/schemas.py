from datetime import datetime

from pydantic import BaseModel


class WishlistItemResponse(BaseModel):
    product_public_id: str
    slug: str
    name: str
    image_url: str | None
    category_code: str
    min_price_vnd: int | None
    in_stock: bool
    is_available: bool
    first_added_at: datetime
    last_added_at: datetime


class WishlistResponse(BaseModel):
    items: list[WishlistItemResponse]
