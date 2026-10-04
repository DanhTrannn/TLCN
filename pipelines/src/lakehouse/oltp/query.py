from __future__ import annotations

from datetime import datetime, timedelta

from lakehouse.oltp.cursor import CursorState


def _subtract_lookback(cursor_at: str, minutes: int) -> str:
    """Subtract lookback minutes from cursor timestamp string safely."""
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(cursor_at, fmt)
            shifted = dt - timedelta(minutes=minutes)
            return shifted.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
    try:
        dt = datetime.fromisoformat(cursor_at)
        shifted = dt - timedelta(minutes=minutes)
        return shifted.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return cursor_at


def build_range_predicate(
    cursor_field: str,
    pk: str,
    committed: CursorState | None,
    high_watermark_at: str | None,
    high_watermark_pk: int | None,
    lookback_minutes: int = 0,
) -> str:
    """Build the SQL WHERE clause delimiting the extraction window.

    The window is delimited by (committed - lookback, high_watermark].
    If lookback_minutes > 0, an overlapping window is extracted to capture late-arriving
    transactions committed out of order. Silver layer MERGE handles idempotency.
    Without a committed cursor (first run) only the upper bound is applied.
    Returns an empty string when no bound exists, otherwise a clause starting with `` WHERE ``.
    """
    clauses: list[str] = []
    if committed is not None:
        if lookback_minutes > 0:
            lookback_at = _subtract_lookback(committed.cursor_at, lookback_minutes)
            clauses.append(f"(`{cursor_field}` >= '{lookback_at}')")
        else:
            clauses.append(
                f"(`{cursor_field}` > '{committed.cursor_at}' OR "
                f"(`{cursor_field}` = '{committed.cursor_at}' AND "
                f"`{pk}` > {committed.cursor_pk or 0}))"
            )
    if high_watermark_at is not None:
        clauses.append(
            f"(`{cursor_field}` < '{high_watermark_at}' OR "
            f"(`{cursor_field}` = '{high_watermark_at}' AND "
            f"`{pk}` <= {high_watermark_pk or 0}))"
        )
    if not clauses:
        return ""
    return " WHERE " + " AND ".join(clauses)
