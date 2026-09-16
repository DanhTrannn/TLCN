from datetime import datetime

from pydantic import BaseModel, ConfigDict


class StoreDashboardResponse(BaseModel):
    store_name: str
    today_orders: int
    today_revenue_vnd: int
    total_orders: int
    completed_orders: int
    total_revenue_vnd: int
    low_stock_items: int
    active_staff: int


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
    opening_on_hand: int


class StoreStaffMember(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: str
    display_name: str
    email: str
    role: str
    status: str
    created_at: datetime
