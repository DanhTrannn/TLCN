import base64
import json
from datetime import datetime
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import VALIDATION_ERROR, AppError, not_found
from app.models.catalog import Category, Product, ProductVariant
from app.models.inventory import Inventory
from app.modules.catalog.schemas import (
    CatalogFacetsResponse,
    CategoryResponse,
    ProductDetailResponse,
    ProductListItem,
    ProductListResponse,
    ProductSort,
    VariantResponse,
)

_MAX_FACET_VALUES = 10


def list_categories(db: Session) -> list[CategoryResponse]:
    parent = Category.__table__.alias("parent")
    rows = db.execute(
        select(
            Category.public_id,
            Category.code,
            Category.name,
            parent.c.code.label("parent_code"),
        )
        .outerjoin(parent, parent.c.category_id == Category.parent_category_id)
        .where(Category.is_active.is_(True))
        .order_by(Category.category_id)
    ).all()
    return [
        CategoryResponse(
            public_id=str(row.public_id),
            code=row.code,
            name=row.name,
            parent_code=row.parent_code,
        )
        for row in rows
    ]


def get_catalog_facets(db: Session) -> CatalogFacetsResponse:
    base_conditions = (
        ProductVariant.is_active.is_(True),
        Product.is_active.is_(True),
        Category.is_active.is_(True),
    )
    base_join = (
        select(ProductVariant.variant_id)
        .join(Product, Product.product_id == ProductVariant.product_id)
        .join(Category, Category.category_id == Product.category_id)
    )
    sizes = db.execute(
        base_join.with_only_columns(ProductVariant.size_code)
        .where(*base_conditions)
        .distinct()
        .order_by(ProductVariant.size_code)
    ).scalars().all()
    colors = db.execute(
        base_join.with_only_columns(ProductVariant.color_code)
        .where(*base_conditions)
        .distinct()
        .order_by(ProductVariant.color_code)
    ).scalars().all()
    price_range = db.execute(
        base_join.with_only_columns(
            func.min(ProductVariant.price_vnd),
            func.max(ProductVariant.price_vnd),
        ).where(*base_conditions)
    ).one()
    return CatalogFacetsResponse(
        sizes=list(sizes),
        colors=list(colors),
        min_price_vnd=(int(price_range[0]) if price_range[0] is not None else None),
        max_price_vnd=(int(price_range[1]) if price_range[1] is not None else None),
    )


def _normalize_values(values: list[str] | None, field_name: str) -> list[str]:
    normalized = list(dict.fromkeys(value.strip() for value in values or [] if value.strip()))
    if len(normalized) > _MAX_FACET_VALUES:
        raise AppError(
            VALIDATION_ERROR,
            f"Chỉ được chọn tối đa {_MAX_FACET_VALUES} giá trị {field_name}.",
            status_code=400,
        )
    return normalized


def _search_pattern(query: str) -> str:
    escaped = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def _encode_product_cursor(sort: ProductSort, value: datetime | int, product_id: int) -> str:
    serialized_value = value.isoformat() if isinstance(value, datetime) else value
    raw = json.dumps(
        {"s": sort, "v": serialized_value, "i": product_id},
        separators=(",", ":"),
    ).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii")


def _decode_product_cursor(cursor: str, sort: ProductSort) -> tuple[datetime | int, int]:
    try:
        data: dict[str, Any] = json.loads(base64.urlsafe_b64decode(cursor.encode("ascii")))
        if data["s"] != sort:
            raise ValueError("cursor sort mismatch")
        value: datetime | int
        if sort == "newest":
            value = datetime.fromisoformat(str(data["v"]))
        else:
            value = int(data["v"])
        return value, int(data["i"])
    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        raise AppError(VALIDATION_ERROR, "Cursor không hợp lệ.", status_code=400) from error


