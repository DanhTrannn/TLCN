from __future__ import annotations

import pytest
from jobs.oltp.build_oltp_gold import (
    VALID_STAGES,
    parse_args,
    run_gold_dimensions,
    run_gold_facts,
    run_gold_marts,
)


def test_valid_stages_declaration():
    """Ensure all required Gold stages are recognized."""
    assert "all" in VALID_STAGES
    assert "dimensions" in VALID_STAGES
    assert "facts" in VALID_STAGES
    assert "marts" in VALID_STAGES


def test_parse_args_default_stage():
    """When --stage is omitted, default to 'all' for backward compatibility."""
    args = parse_args(["--run-id", "run-101"])
    assert args.run_id == "run-101"
    assert args.stage == "all"
    assert args.snapshot_date is not None


def test_parse_args_explicit_stages():
    """Verify parsing for each explicit Gold stage."""
    args_dim = parse_args(["--run-id", "run-101", "--stage", "dimensions"])
    assert args_dim.stage == "dimensions"

    args_fact = parse_args(["--run-id", "run-101", "--stage", "facts"])
    assert args_fact.stage == "facts"

    args_marts = parse_args(["--run-id", "run-101", "--stage", "marts"])
    assert args_marts.stage == "marts"


def test_parse_args_invalid_stage_rejected():
    """Invalid stage names must be rejected."""
    with pytest.raises(SystemExit):
        parse_args(["--run-id", "run-101", "--stage", "unsupported_stage"])


def test_modular_functions_callable():
    """Verify modular functions are defined and callable."""
    assert callable(run_gold_dimensions)
    assert callable(run_gold_facts)
    assert callable(run_gold_marts)
