from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.deps import get_db, get_current_staff
from app.modules.pos.schemas import POSTransactionRequest, POSTransactionResponse, POSProductSearchResponse
from app.modules.pos.service import search_products, create_pos_transaction

router = APIRouter(prefix="/api/v1/pos", tags=["pos"])


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
    db: Session = Depends(get_db),
    staff=Depends(get_current_staff),
):
    result = create_pos_transaction(db, request, staff_id=staff.customer_id)
    return result
