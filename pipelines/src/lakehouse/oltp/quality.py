"""Persistent data-quality audit and post-Gold publication gates."""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Iterable

if TYPE_CHECKING:
    from pyspark.sql import DataFrame, SparkSession

try:
    from pyspark.sql import functions as F
except ImportError:  # pragma: no cover - unit tests without Spark
    F = None  # type: ignore


QUALITY_RESULTS_TABLE = "lakehouse.system.data_quality_results"

QUALITY_RESULTS_DDL = f"""
CREATE TABLE IF NOT EXISTS {QUALITY_RESULTS_TABLE} (
    check_id                       STRING,
    run_id                         STRING,
    batch_date                     DATE,
    phase                          STRING,
    check_name                     STRING,
    dataset                        STRING,
    severity                       STRING,
    observed_value                 STRING,
    expected_value                 STRING,
    variance_percent               DOUBLE,
    failed_rows                    BIGINT,
    status                         STRING,
    details                        STRING,
    checked_at                     TIMESTAMP
)
USING iceberg
PARTITIONED BY (days(checked_at))
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
"""


class GoldQualityGateError(RuntimeError):
    """Raised when a blocking post-publication Gold quality check fails."""


@dataclass(frozen=True)
class QualityCheckResult:
    check_name: str
    dataset: str
    observed_value: str
    expected_value: str
    passed: bool
    details: str
    severity: str = "ERROR"
    variance_percent: float = 0.0
    failed_rows: int = 0


def ensure_quality_results_table(spark: SparkSession) -> None:
    spark.sql("CREATE NAMESPACE IF NOT EXISTS lakehouse.system")
    spark.sql(QUALITY_RESULTS_DDL)


def _result_payload(result: Any) -> dict[str, Any]:
    if isinstance(result, QualityCheckResult):
        return asdict(result)
    return {
        "check_name": getattr(result, "metric_name", "unknown_check"),
        "dataset": getattr(result, "table_name", "unknown_dataset"),
        "observed_value": str(getattr(result, "silver_value", "")),
        "expected_value": str(getattr(result, "source_value", "")),
        "passed": bool(getattr(result, "passed", False)),
        "details": getattr(result, "details", ""),
        "severity": getattr(result, "severity", "ERROR"),
        "variance_percent": float(getattr(result, "variance_percent", 0.0)),
        "failed_rows": int(getattr(result, "failed_rows", 0)),
    }


def _sql_string(value: Any) -> str:
    """Quote a value as a Spark SQL string literal."""
    return "'" + str(value).replace("'", "''") + "'"


def persist_quality_results(
    spark: SparkSession,
    results: Iterable[Any],
    *,
    run_id: str,
    batch_date: str,
    phase: str,
) -> None:
    """Append quality evidence before the gate succeeds or raises."""
    checked_at = datetime.now(timezone.utc).replace(tzinfo=None)
    rows = []
    for result in results:
        payload = _result_payload(result)
        rows.append(
            "(" + ", ".join(
                (
                    _sql_string(uuid.uuid4().hex),
                    _sql_string(run_id),
                    f"DATE {_sql_string(batch_date)}",
                    _sql_string(phase),
                    _sql_string(payload["check_name"]),
                    _sql_string(payload["dataset"]),
                    _sql_string(payload["severity"]),
                    _sql_string(payload["observed_value"]),
                    _sql_string(payload["expected_value"]),
                    str(float(payload["variance_percent"])),
                    str(int(payload["failed_rows"])),
                    _sql_string("PASSED" if payload["passed"] else "FAILED"),
                    _sql_string(payload["details"]),
                    f"TIMESTAMP {_sql_string(checked_at.strftime('%Y-%m-%d %H:%M:%S.%f'))}",
                )
            ) + ")"
        )

    if not rows:
        return

    ensure_quality_results_table(spark)
    # SQL VALUES executes fully in the JVM. That avoids starting Python workers
    # merely to persist a few audit rows, and keeps the gate portable across a
    # Spark cluster whose worker image may use a different Python minor version.
    spark.sql(f"INSERT INTO {QUALITY_RESULTS_TABLE} VALUES " + ", ".join(rows))


def _exact_count_check(
    check_name: str,
    source_dataset: str,
    source_count: int,
    target_dataset: str,
    target_count: int,
) -> QualityCheckResult:
    passed = source_count == target_count
    return QualityCheckResult(
        check_name=check_name,
        dataset=target_dataset,
        observed_value=str(target_count),
        expected_value=str(source_count),
        passed=passed,
        variance_percent=(
            0.0
            if source_count == target_count
            else (100.0 if source_count == 0 else round(abs(source_count - target_count) / source_count * 100, 4))
        ),
        failed_rows=abs(source_count - target_count),
        details=(
            f"{source_dataset} and {target_dataset} counts match"
            if passed
            else f"count mismatch: {source_dataset}={source_count}, {target_dataset}={target_count}"
        ),
    )


def _sum_as_int(df: DataFrame, column_name: str) -> int:
    value = df.select(F.coalesce(F.sum(F.col(column_name)), F.lit(0)).alias("value")).first()["value"]
    return int(value or 0)


