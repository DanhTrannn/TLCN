from fastapi import APIRouter, Depends, Header, Query, Response
from sqlalchemy.orm import Session

from app.core.errors import VALIDATION_ERROR, AppError, not_found
from app.db.deps import get_current_admin, get_current_staff, get_db, verify_csrf
from app.models.customer import Customer
from app.models.multicity import Store, StoreInventory
from app.models.catalog import ProductVariant
from app.modules.admin.branch_inventory_schemas import BranchInventoryItem, UpdateStockRequest
from app.modules.admin.branch_inventory_service import check_store_inventory_permission
from app.modules.admin.schemas import (
    AdminCustomerResponse,
    AdminOrderResponse,
    AdminOverviewResponse,
    AdminProductResponse,
    ArchiveRequest,
    CreateProductRequest,
    UpdateCustomerRequest,
    UpdateProductRequest,
    UpdateVariantRequest,
)
from app.modules.admin.service import (
    archive_product,
    create_product,
    get_admin_order_detail,
    get_overview,
    list_customers,
    list_orders,
    list_products,
    update_customer_status,
    update_product,
    update_variant,
)
from app.modules.orders.schemas import (
    CancelOrderRequest,
    OrderDetailResponse,
    OrderTransitionResponse,
)
from app.modules.orders.service import cancel_order, confirm_order

router = APIRouter(prefix="/admin", tags=["admin"])


def _require_idempotency_key(value: str | None) -> str:
    key = value.strip() if value else ""
    if not key or len(key) > 64:
        raise AppError(
            VALIDATION_ERROR,
            "Idempotency-Key phải có từ 1 đến 64 ký tự.",
            status_code=400,
        )
    return key


