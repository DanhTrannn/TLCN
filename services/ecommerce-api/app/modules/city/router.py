from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError, forbidden, not_found
from app.db.deps import get_current_staff, get_db
from app.models.customer import Customer
from app.models.multicity import City
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


def _resolve_city_id(db: Session, actor: Customer, city_id: int | None) -> int:
    if actor.role == "city_planner":
        if not actor.city_id:
            raise forbidden("Tài khoản không gắn với thành phố nào.")
        return actor.city_id
    if actor.role == "admin":
        if city_id is not None:
            return city_id
        first_city = db.execute(
            select(City).where(City.is_active == True).order_by(City.city_id).limit(1)
        ).scalar_one_or_none()
        if first_city is None:
            raise not_found("Không có thành phố nào.")
        return first_city.city_id
    raise forbidden("Chỉ quản lý thành phố hoặc quản trị viên mới có quyền truy cập.")


@admin_city_router.get("/dashboard", response_model=CityDashboardResponse)
def city_dashboard(
    city_id: int | None = Query(default=None, gt=0),
    actor: Customer = Depends(get_current_staff),
    db: Session = Depends(get_db),
) -> CityDashboardResponse:
    resolved_city_id = _resolve_city_id(db, actor, city_id)
    return get_city_dashboard(db, resolved_city_id)


@admin_city_router.get("/stores", response_model=list[CityStoreResponse])
def city_stores(
    city_id: int | None = Query(default=None, gt=0),
    actor: Customer = Depends(get_current_staff),
    db: Session = Depends(get_db),
) -> list[CityStoreResponse]:
    resolved_city_id = _resolve_city_id(db, actor, city_id)
    return list_city_stores(db, resolved_city_id)


@admin_city_router.get("/orders", response_model=list[CityOrderResponse])
def city_orders(
    status: str | None = Query(
        default=None,
        pattern=r"^(paid|payment_failed|confirmed|completed|cancelled)$",
    ),
    store_id: int | None = Query(default=None, gt=0),
    city_id: int | None = Query(default=None, gt=0),
    actor: Customer = Depends(get_current_staff),
    db: Session = Depends(get_db),
) -> list[CityOrderResponse]:
    resolved_city_id = _resolve_city_id(db, actor, city_id)
    return list_city_orders(db, resolved_city_id, status, store_id)


@admin_city_router.get("/inventory", response_model=list[CityInventoryItem])
def city_inventory(
    city_id: int | None = Query(default=None, gt=0),
    actor: Customer = Depends(get_current_staff),
    db: Session = Depends(get_db),
) -> list[CityInventoryItem]:
    resolved_city_id = _resolve_city_id(db, actor, city_id)
    return list_city_inventory(db, resolved_city_id)