def list_products(
    db: Session,
    category_code: str | None,
    query: str | None,
    sizes: list[str] | None,
    colors: list[str] | None,
    min_price_vnd: int | None,
    max_price_vnd: int | None,
    in_stock_only: bool,
    sort: ProductSort,
    cursor: str | None,
) -> ProductListResponse:
    settings = get_settings()
    page_size = settings.catalog_page_size
    normalized_query = query.strip() if query else None
    normalized_sizes = _normalize_values(sizes, "size")
    normalized_colors = _normalize_values(colors, "màu")
    if min_price_vnd is not None and max_price_vnd is not None and min_price_vnd > max_price_vnd:
        raise AppError(
            VALIDATION_ERROR,
            "Giá tối thiểu không được lớn hơn giá tối đa.",
            status_code=400,
        )

    variant_stats_stmt = (
        select(
            ProductVariant.product_id.label("product_id"),
            func.min(ProductVariant.price_vnd).label("min_price_vnd"),
            func.max(func.coalesce(Inventory.on_hand, 0)).label("max_on_hand"),
        )
        .outerjoin(Inventory, Inventory.variant_id == ProductVariant.variant_id)
        .where(ProductVariant.is_active.is_(True))
    )
    if normalized_sizes:
        variant_stats_stmt = variant_stats_stmt.where(ProductVariant.size_code.in_(normalized_sizes))
    if normalized_colors:
        variant_stats_stmt = variant_stats_stmt.where(ProductVariant.color_code.in_(normalized_colors))
    if min_price_vnd is not None:
        variant_stats_stmt = variant_stats_stmt.where(ProductVariant.price_vnd >= min_price_vnd)
    if max_price_vnd is not None:
        variant_stats_stmt = variant_stats_stmt.where(ProductVariant.price_vnd <= max_price_vnd)
    if in_stock_only:
        variant_stats_stmt = variant_stats_stmt.where(Inventory.on_hand > 0)
    variant_stats = variant_stats_stmt.group_by(ProductVariant.product_id).subquery()

    stmt = (
        select(
            Product,
            Category.code.label("category_code"),
            variant_stats.c.min_price_vnd,
            variant_stats.c.max_on_hand,
        )
        .join(Category, Category.category_id == Product.category_id)
        .join(variant_stats, variant_stats.c.product_id == Product.product_id)
        .where(Product.is_active.is_(True), Category.is_active.is_(True))
    )
    if category_code:
        stmt = stmt.where(Category.code == category_code)
    if normalized_query:
        pattern = _search_pattern(normalized_query)
        stmt = stmt.where(
            or_(
                Product.name.like(pattern, escape="\\"),
                Product.description.like(pattern, escape="\\"),
            )
        )

    cursor_value: datetime | int | None = None
    cursor_id: int | None = None
    if cursor:
        cursor_value, cursor_id = _decode_product_cursor(cursor, sort)

    if sort == "newest":
        if cursor_value is not None and cursor_id is not None:
            if not isinstance(cursor_value, datetime):
                raise AppError(VALIDATION_ERROR, "Cursor không hợp lệ.", status_code=400)
            stmt = stmt.where(
                (Product.created_at < cursor_value)
                | ((Product.created_at == cursor_value) & (Product.product_id < cursor_id))
            )
        stmt = stmt.order_by(Product.created_at.desc(), Product.product_id.desc())
    elif sort == "price_asc":
        if cursor_value is not None and cursor_id is not None:
            stmt = stmt.where(
                (variant_stats.c.min_price_vnd > cursor_value)
                | (
                    (variant_stats.c.min_price_vnd == cursor_value)
                    & (Product.product_id > cursor_id)
                )
            )
        stmt = stmt.order_by(variant_stats.c.min_price_vnd.asc(), Product.product_id.asc())
    else:
        if cursor_value is not None and cursor_id is not None:
            stmt = stmt.where(
                (variant_stats.c.min_price_vnd < cursor_value)
                | (
                    (variant_stats.c.min_price_vnd == cursor_value)
                    & (Product.product_id < cursor_id)
                )
            )
        stmt = stmt.order_by(variant_stats.c.min_price_vnd.desc(), Product.product_id.desc())

    rows = db.execute(stmt.limit(page_size + 1)).all()
    has_more = len(rows) > page_size
    rows = rows[:page_size]
    items = [
        ProductListItem(
            public_id=str(row.Product.public_id),
            slug=row.Product.slug,
            name=row.Product.name,
            image_url=row.Product.image_url,
            category_code=row.category_code,
            min_price_vnd=int(row.min_price_vnd),
            in_stock=int(row.max_on_hand or 0) > 0,
        )
        for row in rows
    ]

    next_cursor = None
    if has_more and rows:
        last = rows[-1]
        cursor_sort_value: datetime | int = (
            last.Product.created_at if sort == "newest" else int(last.min_price_vnd)
        )
        next_cursor = _encode_product_cursor(sort, cursor_sort_value, last.Product.product_id)

    return ProductListResponse(items=items, next_cursor=next_cursor)


def get_product_detail(db: Session, slug: str) -> ProductDetailResponse:
    row = db.execute(
        select(Product, Category.code, Category.name)
        .join(Category, Category.category_id == Product.category_id)
        .where(Product.slug == slug, Product.is_active.is_(True))
    ).first()
    if row is None:
        raise not_found("Không tìm thấy sản phẩm.")
    product, category_code, category_name = row

    variant_rows = db.execute(
        select(ProductVariant, func.coalesce(Inventory.on_hand, 0).label("on_hand"))
        .outerjoin(Inventory, Inventory.variant_id == ProductVariant.variant_id)
        .where(ProductVariant.product_id == product.product_id, ProductVariant.is_active.is_(True))
        .order_by(ProductVariant.variant_id)
    ).all()

    variants = [
        VariantResponse(
            public_id=str(variant.public_id),
            sku=variant.sku,
            size_code=variant.size_code,
            color_code=variant.color_code,
            price_vnd=variant.price_vnd,
            in_stock=int(on_hand or 0) > 0,
        )
        for variant, on_hand in variant_rows
    ]

    return ProductDetailResponse(
        public_id=str(product.public_id),
        slug=product.slug,
        name=product.name,
        description=product.description,
        image_url=product.image_url,
        category_code=category_code,
        category_name=category_name,
        variants=variants,
    )
