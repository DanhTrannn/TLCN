from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from lakehouse.config import TableSpec
from lakehouse.oltp.reconcile import (
    MetricReconciliationResult,
    ReconciliationGateError,
    check_table_counts,
    run_reconciliation_gate,
)
from lakehouse.oltp import reconcile


def test_metric_reconciliation_result_properties():
    res = MetricReconciliationResult(
        metric_name="row_count",
        table_name="orders",
        source_value=100,
        silver_value=100,
        variance_percent=0.0,
        passed=True,
        details="diff=0 rows",
    )
    assert res.passed is True
    assert res.variance_percent == 0.0


def test_check_table_counts_passes_within_tolerance():
    mock_spark = MagicMock()
    mock_cfg = MagicMock()

    table_spec = TableSpec(
        name="orders",
        cursor_field="updated_at",
        pk="order_id",
        mutability="mutable",
        silver_table="silver_orders",
    )
    mock_cfg.table.return_value = table_spec
    mock_cfg.jdbc_url = "jdbc:mysql://localhost:3306/ecommerce"

    # Source returns 1000 rows
    mock_source_df = MagicMock()
    mock_source_df.first.return_value = {"cnt": 1000}
    mock_spark.read.format.return_value.options.return_value.load.return_value = mock_source_df

    # Silver returns 1000 rows
    mock_silver_tbl = MagicMock()
    mock_silver_tbl.count.return_value = 1000
    mock_spark.table.return_value = mock_silver_tbl

    results = check_table_counts(mock_spark, mock_cfg, table_names=["orders"], tolerance_pct=0.05)
    assert len(results) == 1
    assert results[0].passed is True
    assert results[0].variance_percent == 0.0


def test_check_table_counts_fails_exceeding_tolerance():
    mock_spark = MagicMock()
    mock_cfg = MagicMock()

    table_spec = TableSpec(
        name="orders",
        cursor_field="updated_at",
        pk="order_id",
        mutability="mutable",
        silver_table="silver_orders",
    )
    mock_cfg.table.return_value = table_spec
    mock_cfg.jdbc_url = "jdbc:mysql://localhost:3306/ecommerce"

    # Source has 1000 rows, but Silver only has 950 rows (5% variance > 0.05%)
    mock_source_df = MagicMock()
    mock_source_df.first.return_value = {"cnt": 1000}
    mock_spark.read.format.return_value.options.return_value.load.return_value = mock_source_df

    mock_silver_tbl = MagicMock()
    mock_silver_tbl.count.return_value = 950
    mock_spark.table.return_value = mock_silver_tbl

    results = check_table_counts(mock_spark, mock_cfg, table_names=["orders"], tolerance_pct=0.05)
    assert len(results) == 1
    assert results[0].passed is False
    assert results[0].variance_percent == 5.0
    assert "MISMATCH" in results[0].details


def test_check_table_counts_fails_when_source_is_empty_but_silver_is_not():
    mock_spark = MagicMock()
    mock_cfg = MagicMock()
    mock_cfg.table.return_value = TableSpec(
        name="orders",
        cursor_field="updated_at",
        pk="order_id",
        mutability="mutable",
        silver_table="silver_orders",
    )
    mock_cfg.jdbc_url = "jdbc:mysql://localhost:3306/ecommerce"
    mock_source_df = MagicMock()
    mock_source_df.first.return_value = {"cnt": 0}
    mock_spark.read.format.return_value.options.return_value.load.return_value = mock_source_df
    mock_spark.table.return_value.count.return_value = 12

    result = check_table_counts(
        mock_spark,
        mock_cfg,
        table_names=["orders"],
        tolerance_pct=0.05,
    )[0]

    assert result.passed is False
    assert result.variance_percent == 100.0
    assert result.failed_rows == 12


def test_check_table_counts_never_hides_silver_read_errors():
    mock_spark = MagicMock()
    mock_cfg = MagicMock()
    mock_cfg.table.return_value = TableSpec(
        name="orders",
        cursor_field="updated_at",
        pk="order_id",
        mutability="mutable",
        silver_table="silver_orders",
    )
    mock_cfg.jdbc_url = "jdbc:mysql://localhost:3306/ecommerce"
    mock_source_df = MagicMock()
    mock_source_df.first.return_value = {"cnt": 0}
    mock_spark.read.format.return_value.options.return_value.load.return_value = mock_source_df
    mock_spark.table.side_effect = RuntimeError("catalog unavailable")

    result = check_table_counts(mock_spark, mock_cfg, table_names=["orders"])[0]

    assert result.passed is False
    assert "SILVER READ ERROR" in result.details


def test_run_reconciliation_gate_raises_on_failure(monkeypatch):
    mock_spark = MagicMock()
    mock_cfg = MagicMock()

    table_spec = TableSpec(
        name="orders",
        cursor_field="updated_at",
        pk="order_id",
        mutability="mutable",
        silver_table="silver_orders",
    )
    mock_cfg.table.return_value = table_spec
    mock_cfg.tables = (table_spec,)
    mock_cfg.jdbc_url = "jdbc:mysql://localhost:3306/ecommerce"

    # Source 1000, Silver 500 (50% mismatch)
    mock_source_df = MagicMock()
    mock_source_df.first.return_value = {"cnt": 1000}
    mock_spark.read.format.return_value.options.return_value.load.return_value = mock_source_df

    mock_silver_tbl = MagicMock()
    mock_silver_tbl.count.return_value = 500
    mock_spark.table.return_value = mock_silver_tbl
    monkeypatch.setattr(reconcile, "check_financial_metrics", lambda *args, **kwargs: [])

    with pytest.raises(ReconciliationGateError) as exc_info:
        run_reconciliation_gate(mock_spark, mock_cfg, tolerance_pct=0.05)
    assert "Reconciliation Gate failed" in str(exc_info.value)
