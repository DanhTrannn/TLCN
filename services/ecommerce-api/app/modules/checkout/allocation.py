from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.multicity import City, Store, StoreInventory


CITY_PREFIXES = ["Thành phố", "TP.", "TP", "Tỉnh", "T."]


def parse_city_from_address(address: str) -> str | None:
    """Parse city name from shipping address."""
    parts = [p.strip() for p in address.split(",")]
    if len(parts) >= 3:
        city = parts[-1]
        for prefix in CITY_PREFIXES:
            if city.startswith(prefix):
                city = city[len(prefix):].strip()
                break
        return city if city else None
    return None


def find_stores_in_city(db: Session, city_name: str) -> list[Store]:
    """Find all active stores in a city."""
    stmt = (
        select(Store)
        .join(City, City.city_id == Store.city_id)
        .where(City.name.contains(city_name))
        .where(Store.is_active == True)  # noqa: E712
        .where(City.is_active == True)  # noqa: E712
    )
    results = list(db.execute(stmt).scalars().all())
    if not results:
        # Try reverse: city name contains the parsed name
        stmt = (
            select(Store)
            .join(City, City.city_id == Store.city_id)
            .where(City.name.like(f"%{city_name}%"))
            .where(Store.is_active == True)  # noqa: E712
            .where(City.is_active == True)  # noqa: E712
        )
        results = list(db.execute(stmt).scalars().all())
    return results


def find_store_with_all_items(
    db: Session, stores: list[Store], items: list[dict]
) -> Store | None:
    """Find a single store that has ALL items in sufficient quantity."""
    if not stores:
        return None

    for store in stores:
        store_has_all = True
        for item in items:
            stmt = (
                select(StoreInventory.on_hand)
                .where(
                    StoreInventory.store_id == store.store_id,
                    StoreInventory.variant_id == item["variant_id"],
                    StoreInventory.on_hand >= item["quantity"],
                )
            )
            row = db.execute(stmt).first()
            if not row:
                store_has_all = False
                break

        if store_has_all:
            return store

    return None


def allocate_order_to_stores(
    db: Session, order_id: int, shipping_address: str, items: list[dict]
) -> dict:
    """Allocate order to a single store that has ALL items, or fallback to global."""
    city_name = parse_city_from_address(shipping_address)

    allocation_result = {"store_id": None, "source": "global", "allocations": []}

    if not city_name:
        return allocation_result

    stores = find_stores_in_city(db, city_name)
    if not stores:
        return allocation_result

    best_store = find_store_with_all_items(db, stores, items)

    if best_store:
        allocation_result["store_id"] = best_store.store_id
        allocation_result["source"] = "store"
        for item in items:
            allocation_result["allocations"].append({
                "variant_id": item["variant_id"],
                "store_id": best_store.store_id,
                "quantity": item["quantity"],
                "source": "store",
            })
    else:
        for item in items:
            allocation_result["allocations"].append({
                "variant_id": item["variant_id"],
                "store_id": None,
                "quantity": item["quantity"],
                "source": "global",
            })

    return allocation_result
