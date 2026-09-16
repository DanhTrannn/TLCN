from datetime import datetime

from pydantic import BaseModel, ConfigDict


class StoreDashboardResponse(BaseModel):
    store_name: str
    revenue_vnd: int
    orders_today: int
    low_stock_count: int


class StoreOrderResponse(BaseModel):
    order_number: str
    customer_name: str
    customer_email: str
    channel: str
    status: str
    total_vnd: int
    item_count: int
    created_at: datetime


class StoreInventoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    variant_id: int
    sku: str
    product_name: str
    size_code: str
    color_code: str
    price_vnd: int
    on_hand: int
    opening_on_hand: int


class StoreStaffMember(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    customer_id: int
    public_id: str
    display_name: str
    email: str
    status: str
    created_at: datetime
