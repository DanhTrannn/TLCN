from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import not_found
from app.models.catalog import Product, ProductVariant
from app.models.multicity import City, Store, StoreInventory
from app.modules.location.schemas import (
    CityResponse,
    ProductAvailabilityResponse,
    StoreResponse,
    StoreStock,
    VariantAvailability,
)


def list_active_cities(db: Session) -> list[CityResponse]:
    store_count = (
        select(Store.city_id, func.count(Store.store_id).label("store_count"))
        .where(Store.is_active.is_(True))
        .group_by(Store.city_id)
        .subquery()
    )
    rows = db.execute(
        select(
            City.code,
            City.name,
            func.coalesce(store_count.c.store_count, 0).label("store_count"),
        )
        .outerjoin(store_count, store_count.c.city_id == City.city_id)
        .where(City.is_active.is_(True))
        .order_by(City.name)
    ).all()
    return [
        CityResponse(code=row.code, name=row.name, store_count=int(row.store_count))
        for row in rows
    ]


def list_stores_by_city(db: Session, city_code: str) -> list[StoreResponse]:
    city = db.execute(
        select(City).where(City.code == city_code, City.is_active.is_(True))
    ).scalar_one_or_none()
    if city is None:
        raise not_found("Không tìm thấy thành phố.")
    rows = db.execute(
        select(Store)
        .where(Store.city_id == city.city_id, Store.is_active.is_(True))
        .order_by(Store.name)
    ).scalars().all()
    return [
        StoreResponse(code=s.code, name=s.name, address=s.address, phone=s.phone)
        for s in rows
    ]


def get_product_availability(
    db: Session, slug: str, city_code: str
) -> ProductAvailabilityResponse:
    city = db.execute(
        select(City).where(City.code == city_code, City.is_active.is_(True))
    ).scalar_one_or_none()
    if city is None:
        raise not_found("Không tìm thấy thành phố.")

    product = db.execute(
        select(Product).where(Product.slug == slug, Product.is_active.is_(True))
    ).scalar_one_or_none()
    if product is None:
        raise not_found("Không tìm thấy sản phẩm.")

    city_store_ids = db.execute(
        select(Store.store_id).where(
            Store.city_id == city.city_id, Store.is_active.is_(True)
        )
    ).scalars().all()

    variants = db.execute(
        select(ProductVariant).where(
            ProductVariant.product_id == product.product_id,
            ProductVariant.is_active.is_(True),
        )
    ).scalars().all()

    variant_availability: list[VariantAvailability] = []
    for v in variants:
        if not city_store_ids:
            stocks: list[StoreStock] = []
        else:
            stock_rows = db.execute(
                select(
                    Store.code.label("store_code"),
                    Store.name.label("store_name"),
                    ProductVariant.public_id,
                    ProductVariant.sku,
                    ProductVariant.size_code,
                    ProductVariant.color_code,
                    ProductVariant.price_vnd,
                    StoreInventory.on_hand,
                )
                .select_from(StoreInventory)
                .join(Store, Store.store_id == StoreInventory.store_id)
                .join(ProductVariant, ProductVariant.variant_id == StoreInventory.variant_id)
                .where(
                    StoreInventory.store_id.in_(city_store_ids),
                    StoreInventory.on_hand > 0,
                    StoreInventory.variant_id == v.variant_id,
                )
                .order_by(Store.name)
            ).all()
            stocks = [
                StoreStock(
                    store_code=row.store_code,
                    store_name=row.store_name,
                    variant_public_id=str(row.public_id),
                    sku=row.sku,
                    size_code=row.size_code,
                    color_code=row.color_code,
                    price_vnd=row.price_vnd,
                    on_hand=row.on_hand,
                )
                for row in stock_rows
            ]

        total_on_hand = sum(s.on_hand for s in stocks)
        variant_availability.append(
            VariantAvailability(
                variant_public_id=str(v.public_id),
                sku=v.sku,
                size_code=v.size_code,
                color_code=v.color_code,
                price_vnd=v.price_vnd,
                total_on_hand=total_on_hand,
                in_stock=total_on_hand > 0,
                stores=stocks,
            )
        )

    return ProductAvailabilityResponse(
        product_slug=product.slug,
        product_name=product.name,
        variants=variant_availability,
    )
