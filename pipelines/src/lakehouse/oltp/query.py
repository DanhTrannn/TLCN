"""Compose cursor bounds from external MySQL SQL fragments."""

from datetime import datetime, timedelta, timezone

from lakehouse.oltp.cursor import CursorState
from lakehouse.sql import identifier, literal, render_sql


def parse_cursor_timestamp(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return dt.astimezone(timezone.utc).replace(tzinfo=None) if dt.tzinfo else dt


def _subtract_lookback(cursor_at: str, minutes: int) -> str:
    dt = parse_cursor_timestamp(cursor_at) - timedelta(minutes=minutes)
    return dt.isoformat(sep=" ", timespec="microseconds")


def build_range_predicate(
    cursor_field: str,
    pk: str,
    committed: CursorState | None,
    high_watermark_at: str | None,
    high_watermark_pk: int | None,
    lookback_minutes: int = 0,
) -> str:
    if lookback_minutes < 0:
        raise ValueError("lookback_minutes must not be negative")
    clauses = []
    column, key = identifier(cursor_field), identifier(pk)
    if committed is not None:
        lower = parse_cursor_timestamp(committed.cursor_at)
        if lookback_minutes:
            clauses.append(
                render_sql(
                    "mysql/cursor_lookback.sql",
                    column=column,
                    lower=literal(_subtract_lookback(committed.cursor_at, lookback_minutes)),
                ).strip()
            )
        else:
            clauses.append(
                render_sql(
                    "mysql/cursor_lower.sql",
                    column=column,
                    pk=key,
                    lower=literal(lower.isoformat(sep=" ", timespec="microseconds")),
                    lower_pk=literal(committed.cursor_pk or 0),
                ).strip()
            )
    if high_watermark_at is not None:
        upper = parse_cursor_timestamp(high_watermark_at)
        clauses.append(
            render_sql(
                "mysql/cursor_upper.sql",
                column=column,
                pk=key,
                upper=literal(upper.isoformat(sep=" ", timespec="microseconds")),
                upper_pk=literal(high_watermark_pk or 0),
            ).strip()
        )
    return render_sql("mysql/cursor_where.sql", predicate=" AND ".join(clauses)).rstrip() if clauses else ""
