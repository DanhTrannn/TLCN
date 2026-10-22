"""OLTP to Silver Reconciliation Gate.

Verifies data correctness and parity between Source MySQL tables and Iceberg Silver tables
prior to publishing into Gold Dimensions, Facts, and Data Marts.

Acceptance criteria:
- Row counts for critical transactional tables (orders, order_items, payments, etc.)
  must match within the allowed variance tolerance (default: 0.05%).
- Gross revenue totals must reconcile between MySQL orders/payments and Silver facts.
- If variance exceeds the threshold, ReconciliationGateError is raised, halting Gold publishing.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pyspark.sql import SparkSession

from lakehouse.config import Config
from lakehouse.oltp.quality import persist_quality_results

logger = logging.getLogger("lakehouse.reconcile")


class ReconciliationGateError(Exception):
    """Raised when source-to-lakehouse reconciliation checks fail."""

    pass


@dataclass
class MetricReconciliationResult:
    metric_name: str
    table_name: str
    source_value: int
    silver_value: int
    variance_percent: float
    passed: bool
    details: str = ""
    severity: str = "ERROR"
    failed_rows: int = 0


def _variance_percent(source_value: int, target_value: int) -> float:
    """Return a safe variance where 0 -> non-zero is always a 100% mismatch."""
    difference = abs(source_value - target_value)
    if difference == 0:
        return 0.0
    if source_value == 0:
        return 100.0
    return round(difference / abs(source_value) * 100.0, 4)


def _within_tolerance(source_value: int, target_value: int, tolerance_pct: float) -> bool:
    if source_value == 0:
        return target_value == 0
    return _variance_percent(source_value, target_value) <= tolerance_pct


def check_table_counts(
    spark: SparkSession,
    cfg: Config,
    table_names: list[str] | None = None,
    tolerance_pct: float = 0.05,
) -> list[MetricReconciliationResult]:
    results: list[MetricReconciliationResult] = []
    target_tables = table_names or [table.name for table in cfg.tables]

    for tbl_name in target_tables:
        table_spec = cfg.table(tbl_name)
        if not table_spec:
            continue

        # 1. Source MySQL count
        source_df = spark.read.format("jdbc").options(
            url=cfg.jdbc_url,
            query=f"SELECT COUNT(*) AS cnt FROM `{table_spec.name}`",
        ).load()
        source_count = int(source_df.first()["cnt"] or 0)

        # 2. Silver Iceberg count
        silver_table_name = f"lakehouse.silver.{table_spec.silver_table}"
        read_error = None
        try:
            silver_count = int(spark.table(silver_table_name).count())
        except Exception as exc:
            logger.warning("Could not read silver table %s: %s", silver_table_name, exc)
            silver_count = 0
            read_error = str(exc)

        diff = abs(source_count - silver_count)
        variance_pct = _variance_percent(source_count, silver_count)
        passed = read_error is None and _within_tolerance(source_count, silver_count, tolerance_pct)

        results.append(
            MetricReconciliationResult(
                metric_name="row_count",
                table_name=tbl_name,
                source_value=source_count,
                silver_value=silver_count,
                variance_percent=round(variance_pct, 4),
                passed=passed,
                failed_rows=0 if passed else int(diff),
                details=(
                    f"SILVER READ ERROR: {read_error}"
                    if read_error is not None
                    else (
                        f"diff={diff} rows"
                        if passed
                        else f"MISMATCH: source={source_count}, silver={silver_count}, "
                        f"variance={variance_pct:.4f}% > {tolerance_pct}%"
                    )
                ),
            )
        )

    return results


def check_financial_metrics(
    spark: SparkSession,
    cfg: Config,
    tolerance_pct: float = 0.05,
) -> list[MetricReconciliationResult]:
    results: list[MetricReconciliationResult] = []

    from pyspark.sql import functions as F

    metric_specs = (
        (
            "gross_revenue_vnd",
            "orders",
            "SELECT COALESCE(SUM(total_vnd), 0) AS value FROM `orders` WHERE status != 'cancelled'",
            "lakehouse.silver.silver_orders",
            "total_vnd",
            "status != 'cancelled'",
        ),
        (
            "successful_payments_vnd",
            "payments",
            "SELECT COALESCE(SUM(amount_vnd), 0) AS value FROM `payments` WHERE status = 'succeeded'",
            "lakehouse.silver.silver_payments",
            "amount_vnd",
            "status = 'succeeded'",
        ),
        (
            "successful_refunds_vnd",
            "refunds",
            "SELECT COALESCE(SUM(amount_vnd), 0) AS value FROM `refunds` WHERE status = 'succeeded'",
            "lakehouse.silver.silver_refunds",
            "amount_vnd",
            "status = 'succeeded'",
        ),
    )

    for metric_name, table_name, source_query, silver_table, amount_column, predicate in metric_specs:
        source_df = spark.read.format("jdbc").options(
            url=cfg.jdbc_url,
            query=source_query,
        ).load()
        source_value = int(source_df.first()["value"] or 0)

        read_error = None
        try:
            silver_value = int(
                spark.table(silver_table)
                .filter(predicate)
                .select(F.coalesce(F.sum(amount_column), F.lit(0)).alias("value"))
                .first()["value"]
                or 0
            )
        except Exception as exc:
            logger.warning("Could not compute %s from %s: %s", metric_name, silver_table, exc)
            silver_value = 0
            read_error = str(exc)

        difference = abs(source_value - silver_value)
        variance_pct = _variance_percent(source_value, silver_value)
        passed = read_error is None and _within_tolerance(source_value, silver_value, tolerance_pct)
        results.append(
            MetricReconciliationResult(
                metric_name=metric_name,
                table_name=table_name,
                source_value=source_value,
                silver_value=silver_value,
                variance_percent=variance_pct,
                passed=passed,
                failed_rows=0 if passed else 1,
                details=(
                    f"SILVER READ ERROR: {read_error}"
                    if read_error is not None
                    else (
                        f"diff={difference} VND"
                        if passed
                        else f"MISMATCH: source={source_value} VND, silver={silver_value} VND, "
                        f"variance={variance_pct:.4f}% > {tolerance_pct}%"
                    )
                ),
            )
        )

    return results


def run_reconciliation_gate(
    spark: SparkSession,
    cfg: Config,
    tolerance_pct: float = 0.05,
    run_id: str | None = None,
    batch_date: str | None = None,
    persist_results: bool = False,
) -> dict[str, Any]:
    """Execute all reconciliation gate checks and fail if variance exceeds tolerance."""
    all_results: list[MetricReconciliationResult] = []
    all_results.extend(check_table_counts(spark, cfg, tolerance_pct=tolerance_pct))
    all_results.extend(check_financial_metrics(spark, cfg, tolerance_pct=tolerance_pct))

    if persist_results:
        if not run_id or not batch_date:
            raise ValueError("run_id and batch_date are required when persist_results=True")
        persist_quality_results(
            spark,
            all_results,
            run_id=run_id,
            batch_date=batch_date,
            phase="pre_gold_reconciliation",
        )

    failed = [r for r in all_results if not r.passed]
    summary = {
        "total_checks": len(all_results),
        "passed_checks": len(all_results) - len(failed),
        "failed_checks": len(failed),
        "status": "PASSED" if not failed else "FAILED",
        "results": [
            {
                "metric": r.metric_name,
                "table": r.table_name,
                "source": r.source_value,
                "silver": r.silver_value,
                "variance_pct": r.variance_percent,
                "passed": r.passed,
                "details": r.details,
            }
            for r in all_results
        ],
    }

    if failed:
        failure_msg = "; ".join([f"{f.table_name}.{f.metric_name}: {f.details}" for f in failed])
        logger.error("Reconciliation Gate Failed: %s", failure_msg)
        raise ReconciliationGateError(
            f"Reconciliation Gate failed with {len(failed)} violation(s): {failure_msg}"
        )

    logger.info("Reconciliation Gate passed all %d checks successfully.", len(all_results))
    return summary
