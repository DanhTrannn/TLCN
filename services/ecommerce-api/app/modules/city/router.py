from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.errors import AppError, forbidden
from app.db.deps import get_current_staff, get_db
from app.models.customer import Customer
from app.modules.city.schemas import (
    CityDashboardResponse,
    CityInventoryItem,
    CityOrderResponse,
    CityStoreResponse,
)
from app.modules.city.service import (
    get_city_dashboard,
    list_city_inventory,
    list_city_orders,
    list_city_stores,
)

admin_city_router = APIRouter(prefix="/admin/city", tags=["admin-city"])


def _require_city_planner(actor: Customer) -> None:
    if actor.role != "city_planner" or not actor.city_id:
        raise forbidden("Chỉ quản lý thành phố mới có quyền truy cập.")


@admin_city_router.get("/dashboard", response_model=CityDashboardResponse)
def city_dashboard(
    actor: Customer = Depends(get_current_staff),
    db: Session = Depends(get_db),
) -> CityDashboardResponse:
    _require_city_planner(actor)
    return get_city_dashboard(db, actor.city_id)


@admin_city_router.get("/stores", response_model=list[CityStoreResponse])
def city_stores(
    actor: Customer = Depends(get_current_staff),
    db: Session = Depends(get_db),
) -> list[CityStoreResponse]:
    _require_city_planner(actor)
    return list_city_stores(db, actor.city_id)


@admin_city_router.get("/orders", response_model=list[CityOrderResponse])
def city_orders(
    status: str | None = Query(
        default=None,
        pattern=r"^(paid|payment_failed|confirmed|completed|cancelled)$",
    ),
    store_id: int | None = Query(default=None, gt=0),
    actor: Customer = Depends(get_current_staff),
    db: Session = Depends(get_db),
) -> list[CityOrderResponse]:
    _require_city_planner(actor)
    return list_city_orders(db, actor.city_id, status, store_id)


@admin_city_router.get("/inventory", response_model=list[CityInventoryItem])
def city_inventory(
    actor: Customer = Depends(get_current_staff),
    db: Session = Depends(get_db),
) -> list[CityInventoryItem]:
    _require_city_planner(actor)
    return list_city_inventory(db, actor.city_id)
