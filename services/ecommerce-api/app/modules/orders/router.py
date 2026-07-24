from fastapi import APIRouter

router = APIRouter(prefix="/orders", tags=["orders"])
internal_router = APIRouter(prefix="/orders", tags=["internal-orders"])

