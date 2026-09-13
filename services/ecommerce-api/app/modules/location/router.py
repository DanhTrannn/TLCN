from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.deps import get_db, get_optional_customer
from app.modules.location.schemas import (
    CityResponse,
    ProductAvailabilityResponse,
    StoreResponse,
)
from app.modules.location.service import (
    get_product_availability,
    list_active_cities,
    list_stores_by_city,
)

router = APIRouter(
    tags=["location"],
    dependencies=[Depends(get_optional_customer)],
)


@router.get("/locations/cities", response_model=list[CityResponse])
def get_cities(db: Session = Depends(get_db)) -> list[CityResponse]:
    return list_active_cities(db)


@router.get("/locations/cities/{city_code}/stores", response_model=list[StoreResponse])
def get_stores(city_code: str, db: Session = Depends(get_db)) -> list[StoreResponse]:
    return list_stores_by_city(db, city_code)


@router.get(
    "/catalog/products/{slug}/availability",
    response_model=ProductAvailabilityResponse,
)
def get_availability(
    slug: str,
    city_code: str = Query(..., min_length=1, max_length=32),
    db: Session = Depends(get_db),
) -> ProductAvailabilityResponse:
    return get_product_availability(db, slug, city_code)
