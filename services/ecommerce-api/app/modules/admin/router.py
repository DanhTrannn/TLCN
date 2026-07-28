from fastapi import APIRouter, Depends, Header, Query, Response
from sqlalchemy.orm import Session

from app.db.deps import get_current_admin, get_db, verify_csrf
from app.models.customer import Customer
from app.modules.admin.schemas import (
    AdminCustomerResponse,
    AdminOrderResponse,
    AdminOverviewResponse,
    AdminProductResponse,
    CreateProductRequest,
    UpdateCustomerRequest,
    UpdateProductRequest,
    UpdateVariantRequest,
)
from app.modules.admin.service import (
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
from app.modules.orders.schemas import OrderDetailResponse
from app.modules.orders.service import complete_order

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/overview", response_model=AdminOverviewResponse)
def overview(
    _: Customer = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> AdminOverviewResponse:
    return get_overview(db)


@router.get("/products", response_model=list[AdminProductResponse])
def products(
    _: Customer = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> list[AdminProductResponse]:
    return list_products(db)


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
    status: str | None = Query(default=None, pattern=r"^(paid|payment_failed|completed)$"),
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


@router.post("/orders/{order_number}/complete")
def mark_order_complete(
    order_number: str,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    _: Customer = Depends(get_current_admin),
    __: None = Depends(verify_csrf),
) -> dict:
    return complete_order(order_number, idempotency_key, transition_source="admin")


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
