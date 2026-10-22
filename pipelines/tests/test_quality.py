from lakehouse.oltp.quality import (
    QUALITY_RESULTS_DDL,
    QUALITY_RESULTS_TABLE,
    _exact_count_check,
    _sql_string,
)


def test_quality_results_table_is_partitioned_audit_evidence():
    assert QUALITY_RESULTS_TABLE == "lakehouse.system.data_quality_results"
    assert "PARTITIONED BY (days(checked_at))" in QUALITY_RESULTS_DDL
    assert "failed_rows" in QUALITY_RESULTS_DDL
    assert "severity" in QUALITY_RESULTS_DDL


def test_exact_count_check_handles_zero_source_mismatch():
    result = _exact_count_check("row_count", "silver.orders", 0, "gold.fact_order", 4)
    assert result.passed is False
    assert result.variance_percent == 100.0
    assert result.failed_rows == 4


def test_exact_count_check_passes_equal_empty_datasets():
    result = _exact_count_check("row_count", "silver.orders", 0, "gold.fact_order", 0)
    assert result.passed is True
    assert result.variance_percent == 0.0


def test_sql_string_escapes_audit_details():
    assert _sql_string("customer's email") == "'customer''s email'"