@router.get("/overview", response_model=AdminOverviewResponse)
def overview(
    _: Customer = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> AdminOverviewResponse:
    return get_overview(db)


@router.get("/products", response_model=list[AdminProductResponse])
def products(
    search: str | None = Query(default=None, max_length=200),
    _: Customer = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> list[AdminProductResponse]:
    return list_products(db, search)


@router.post("/products", response_model=AdminProductResponse, status_code=201)
def add_product(
    payload: CreateProductRequest,
    _: Customer = Depends(get_current_admin),
    __: None = Depends(verify_csrf),
) -> AdminProductResponse:
    return create_product(payload)


@router.patch("/products/{public_id}", status_code=204)
def patch_product(
    public_id: str,
    payload: UpdateProductRequest,
    _: Customer = Depends(get_current_admin),
    __: None = Depends(verify_csrf),
) -> Response:
    update_product(public_id, payload)
    return Response(status_code=204)


@router.delete("/products/{public_id}", status_code=204)
def delete_product(
    public_id: str,
    payload: ArchiveRequest,
    admin: Customer = Depends(get_current_admin),
    _: None = Depends(verify_csrf),
) -> Response:
    archive_product(admin.customer_id, public_id, payload.reason)
    return Response(status_code=204)


@router.patch("/variants/{public_id}", status_code=204)
def patch_variant(
    public_id: str,
    payload: UpdateVariantRequest,
    _: Customer = Depends(get_current_admin),
    __: None = Depends(verify_csrf),
) -> Response:
    update_variant(public_id, payload)
    return Response(status_code=204)


@router.get("/orders", response_model=list[AdminOrderResponse])
def orders(
    status: str | None = Query(
        default=None,
        pattern=r"^(paid|payment_failed|confirmed|completed|cancelled)$",
    ),
    _: Customer = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> list[AdminOrderResponse]:
    return list_orders(db, status)


@router.get("/orders/{order_number}", response_model=OrderDetailResponse)
def order_detail(
    order_number: str,
    _: Customer = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> OrderDetailResponse:
    return get_admin_order_detail(db, order_number)


@router.post("/orders/{order_number}/confirm", response_model=OrderTransitionResponse)
def confirm_admin_order(
    order_number: str,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    _: Customer = Depends(get_current_admin),
    __: None = Depends(verify_csrf),
) -> OrderTransitionResponse:
    return confirm_order(
        order_number,
        _require_idempotency_key(idempotency_key),
        transition_source="admin",
    )


@router.post("/orders/{order_number}/cancel", response_model=OrderTransitionResponse)
def cancel_admin_order(
    order_number: str,
    payload: CancelOrderRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    admin: Customer = Depends(get_current_admin),
    _: None = Depends(verify_csrf),
) -> OrderTransitionResponse:
    return cancel_order(
        order_number,
        actor_customer_id=admin.customer_id,
        owner_customer_id=None,
        reason=payload.reason,
        idempotency_key=_require_idempotency_key(idempotency_key),
        transition_source="admin",
    )


@router.get("/customers", response_model=list[AdminCustomerResponse])
def customers(
    _: Customer = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> list[AdminCustomerResponse]:
    return list_customers(db)


@router.patch("/customers/{public_id}", status_code=204)
def patch_customer(
    public_id: str,
    payload: UpdateCustomerRequest,
    admin: Customer = Depends(get_current_admin),
    _: None = Depends(verify_csrf),
) -> Response:
    update_customer_status(admin.customer_id, public_id, payload.status)
    return Response(status_code=204)


@router.get("/branch-inventory", response_model=list[BranchInventoryItem])
def list_branch_inventory(
    store_id: int | None = Query(default=None, gt=0),
    city_id: int | None = Query(default=None, gt=0),
    actor: Customer = Depends(get_current_staff),
    db: Session = Depends(get_db),
) -> list[BranchInventoryItem]:
    stmt = (
        select(
            StoreInventory,
            Store.name.label("store_name"),
            Store.city_id,
            Store.city_id.label("city_id_label"),
            ProductVariant.sku.label("variant_sku"),
            ProductVariant.size_code,
            ProductVariant.color_code,
            ProductVariant.price_vnd,
        )
        .join(Store, Store.store_id == StoreInventory.store_id)
        .join(ProductVariant, ProductVariant.variant_id == StoreInventory.variant_id)
    )

    if actor.role == "store_manager":
        stmt = stmt.where(Store.store_id == actor.store_id)
    elif actor.role == "city_planner":
        stmt = stmt.where(Store.city_id == actor.city_id)

    if store_id is not None:
        check_store_inventory_permission(actor, store_id, 0)
        stmt = stmt.where(Store.store_id == store_id)
    if city_id is not None:
        stmt = stmt.where(Store.city_id == city_id)

    rows = db.execute(stmt).all()
    return [
        BranchInventoryItem(
            store_id=row.StoreInventory.store_id,
            store_name=row.store_name,
            city_id=row.city_id,
            city_name="",
            variant_id=row.StoreInventory.variant_id,
            variant_sku=row.variant_sku,
            size_code=row.size_code,
            color_code=row.color_code,
            price_vnd=row.price_vnd,
            on_hand=row.StoreInventory.on_hand,
            opening_on_hand=row.StoreInventory.opening_on_hand,
        )
        for row in rows
    ]


@router.patch("/branch-inventory", status_code=204)
def update_branch_stock(
    payload: UpdateStockRequest,
    actor: Customer = Depends(get_current_staff),
    _: None = Depends(verify_csrf),
    db: Session = Depends(get_db),
) -> Response:
    inventory = db.execute(
        select(StoreInventory).where(
            StoreInventory.store_id == payload.store_id,
            StoreInventory.variant_id == payload.variant_id,
        )
    ).scalar_one_or_none()
    if inventory is None:
        raise not_found("Không tìm thấy tồn kho cho store và variant này.")

    store = db.execute(
        select(Store).where(Store.store_id == payload.store_id)
    ).scalar_one_or_none()
    if store is None:
        raise not_found("Không tìm thấy cửa hàng.")

    check_store_inventory_permission(actor, payload.store_id, store.city_id)

    inventory.on_hand = payload.on_hand
    inventory.version += 1
    db.flush()
    return Response(status_code=204)
