"""Seed catalog: categories, products, variants and opening inventory.

Idempotent (skips when categories already exist) and deterministic (public_id
derived via uuid5) so seed/scenario/manifest stay reproducible. Seed only holds
manual catalog + opening balance; historical data is produced by the generator (see database/seeds/README.md).
"""

import uuid

from sqlalchemy import select

from app.core.config import get_settings
from app.core.ids import uuid7
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.catalog import Category, Product, ProductVariant
from app.models.inventory import Inventory
from app.models.customer import Customer, CustomerCredential

_NS = uuid.uuid5(uuid.NAMESPACE_URL, "tlcn:catalog")


def _pid(kind: str, key: str) -> uuid.UUID:
    return uuid.uuid5(_NS, f"{kind}:{key}")


CATEGORIES = [
    {"code": "ao", "name": "Áo"},
    {"code": "quan", "name": "Quần"},
    {"code": "phu-kien", "name": "Phụ kiện"},
]

# product -> (category_code, name, description, base_price, [(size, color)])
PRODUCTS = [
    ("ao-thun-basic", "ao", "Áo thun basic", "Áo thun cotton co giãn.", 149000,
     [("S", "black"), ("M", "black"), ("L", "white")]),
    ("ao-so-mi-linen", "ao", "Áo sơ mi linen", "Áo sơ mi vải linen thoáng mát.", 329000,
     [("M", "white"), ("L", "blue")]),
    ("ao-khoac-gio", "ao", "Áo khoác gió", "Áo khoác chống nước nhẹ.", 459000,
     [("M", "navy"), ("L", "navy"), ("XL", "black")]),
    ("quan-jean-slim", "quan", "Quần jean slim", "Quần jean ống côn.", 399000,
     [("29", "blue"), ("30", "blue"), ("31", "black")]),
    ("quan-kaki-chino", "quan", "Quần kaki chino", "Quần kaki dáng chino.", 349000,
     [("30", "beige"), ("32", "beige")]),
    ("quan-short-thun", "quan", "Quần short thun", "Quần short mặc nhà.", 159000,
     [("M", "gray"), ("L", "gray")]),
    ("non-luoi-trai", "phu-kien", "Nón lưỡi trai", "Nón thể thao điều chỉnh size.", 129000,
     [("F", "black"), ("F", "white")]),
    ("that-lung-da", "phu-kien", "Thắt lưng da", "Thắt lưng da tổng hợp.", 219000,
     [("F", "brown"), ("F", "black")]),
]

_OPENING_BY_INDEX = [50, 40, 35, 30, 25, 20, 15, 10]


def _seed_admin(session) -> None:
    settings = get_settings()
    email = settings.bootstrap_admin_email.strip().lower()
    existing = session.execute(
        select(CustomerCredential).where(CustomerCredential.email_normalized == email)
    ).scalar_one_or_none()
    if existing is not None:
        customer = session.get(Customer, existing.customer_id)
        if customer is None or customer.role != "admin":
            raise RuntimeError(f"Bootstrap admin email {email} is already used by a non-admin account.")
        return

    customer = Customer(
        public_id=uuid7(),
        display_name=settings.bootstrap_admin_display_name.strip(),
        role="admin",
        status="active",
        data_origin="manual",
    )
    session.add(customer)
    session.flush()
    session.add(
        CustomerCredential(
            customer_id=customer.customer_id,
            email_normalized=email,
            password_hash=hash_password(settings.bootstrap_admin_password),
            is_enabled=True,
        )
    )
    print(f"[seed_catalog] bootstrap admin ready: {email}")


def seed() -> None:
    session = SessionLocal()
    try:
        _seed_admin(session)

        exists = session.execute(select(Category.category_id).limit(1)).first()
        if exists is not None:
            session.commit()
            print("[seed_catalog] categories already present; skipping.")
            return

        cat_by_code: dict[str, Category] = {}
        for c in CATEGORIES:
            category = Category(
                public_id=_pid("category", c["code"]),
                code=c["code"],
                name=c["name"],
                is_active=True,
            )
            session.add(category)
            cat_by_code[c["code"]] = category
        session.flush()

        for slug, cat_code, name, description, base_price, combos in PRODUCTS:
            product = Product(
                public_id=_pid("product", slug),
                category_id=cat_by_code[cat_code].category_id,
                slug=slug,
                name=name,
                description=description,
                image_url=f"https://picsum.photos/seed/{slug}/600/600",
                is_active=True,
            )
            session.add(product)
            session.flush()

            for idx, (size, color) in enumerate(combos):
                sku = f"{slug}-{size}-{color}".upper()
                variant = ProductVariant(
                    public_id=_pid("variant", sku),
                    product_id=product.product_id,
                    sku=sku,
                    size_code=size,
                    color_code=color,
                    price_vnd=base_price + idx * 10000,
                    is_active=True,
                )
                session.add(variant)
                session.flush()

                opening = _OPENING_BY_INDEX[idx % len(_OPENING_BY_INDEX)]
                session.add(
                    Inventory(
                        variant_id=variant.variant_id,
                        opening_on_hand=opening,
                        on_hand=opening,
                        version=0,
                    )
                )

        session.commit()
        print("[seed_catalog] seeded categories, products, variants and inventory.")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed()
