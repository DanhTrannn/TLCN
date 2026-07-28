from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.modules.catalog.schemas import (
    CatalogFacetsResponse,
    CategoryResponse,
    ProductDetailResponse,
    ProductListResponse,
)
from app.modules.catalog.service import (
    get_catalog_facets,
    get_product_detail,
    list_categories,
    list_products,
)

router = APIRouter(tags=["catalog"])


@router.get("/categories", response_model=list[CategoryResponse])
def get_categories(db: Session = Depends(get_db)) -> list[CategoryResponse]:
    return list_categories(db)


@router.get("/catalog/facets", response_model=CatalogFacetsResponse)
def get_facets(db: Session = Depends(get_db)) -> CatalogFacetsResponse:
    return get_catalog_facets(db)


@router.get("/products", response_model=ProductListResponse)
def get_products(
    category: str | None = Query(default=None, max_length=64),
    q: str | None = Query(default=None, max_length=100),
    size: list[str] | None = Query(default=None),
    color: list[str] | None = Query(default=None),
    min_price: int | None = Query(default=None, ge=0),
    max_price: int | None = Query(default=None, ge=0),
    in_stock: bool = Query(default=False),
    sort: Literal["newest", "price_asc", "price_desc"] = Query(default="newest"),
    cursor: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> ProductListResponse:
    return list_products(
        db=db,
        category_code=category,
        query=q,
        sizes=size,
        colors=color,
        min_price_vnd=min_price,
        max_price_vnd=max_price,
        in_stock_only=in_stock,
        sort=sort,
        cursor=cursor,
    )


@router.get("/products/{slug}", response_model=ProductDetailResponse)
def get_product(slug: str, db: Session = Depends(get_db)) -> ProductDetailResponse:
    return get_product_detail(db, slug)
