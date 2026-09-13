"""Seed multi-city and store data.

Idempotent: skips when cities already exist.
"""

from sqlalchemy import insert, select

from app.db.session import SessionLocal
from app.models.multicity import City, Store

CITIES = [
    {"code": "HCM", "name": "Hồ Chí Minh"},
    {"code": "HN", "name": "Hà Nội"},
    {"code": "DN", "name": "Đà Nẵng"},
    {"code": "CT", "name": "Cần Thơ"},
    {"code": "HP", "name": "Hải Phòng"},
]

STORES = [
    {"city_code": "HCM", "code": "HCM-CENTRE", "name": "Trung tâm Sài Gòn", "address": "123 Nguyễn Huệ, Quận 1", "phone": "028-1234-5678"},
    {"city_code": "HCM", "code": "HCM-NORTHEAST", "name": "Cửa hàng Thủ Đức", "address": "456 Lê Văn Việt, Thủ Đức", "phone": "028-8765-4321"},
    {"city_code": "HN", "code": "HN-CENTRE", "name": "Cửa hàng Hoàn Kiếm", "address": "789 Hàng Bài, Hoàn Kiếm", "phone": "024-1111-2222"},
    {"city_code": "DN", "code": "DN-CENTRE", "name": "Cửa hàng Sơn Trà", "address": "321 Bạch Đằng, Sơn Trà", "phone": "023-3333-4444"},
    {"city_code": "CT", "code": "CT-CENTRE", "name": "Cửa hàng Ninh Kiều", "address": "654 Nguyễn Trãi, Ninh Kiều", "phone": "029-5555-6666"},
    {"city_code": "HP", "code": "HP-CENTRE", "name": "Cửa hàng Hồng Bàng", "address": "987 Tô Hiệu, Hồng Bàng", "phone": "022-7777-8888"},
]


def _seed_cities(session) -> dict[str, int]:
    """Insert cities and return mapping of code -> city_id."""
    existing = session.execute(select(City.code, City.city_id)).fetchall()
    city_map = {code: cid for code, cid in existing}

    new_cities = [c for c in CITIES if c["code"] not in city_map]
    if new_cities:
        result = session.execute(
            insert(City).prefix_with("IGNORE"),
            [{"code": c["code"], "name": c["name"], "is_active": True} for c in new_cities],
        )
        if result.rowcount:
            print(f"[seed] inserted {result.rowcount} cities")

    for c in CITIES:
        if c["code"] not in city_map:
            row = session.execute(
                select(City.city_id).where(City.code == c["code"])
            ).scalar_one()
            city_map[c["code"]] = row

    return city_map


def _seed_stores(session, city_map: dict[str, int]) -> None:
    """Insert stores linked to cities."""
    existing_codes = {
        row[0] for row in session.execute(select(Store.code)).fetchall()
    }

    new_stores = [s for s in STORES if s["code"] not in existing_codes]
    if not new_stores:
        return

    rows = []
    for s in new_stores:
        city_id = city_map.get(s["city_code"])
        if city_id is None:
            print(f"[seed] WARNING: city {s['city_code']} not found, skipping store {s['code']}")
            continue
        rows.append({
            "city_id": city_id,
            "code": s["code"],
            "name": s["name"],
            "address": s["address"],
            "phone": s["phone"],
            "is_active": True,
        })

    if rows:
        result = session.execute(insert(Store).prefix_with("IGNORE"), rows)
        print(f"[seed] inserted {result.rowcount} stores")


def seed() -> None:
    session = SessionLocal()
    try:
        exists = session.execute(select(City.city_id).limit(1)).first()
        if exists is not None:
            print("[seed] cities already present; skipping.")
            return

        city_map = _seed_cities(session)
        _seed_stores(session, city_map)
        session.commit()
        print("[seed] multi-city and stores seeded.")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed()
