from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.errors import forbidden
from app.db.deps import get_current_staff, get_db, verify_csrf
from app.models.customer import Customer
from app.modules.pos.schemas import POSProductSearchResponse, POSTransactionRequest, POSTransactionResponse
from app.modules.pos.service import create_pos_transaction, search_products

router = APIRouter(prefix="/pos", tags=["pos"])


def _ensure_store_access(staff: Customer, store_id: int) -> None:
    if staff.role in {"admin", "system_admin"}:
        return
    if staff.store_id is None or staff.store_id != store_id:
        raise forbidden("Nhân viên chỉ được thao tác POS tại cửa hàng được phân công.")


@router.get("/products", response_model=list[POSProductSearchResponse])
def list_products(
    store_id: int,
    search: str = "",
    db: Session = Depends(get_db),
    staff: Customer = Depends(get_current_staff),
):
    _ensure_store_access(staff, store_id)
    return search_products(db, store_id=store_id, query=search)


@router.post("/transactions", response_model=POSTransactionResponse)
def create_transaction(
    request: POSTransactionRequest,
    staff: Customer = Depends(get_current_staff),
    _: None = Depends(verify_csrf),
):
    _ensure_store_access(staff, request.store_id)
    result = create_pos_transaction(request, staff_id=staff.customer_id)
    return result
