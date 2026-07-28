import secrets
from collections.abc import Generator

from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import FORBIDDEN, AppError, auth_required, forbidden
from app.core.security import decode_access_token
from app.db.session import SessionLocal
from app.models.customer import Customer


def get_db() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_current_customer(
    request: Request,
    db: Session = Depends(get_db),
) -> Customer:
    settings = get_settings()
    token = request.cookies.get(settings.auth_cookie_name)
    if not token:
        raise auth_required()
    claims = decode_access_token(token)
    if not claims or "sub" not in claims:
        raise auth_required()
    customer = db.execute(
        select(Customer).where(Customer.public_id == claims["sub"])
    ).scalar_one_or_none()
    if customer is None or customer.status != "active":
        raise auth_required()
    return customer


def get_current_admin(customer: Customer = Depends(get_current_customer)) -> Customer:
    if customer.role != "admin":
        raise forbidden("Chỉ quản trị viên mới có quyền truy cập.")
    return customer


def verify_csrf(request: Request) -> None:
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return
    settings = get_settings()
    cookie_token = request.cookies.get(settings.csrf_cookie_name)
    header_token = request.headers.get("X-CSRF-Token")
    if not cookie_token or not header_token or not secrets.compare_digest(cookie_token, header_token):
        raise AppError(FORBIDDEN, "CSRF token không hợp lệ.", status_code=403)


def require_internal_secret(request: Request) -> None:
    settings = get_settings()
    provided = request.headers.get("X-Internal-Secret")
    if not provided or not secrets.compare_digest(provided, settings.internal_secret):
        raise AppError(FORBIDDEN, "Yêu cầu nội bộ không hợp lệ.", status_code=403)
