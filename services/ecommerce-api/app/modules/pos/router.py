from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.deps import get_current_staff, get_db
from app.modules.pos.schemas import POSProductSearchResponse, POSTransactionRequest, POSTransactionResponse
from app.modules.pos.service import create_pos_transaction, search_products

router = APIRouter(prefix="/pos", tags=["pos"])


@router.get("/products", response_model=list[POSProductSearchResponse])
def list_products(
    store_id: int,
    search: str = "",
    db: Session = Depends(get_db),
    _staff=Depends(get_current_staff),
):
    return search_products(db, store_id=store_id, query=search)


@router.post("/transactions", response_model=POSTransactionResponse)
def create_transaction(
    request: POSTransactionRequest,
    staff=Depends(get_current_staff),
):
    result = create_pos_transaction(request, staff_id=staff.customer_id)
    return result
