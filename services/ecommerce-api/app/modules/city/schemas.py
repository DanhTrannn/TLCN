from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CityDashboardResponse(BaseModel):
    city_name: str
    total_stores: int
    active_stores: int
    total_orders: int
    completed_orders: int
    total_revenue_vnd: int
    total_staff: int
    low_stock_items: int


class CityStoreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    store_id: int
    code: str
    name: str
    address: str
    phone: str
    is_active: bool
    created_at: datetime


class CityOrderResponse(BaseModel):
    order_number: str
    store_name: str
    customer_name: str
    status: str
    total_vnd: int
    item_count: int
    channel: str
    created_at: datetime


class CityInventoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    store_id: int
    store_name: str
    variant_id: int
    variant_sku: str
    product_name: str
    category_name: str
    size_code: str
    color_code: str
    price_vnd: int
    on_hand: int
