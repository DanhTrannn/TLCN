"""Gold builders grouped by business domain; no table I/O."""

from .dimensions import build_dim_date
from .dimensions import build_dim_product
from .dimensions import build_dim_variant
from .dimensions import build_dim_store
from .dimensions import build_dim_delivery_staff
from .dimensions import build_dim_customer
from .sales import build_fact_order
from .sales import build_fact_order_item
from .sales import build_mart_sales_daily
from .logistics import build_fact_shipment
from .logistics import build_mart_logistics_performance
from .returns import build_fact_return_exchange
from .returns import build_mart_product_returns
from .inventory import build_fact_inventory_daily_snapshot
from .inventory import build_mart_inventory_health

__all__ = [
    "build_dim_date",
    "build_dim_product",
    "build_dim_variant",
    "build_dim_store",
    "build_dim_delivery_staff",
    "build_dim_customer",
    "build_fact_order",
    "build_fact_order_item",
    "build_mart_sales_daily",
    "build_fact_shipment",
    "build_mart_logistics_performance",
    "build_fact_return_exchange",
    "build_mart_product_returns",
    "build_fact_inventory_daily_snapshot",
    "build_mart_inventory_health",
]
