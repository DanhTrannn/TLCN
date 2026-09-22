"""Pydantic schemas for RBAC analytics and role-based metrics."""

from pydantic import BaseModel, ConfigDict, Field


class ExecutiveMetricsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    role: str = "executive"
    gmv_vnd: int = 0
    net_revenue_vnd: int = 0
    cogs_vnd: int = 0
    gross_profit_vnd: int = 0
    gross_margin_percent: float = 0.0
    total_orders: int = 0
    aov_vnd: int = 0
    boom_rate_percent: float = 0.0
    return_rate_percent: float = 0.0


class StoreContribution(BaseModel):
    store_id: int | None = None
    store_name: str
    revenue_vnd: int = 0
    order_count: int = 0


class TopProductMetric(BaseModel):
    product_id: int
    product_name: str
    units_sold: int = 0
    revenue_vnd: int = 0


class CategoryShareMetric(BaseModel):
    category_id: int
    category_name: str
    revenue_vnd: int = 0
    share_percent: float = 0.0


class SalesMetricsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    role: str = "sales"
    store_contributions: list[StoreContribution] = Field(default_factory=list)
    top_selling_products: list[TopProductMetric] = Field(default_factory=list)
    category_shares: list[CategoryShareMetric] = Field(default_factory=list)


class FunnelStep(BaseModel):
    step_name: str
    count: int
    conversion_rate_percent: float = 0.0


class MarketingMetricsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    role: str = "marketing"
    funnel_steps: list[FunnelStep] = Field(default_factory=list)
    conversion_rate_percent: float = 0.0
    total_visitors: int = 0
    total_purchases: int = 0


class StoreMetricsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    role: str = "store"
    store_id: int | None = None
    store_name: str | None = None
    store_revenue_today_vnd: int = 0
    store_orders_count: int = 0
    target_achievement_percent: float = 0.0
    low_stock_at_store_count: int = 0


class InventoryMetricsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    role: str = "inventory"
    total_inventory_value_vnd: int = 0
    warehouse_stock_units: int = 0
    store_stock_units: int = 0
    inbound_batches_count: int = 0
    stockout_count: int = 0


class OperationsMetricsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    role: str = "operations"
    pending_fulfillment_count: int = 0
    shipping_sla_violations_count: int = 0
    boom_orders_count: int = 0
    return_requests_count: int = 0


class ReconciliationVariance(BaseModel):
    metric_name: str
    oltp_value: float
    lakehouse_value: float
    variance_percent: float


class SystemMetricsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    role: str = "system"
    pipeline_status: str = "healthy"
    data_freshness_sla_minutes: int = 15
    reconciliation_variance: list[ReconciliationVariance] = Field(default_factory=list)


class DailySalesTrendPoint(BaseModel):
    date: str
    revenue_vnd: int = 0
    cogs_vnd: int = 0
    profit_vnd: int = 0
    orders_count: int = 0


class SalesTrendResponse(BaseModel):
    days: int = 30
    points: list[DailySalesTrendPoint] = Field(default_factory=list)


class SupersetConfigResponse(BaseModel):
    superset_url: str = "http://localhost:8088"
    enabled: bool = True
    guest_token_enabled: bool = False


RoleMetricsResponse = (
    ExecutiveMetricsResponse
    | SalesMetricsResponse
    | MarketingMetricsResponse
    | StoreMetricsResponse
    | InventoryMetricsResponse
    | OperationsMetricsResponse
    | SystemMetricsResponse
)
