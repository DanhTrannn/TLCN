from fastapi import APIRouter

from app.api.health import router as health_router
from app.modules.admin.router import router as admin_router
from app.modules.auth.router import router as auth_router
from app.modules.cart.router import router as cart_router
from app.modules.catalog.router import router as catalog_router
from app.modules.location.router import router as location_router
from app.modules.logistics.router import admin_logistics_router
from app.modules.checkout.router import router as checkout_router
from app.modules.coupons.router import admin_router as admin_coupons_router
from app.modules.coupons.router import router as coupons_router
from app.modules.orders.router import internal_router as internal_orders_router
from app.modules.orders.router import router as orders_router
from app.modules.reviews.router import admin_router as admin_reviews_router
from app.modules.reviews.router import router as reviews_router
from app.modules.returns.router import admin_router as admin_returns_router
from app.modules.returns.router import router as returns_router
from app.modules.pos.router import router as pos_router
from app.modules.store.router import admin_store_router
from app.modules.wishlist.router import router as wishlist_router

api_router = APIRouter()
api_router.include_router(health_router)

v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(auth_router)
v1_router.include_router(admin_router)
v1_router.include_router(admin_store_router)
v1_router.include_router(admin_coupons_router)
v1_router.include_router(admin_reviews_router)
v1_router.include_router(admin_logistics_router)
v1_router.include_router(coupons_router)
v1_router.include_router(catalog_router)
v1_router.include_router(cart_router)
v1_router.include_router(location_router)
v1_router.include_router(checkout_router)
v1_router.include_router(orders_router)
v1_router.include_router(reviews_router)
v1_router.include_router(pos_router)
v1_router.include_router(wishlist_router)
v1_router.include_router(returns_router)
v1_router.include_router(admin_returns_router)
api_router.include_router(v1_router)

internal_router = APIRouter(prefix="/internal/v1")
internal_router.include_router(internal_orders_router)
