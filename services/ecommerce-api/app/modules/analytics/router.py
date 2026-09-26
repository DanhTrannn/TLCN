"""FastAPI router for analytics endpoints with RBAC enforcement."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.errors import FORBIDDEN, AppError
from app.db.deps import get_current_admin, get_current_staff, get_db
from app.models.customer import Customer
from app.modules.admin.schemas import AdminOverviewResponse
from app.modules.admin.service import get_overview
from app.modules.analytics.schemas import (
    RoleMetricsResponse,
    SalesTrendResponse,
)
from app.modules.analytics.service import (
    get_role_metrics_data,
    get_sales_trend,
    resolve_effective_store_id,
    validate_role_access,
)

router = APIRouter(prefix="/admin/analytics", tags=["admin-analytics"])


@router.get("/overview", response_model=AdminOverviewResponse)
def get_analytics_overview(
    db: Session = Depends(get_db),
    admin: Customer = Depends(get_current_admin),
) -> AdminOverviewResponse:
    """Financial & Operational System-wide Overview (Admin only)."""
    return get_overview(db)


@router.get("/role-metrics", response_model=RoleMetricsResponse)
def get_role_metrics(
    target_role: str = Query(..., description="Target business role name or alias"),
    store_id: int | None = Query(None, description="Optional store filter for store metrics"),
    actor: Customer = Depends(get_current_staff),
    db: Session = Depends(get_db),
) -> RoleMetricsResponse:
    """Role-based metrics aggregation with strict RBAC security check backed by Trino Lakehouse DWH."""
    validate_role_access(actor=actor, target_role=target_role, store_id=store_id)
    effective_store_id = resolve_effective_store_id(actor=actor, target_role=target_role, store_id=store_id)
    return get_role_metrics_data(target_role=target_role, store_id=effective_store_id, db=db)


@router.get("/sales-trend", response_model=SalesTrendResponse)
def get_analytics_sales_trend(
    days: int = Query(30, ge=1, le=365, description="Number of days for sales trend"),
    actor: Customer = Depends(get_current_staff),
) -> SalesTrendResponse:
    """Daily revenue, COGS, and profit trend (Admin or Sales Manager only)."""
    if actor.role not in ("admin", "sales_manager"):
        raise AppError(
            FORBIDDEN,
            "Chỉ quản trị viên hoặc trưởng phòng kinh doanh mới có quyền truy cập biểu đồ xu hướng.",
            status_code=403,
        )
    return get_sales_trend(days=days)
