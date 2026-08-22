from lakehouse.cursor import CursorState


def build_range_predicate(
    cursor_field: str,
    pk: str,
    committed: CursorState | None,
    high_watermark_at: str | None,
    high_watermark_pk: int | None,
) -> str:
    """Build the SQL WHERE clause delimiting the extraction window.

    The window is the half-open range (committed, high_watermark] expressed as
    a composite cursor pair ``(cursor_field, pk)``. Without a committed cursor
    (first run) only the upper bound is applied. Returns an empty string when
    no bound exists, otherwise a clause starting with `` WHERE ``.
    """
    clauses: list[str] = []
    if committed is not None:
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