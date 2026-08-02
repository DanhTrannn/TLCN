from typing import Any


class AppError(Exception):
    """Domain/application error mapped to a stable error code and HTTP status."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


VALIDATION_ERROR = "VALIDATION_ERROR"
AUTH_REQUIRED = "AUTH_REQUIRED"
INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
ACCOUNT_LOCKED = "ACCOUNT_LOCKED"
EMAIL_ALREADY_EXISTS = "EMAIL_ALREADY_EXISTS"
FORBIDDEN = "FORBIDDEN"
RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
CART_NOT_ACTIVE = "CART_NOT_ACTIVE"
EMPTY_CART = "EMPTY_CART"
VARIANT_NOT_SELLABLE = "VARIANT_NOT_SELLABLE"
OUT_OF_STOCK = "OUT_OF_STOCK"
COUPON_INVALID = "COUPON_INVALID"
COUPON_USAGE_LIMIT = "COUPON_USAGE_LIMIT"
REVIEW_NOT_ALLOWED = "REVIEW_NOT_ALLOWED"
REVIEW_ALREADY_EXISTS = "REVIEW_ALREADY_EXISTS"
IDEMPOTENCY_CONFLICT = "IDEMPOTENCY_CONFLICT"
INVALID_STATE_TRANSITION = "INVALID_STATE_TRANSITION"
CONCURRENCY_RETRY_EXHAUSTED = "CONCURRENCY_RETRY_EXHAUSTED"
INTERNAL_ERROR = "INTERNAL_ERROR"


def auth_required() -> AppError:
    return AppError(AUTH_REQUIRED, "Yêu cầu đăng nhập.", status_code=401)


def forbidden(message: str = "Không có quyền truy cập.") -> AppError:
    return AppError(FORBIDDEN, message, status_code=403)


def not_found(message: str = "Không tìm thấy tài nguyên.") -> AppError:
    return AppError(RESOURCE_NOT_FOUND, message, status_code=404)
