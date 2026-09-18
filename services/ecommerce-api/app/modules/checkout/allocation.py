from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.inventory import Inventory

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


def deduct_inventory(db: Session, items: list[dict]) -> None:
    """Deduct central inventory (inventory table) for online orders."""
    for item in items:
        stmt = (
            select(Inventory)
            .where(Inventory.variant_id == item["variant_id"])
            .with_for_update()
        )
        inv = db.execute(stmt).scalar_one_or_none()
        if inv is None or inv.on_hand < item["quantity"]:
            from app.core.errors import AppError, OUT_OF_STOCK
            raise AppError(OUT_OF_STOCK, "Sản phẩm không đủ tồn kho.", status_code=409)
        inv.on_hand -= item["quantity"]
        inv.version += 1


def allocate_order_to_stores(db, order_id, shipping_address, items):
    raise NotImplementedError("Store allocation removed. Task 2 will update the checkout service.")
