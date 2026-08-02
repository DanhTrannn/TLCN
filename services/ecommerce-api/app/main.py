from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router, internal_router
from app.core.config import get_settings
from app.core.handlers import register_exception_handlers
from app.core.logging_config import configure_logging
from app.core.middleware import RequestContextMiddleware

settings = get_settings()
configure_logging(settings.service_name, settings.service_version)

app = FastAPI(
    title="D&K Ecommerce API",
    version=settings.service_version,
    docs_url="/docs" if settings.enable_docs else None,
    redoc_url=None,
)
app.add_middleware(RequestContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "X-CSRF-Token", "Idempotency-Key", "X-Request-ID"],
)
register_exception_handlers(app)
app.include_router(api_router)
app.include_router(internal_router)
