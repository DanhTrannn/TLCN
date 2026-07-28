import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.errors import INTERNAL_ERROR, VALIDATION_ERROR, AppError

logger = logging.getLogger("ecommerce_api.error")


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "")


def _envelope(code: str, message: str, request_id: str, details: dict | None = None) -> dict:
    return {
        "error": {
            "code": code,
            "message": message,
            "request_id": request_id,
            "details": details or {},
        }
    }


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        request.state.error_code = exc.code
        return JSONResponse(
            status_code=exc.status_code,
            content=_envelope(exc.code, exc.message, _request_id(request), exc.details),
        )

    @app.exception_handler(RequestValidationError)
    async def _handle_validation(request: Request, exc: RequestValidationError) -> JSONResponse:
        request.state.error_code = VALIDATION_ERROR
        return JSONResponse(
            status_code=422,
            content=_envelope(
                VALIDATION_ERROR,
                "Dữ liệu không hợp lệ.",
                _request_id(request),
                {"errors": [{"loc": e.get("loc"), "msg": e.get("msg")} for e in exc.errors()]},
            ),
        )

    @app.exception_handler(Exception)
    async def _handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        request.state.error_code = INTERNAL_ERROR
        logger.exception(
            "unhandled_error",
            extra={"request_id": _request_id(request), "error_code": INTERNAL_ERROR},
        )
        return JSONResponse(
            status_code=500,
            content=_envelope(INTERNAL_ERROR, "Lỗi hệ thống.", _request_id(request)),
        )
