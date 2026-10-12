from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import OUT_OF_STOCK, AppError
from app.core.ids import uuid7
from app.models.inventory import Inventory
from app.models.inventory_tx import InventoryTransaction

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


def deduct_inventory(
    db: Session, items: list[dict], reference_code: str | None = None
) -> None:
    """Deduct central inventory (inventory table) for online orders and record ledger transaction."""
    now = datetime.now(timezone.utc)
    for item in items:
        stmt = (
            select(Inventory)
            .where(Inventory.variant_id == item["variant_id"])
            .with_for_update()
        )
        inv = db.execute(stmt).scalar_one_or_none()
        if inv is None or inv.on_hand < item["quantity"]:
            raise AppError(OUT_OF_STOCK, "Sản phẩm không đủ tồn kho.", status_code=409)
        inv.on_hand -= item["quantity"]
        inv.version += 1
        db.add(
            InventoryTransaction(
                public_id=uuid7(),
                variant_id=item["variant_id"],
                location_type="central_warehouse",
                store_id=None,
                movement_type="outbound_order",
                quantity_delta=-item["quantity"],
                reference_code=reference_code,
                notes="Xuất kho cho đơn hàng online",
                created_at=now,
            )
        )
