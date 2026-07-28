from fastapi import APIRouter

from app.api.health import router as health_router
from app.modules.admin.router import router as admin_router
from app.modules.auth.router import router as auth_router
from app.modules.cart.router import router as cart_router
from app.modules.catalog.router import router as catalog_router
from app.modules.checkout.router import router as checkout_router
from app.modules.orders.router import internal_router as internal_orders_router
from app.modules.orders.router import router as orders_router
from app.modules.wishlist.router import router as wishlist_router

api_router = APIRouter()
api_router.include_router(health_router)

v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(auth_router)
v1_router.include_router(admin_router)
v1_router.include_router(catalog_router)
v1_router.include_router(cart_router)
v1_router.include_router(checkout_router)
v1_router.include_router(orders_router)
v1_router.include_router(wishlist_router)
api_router.include_router(v1_router)

internal_router = APIRouter(prefix="/internal/v1")
internal_router.include_router(internal_orders_router)

