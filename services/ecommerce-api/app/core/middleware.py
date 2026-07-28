import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.ids import new_request_id

logger = logging.getLogger("ecommerce_api.access")

_REQUEST_ID_HEADER = "X-Request-ID"
_MAX_CLIENT_ID_LEN = 128


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        client_id = request.headers.get(_REQUEST_ID_HEADER, "")
        request_id = client_id if 0 < len(client_id) <= _MAX_CLIENT_ID_LEN else new_request_id()
        request.state.request_id = request_id

        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            latency_ms = (time.perf_counter() - start) * 1000
            logger.exception(
                "request_failed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "route": request.url.path,
                    "latency_ms": round(latency_ms, 2),
                    "error_code": getattr(request.state, "error_code", "INTERNAL_ERROR"),
                },
            )
            raise

        latency_ms = (time.perf_counter() - start) * 1000
        response.headers[_REQUEST_ID_HEADER] = request_id
        logger.info(
            "request",
            extra={
                "request_id": request_id,
                "method": request.method,
                "route": request.url.path,
                "status": response.status_code,
                "latency_ms": round(latency_ms, 2),
                "error_code": getattr(request.state, "error_code", None),
            },
        )
        return response
