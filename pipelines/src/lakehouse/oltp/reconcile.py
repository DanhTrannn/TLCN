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

logger = logging.getLogger("lakehouse.reconcile")


class ReconciliationGateError(Exception):
    """Raised when source-to-lakehouse reconciliation checks fail."""

    pass


@dataclass
class MetricReconciliationResult:
    metric_name: str
    table_name: str
    source_value: float
    silver_value: float
    variance_percent: float
    passed: bool
    details: str = ""


def check_table_counts(
    spark: SparkSession,
    cfg: Config,
    table_names: list[str] | None = None,
    tolerance_pct: float = 0.05,
) -> list[MetricReconciliationResult]:
    results: list[MetricReconciliationResult] = []
    target_tables = table_names or [
        "orders",
        "order_items",
        "payments",
        "customers",
        "products",
        "product_variants",
        "inbound_receipts",
    ]

    for tbl_name in target_tables:
        table_spec = cfg.table(tbl_name)
        if not table_spec:
            continue

        # 1. Source MySQL count
        source_df = spark.read.format("jdbc").options(
            url=cfg.jdbc_url,
            query=f"SELECT COUNT(*) AS cnt FROM `{table_spec.name}`",
        ).load()
        source_count = float(source_df.first()["cnt"] or 0)

        # 2. Silver Iceberg count
        silver_table_name = f"lakehouse.silver.{table_spec.silver_table}"
        try:
            silver_count = float(spark.table(silver_table_name).count())
        except Exception as exc:
            logger.warning("Could not read silver table %s: %s", silver_table_name, exc)
            silver_count = 0.0

        diff = abs(source_count - silver_count)
        variance_pct = (diff / source_count * 100.0) if source_count > 0 else 0.0
        passed = variance_pct <= tolerance_pct

        results.append(
            MetricReconciliationResult(
                metric_name="row_count",
                table_name=tbl_name,
                source_value=source_count,
                silver_value=silver_count,
                variance_percent=round(variance_pct, 4),
                passed=passed,
                details=f"diff={diff:.0f} rows" if passed else f"MISMATCH: source={source_count:.0f}, silver={silver_count:.0f}, variance={variance_pct:.3f}% > {tolerance_pct}%",
            )
        )

    return results


def check_financial_metrics(
    spark: SparkSession,
    cfg: Config,
    tolerance_pct: float = 0.05,
) -> list[MetricReconciliationResult]:
    results: list[MetricReconciliationResult] = []

    # Order revenue check
    source_rev_df = spark.read.format("jdbc").options(
        url=cfg.jdbc_url,
        query="SELECT COALESCE(SUM(total_vnd), 0) AS rev FROM `orders` WHERE status != 'cancelled'",
    ).load()
    source_rev = float(source_rev_df.first()["rev"] or 0)

    try:
        silver_orders = spark.table("lakehouse.silver.silver_orders")
        from pyspark.sql import functions as F

        silver_rev = float(
            silver_orders.filter(F.col("status") != "cancelled")
            .select(F.coalesce(F.sum("total_vnd"), F.lit(0)).alias("rev"))
            .first()["rev"]
            or 0
        )
    except Exception as exc:
        logger.warning("Could not compute silver revenue: %s", exc)
        silver_rev = 0.0

    diff_rev = abs(source_rev - silver_rev)
    var_rev = (diff_rev / source_rev * 100.0) if source_rev > 0 else 0.0
    passed_rev = var_rev <= tolerance_pct

    results.append(
        MetricReconciliationResult(
            metric_name="gross_revenue_vnd",
            table_name="orders",
            source_value=source_rev,
            silver_value=silver_rev,
            variance_percent=round(var_rev, 4),
            passed=passed_rev,
            details=f"diff={diff_rev:.0f} VND" if passed_rev else f"REVENUE MISMATCH: source={source_rev:.0f}, silver={silver_rev:.0f}, variance={var_rev:.3f}% > {tolerance_pct}%",
        )
    )

    return results


def run_reconciliation_gate(
    spark: SparkSession,
    cfg: Config,
    tolerance_pct: float = 0.05,
) -> dict[str, Any]:
    """Execute all reconciliation gate checks and fail if variance exceeds tolerance."""
    all_results: list[MetricReconciliationResult] = []
    all_results.extend(check_table_counts(spark, cfg, tolerance_pct=tolerance_pct))
    all_results.extend(check_financial_metrics(spark, cfg, tolerance_pct=tolerance_pct))

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
