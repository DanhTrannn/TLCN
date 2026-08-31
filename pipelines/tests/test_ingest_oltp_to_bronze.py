import pytest

pyspark = pytest.importorskip("pyspark", reason="pyspark not installed")

import os
from unittest.mock import MagicMock, patch

from pyspark.sql import SparkSession


@pytest.fixture(scope="session")
def spark():
    return SparkSession.builder.master("local[1]").appName("test-ingest-oltp-to-bronze").getOrCreate()


def test_build_landing_path():
    from jobs.oltp.ingest_oltp_to_bronze import build_landing_path

    path = build_landing_path(
        bucket="lakehouse",
        table="orders",
        extract_date="2026-08-15",
        run_id="run123",
    )
    assert path == "s3a://lakehouse/landing/oltp/orders/extract_date=2026-08-15/run_id=run123/data/*.parquet"


def test_build_target_table():
    from jobs.oltp.ingest_oltp_to_bronze import build_target_table

    assert build_target_table("orders") == "lakehouse.bronze.orders"
    assert build_target_table("customers") == "lakehouse.bronze.customers"


def test_build_quarantine_table():
    from jobs.oltp.ingest_oltp_to_bronze import build_quarantine_table

    assert build_quarantine_table("orders") == "lakehouse.quarantine.orders_errors"
    assert build_quarantine_table("customers") == "lakehouse.quarantine.customers_errors"
