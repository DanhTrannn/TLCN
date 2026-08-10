import logging
import time
from datetime import UTC, datetime

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.access_logging import build_access_event
from app.core.ids import new_request_id

logger = logging.getLogger("ecommerce_api.access")

_REQUEST_ID_HEADER = "X-Request-ID"
class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        # Always mint the server request identity. Trusting a caller-supplied value
        # would allow collisions to erase distinct requests during Silver deduplication.
        request_id = new_request_id()
        request.state.request_id = request_id
        request.state.actor_type = "anonymous"
        request.state.actor_key = None

        start_ns = time.perf_counter_ns()
        try:
            response = await call_next(request)
        except Exception as error:
            completed_at = datetime.now(UTC)
            access_event = build_access_event(
                request,
                request_id=request_id,
                status_code=500,
                duration_ns=time.perf_counter_ns() - start_ns,
                completed_at=completed_at,
                exception_type=type(error).__name__,
            )
            logger.error(
                "http.server.request",
                extra={
                    "access_event": access_event,
                },
            )
            logger.exception(
                "request_failed",
                extra={
                    "request_id": request_id,
                    "error_code": getattr(
                        request.state,
                        "error_code",
                        "INTERNAL_ERROR",
                    ),
                },
            )
            raise

        completed_at = datetime.now(UTC)
        access_event = build_access_event(
            request,
            request_id=request_id,
            status_code=response.status_code,
            duration_ns=time.perf_counter_ns() - start_ns,
            completed_at=completed_at,
        )
        response.headers[_REQUEST_ID_HEADER] = request_id
        if response.status_code >= 500:
            level = logging.ERROR
        elif response.status_code >= 400:
            level = logging.WARNING
        else:
            level = logging.INFO
        logger.log(level, "http.server.request", extra={"access_event": access_event})
        return response
