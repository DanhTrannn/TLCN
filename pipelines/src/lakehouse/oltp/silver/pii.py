from __future__ import annotations

from typing import Any
from pyspark.sql import DataFrame, functions as F
import os
import re

_PII_COLUMN_PATTERN = re.compile(
    r"(^|_)(email|phone|full_name|display_name|receiver_name|receiver_phone|address)(_|$)", re.IGNORECASE
)


def _get_salt() -> str:
    salt = os.environ.get("SILVER_PSEUDONYMIZE_SALT", "").strip()
    if not salt:
        raise ValueError(
            "SILVER_PSEUDONYMIZE_SALT is required and must not be empty. "
            "NĐ 13/2023/NĐ-CP on Personal Data Protection requires cryptographic salting "
            "to prevent dictionary and rainbow-table attacks on PII."
        )
    return salt


def _pseudonymized_column_name(column_name: str) -> str:
    """Return stable canonical names consumed by the Silver and Gold schemas."""
    if column_name == "email_normalized":
        return "email_pseudonymized"
    return f"{column_name}_pseudonymized"


def _pseudonymize(column: Any) -> Any:
    """Create a deterministic, normalized token without retaining the raw PII value."""
    normalized = F.lower(F.trim(column.cast("string")))
    return F.when(
        column.isNull(),
        F.lit(None).cast("string"),
    ).otherwise(
        F.sha2(
            F.concat(F.lit(_get_salt()), F.lit(":"), normalized),
            256,
        )
    )


def _redact_quarantine_pii(df: DataFrame) -> DataFrame:
    """Pseudonymize direct identifiers before serializing rejected rows."""
    redacted = df
    for column_name in df.columns:
        if _PII_COLUMN_PATTERN.search(column_name):
            redacted = redacted.withColumn(column_name, _pseudonymize(F.col(column_name)))
    return redacted