def run_gold_quality_gate(
    spark: SparkSession,
    *,
    run_id: str,
    batch_date: str,
    persist_results: bool = True,
) -> dict[str, Any]:
    """Validate Gold publication completeness, keys, references, PII, and run freshness."""
    silver_orders = spark.table("lakehouse.silver.silver_orders")
    silver_order_items = spark.table("lakehouse.silver.silver_order_items")
    fact_order = spark.table("lakehouse.gold.fact_order")
    fact_order_item = spark.table("lakehouse.gold.fact_order_item")

    results: list[QualityCheckResult] = [
        _exact_count_check(
            "silver_to_gold_row_count",
            "lakehouse.silver.silver_orders",
            silver_orders.count(),
            "lakehouse.gold.fact_order",
            fact_order.count(),
        ),
        _exact_count_check(
            "silver_to_gold_row_count",
            "lakehouse.silver.silver_order_items",
            silver_order_items.count(),
            "lakehouse.gold.fact_order_item",
            fact_order_item.count(),
        ),
    ]

    silver_revenue = _sum_as_int(silver_orders, "total_vnd")
    gold_revenue = _sum_as_int(fact_order, "gross_revenue_vnd")
    results.append(
        QualityCheckResult(
            check_name="silver_to_gold_gross_revenue_vnd",
            dataset="lakehouse.gold.fact_order",
            observed_value=str(gold_revenue),
            expected_value=str(silver_revenue),
            passed=gold_revenue == silver_revenue,
            failed_rows=0 if gold_revenue == silver_revenue else 1,
            details=f"silver={silver_revenue} VND, gold={gold_revenue} VND",
        )
    )

    for table_name, primary_key in (
        ("lakehouse.gold.fact_order", "order_id"),
        ("lakehouse.gold.fact_order_item", "order_item_id"),
        ("lakehouse.gold.dim_customer", "customer_key"),
        ("lakehouse.gold.dim_product", "product_key"),
        ("lakehouse.gold.dim_variant", "variant_key"),
    ):
        df = spark.table(table_name)
        duplicate_rows = (
            df.groupBy(primary_key)
            .count()
            .filter(F.col(primary_key).isNull() | (F.col("count") > 1))
            .count()
        )
        results.append(
            QualityCheckResult(
                check_name="primary_key_unique_not_null",
                dataset=table_name,
                observed_value=str(duplicate_rows),
                expected_value="0",
                passed=duplicate_rows == 0,
                failed_rows=duplicate_rows,
                details=f"duplicate or null {primary_key} groups={duplicate_rows}",
            )
        )

    dim_product = spark.table("lakehouse.gold.dim_product").select("product_key")
    dim_variant = spark.table("lakehouse.gold.dim_variant").select("variant_key")
    orphan_products = (
        fact_order_item.filter(F.col("product_key") > 0)
        .join(dim_product, "product_key", "left_anti")
        .count()
    )
    orphan_variants = (
        fact_order_item.filter(F.col("variant_key") > 0)
        .join(dim_variant, "variant_key", "left_anti")
        .count()
    )
    for key_name, orphan_count in (
        ("product_key", orphan_products),
        ("variant_key", orphan_variants),
    ):
        results.append(
            QualityCheckResult(
                check_name="referential_integrity",
                dataset="lakehouse.gold.fact_order_item",
                observed_value=str(orphan_count),
                expected_value="0",
                passed=orphan_count == 0,
                failed_rows=orphan_count,
                details=f"orphan {key_name} rows={orphan_count}",
            )
        )

    for table_name in (
        "lakehouse.gold.fact_order",
        "lakehouse.gold.fact_order_item",
        "lakehouse.gold.mart_sales_daily",
    ):
        current_run_rows = spark.table(table_name).filter(F.col("_source_run_id") == run_id).count()
        results.append(
            QualityCheckResult(
                check_name="current_run_freshness_marker",
                dataset=table_name,
                observed_value=str(current_run_rows),
                expected_value=">0",
                passed=current_run_rows > 0,
                failed_rows=0 if current_run_rows > 0 else 1,
                details=f"rows published by run {run_id}={current_run_rows}",
            )
        )

    hash_pattern = r"^[0-9a-f]{64}$"
    for table_name, columns in (
        ("lakehouse.gold.dim_customer", ("email", "phone", "full_name")),
        ("lakehouse.gold.dim_delivery_staff", ("phone", "full_name")),
    ):
        df = spark.table(table_name)
        for column_name in columns:
            invalid = df.filter(
                F.col(column_name).isNotNull() & ~F.col(column_name).rlike(hash_pattern)
            ).count()
            results.append(
                QualityCheckResult(
                    check_name="pii_pseudonymization",
                    dataset=f"{table_name}.{column_name}",
                    observed_value=str(invalid),
                    expected_value="0",
                    passed=invalid == 0,
                    failed_rows=invalid,
                    details=f"non-null values not matching SHA-256 token format={invalid}",
                )
            )

    if persist_results:
        persist_quality_results(
            spark,
            results,
            run_id=run_id,
            batch_date=batch_date,
            phase="post_gold",
        )

    failed = [result for result in results if not result.passed and result.severity == "ERROR"]
    summary = {
        "total_checks": len(results),
        "passed_checks": len(results) - len(failed),
        "failed_checks": len(failed),
        "status": "PASSED" if not failed else "FAILED",
        "results": [asdict(result) for result in results],
    }
    if failed:
        messages = "; ".join(f"{item.dataset}.{item.check_name}: {item.details}" for item in failed)
        raise GoldQualityGateError(
            f"Gold quality gate failed with {len(failed)} violation(s): {messages}"
        )
    return summary
