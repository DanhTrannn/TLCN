import random
import time
from collections.abc import Callable
from typing import TypeVar

from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import CONCURRENCY_RETRY_EXHAUSTED, AppError
from app.db.session import SessionLocal

T = TypeVar("T")

# MySQL transient error codes: deadlock, lock wait timeout.
_TRANSIENT_MYSQL_CODES = {1213, 1205}


def _is_transient(error: OperationalError) -> bool:
    args = getattr(error.orig, "args", None)
    if args and isinstance(args[0], int):
        return args[0] in _TRANSIENT_MYSQL_CODES
    return False


def run_in_transaction(work: Callable[[Session], T]) -> T:
    """Run ``work`` in a READ COMMITTED transaction with bounded retry on
    deadlock / lock-wait-timeout. ``work`` must be side-effect-free outside the
    session so it can be retried safely."""
    settings = get_settings()
    attempts = settings.checkout_max_retries
    last_error: OperationalError | None = None

    for attempt in range(attempts):
        session = SessionLocal()
        try:
            result = work(session)
            session.commit()
            return result
        except OperationalError as error:
            session.rollback()
            if not _is_transient(error):
                raise
            last_error = error
            sleep_s = (2**attempt) * 0.05 + random.uniform(0, 0.05)
            time.sleep(sleep_s)
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    raise AppError(
        CONCURRENCY_RETRY_EXHAUSTED,
        "Hệ thống đang bận, vui lòng thử lại.",
        status_code=409,
    ) from last_error
