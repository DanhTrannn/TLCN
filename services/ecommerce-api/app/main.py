from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router, internal_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title="TLCN Ecommerce API",
    version=settings.service_version,
    docs_url="/docs" if settings.enable_docs else None,
    redoc_url=None,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "X-CSRF-Token", "Idempotency-Key", "X-Request-ID"],
)
app.include_router(api_router)
app.include_router(internal_router)

