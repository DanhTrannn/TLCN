from unittest.mock import MagicMock, patch
import pytest

from app.modules.analytics.trino_client import TrinoClient


def test_trino_client_execute_query_mock():
    mock_post_resp = MagicMock()
    mock_post_resp.status_code = 200
    mock_post_resp.json.return_value = {
        "id": "query_123",
        "nextUri": "http://trino:8080/v1/statement/queued/query_123/1",
    }

    mock_poll_resp_1 = MagicMock()
    mock_poll_resp_1.status_code = 200
    mock_poll_resp_1.json.return_value = {
        "id": "query_123",
        "nextUri": "http://trino:8080/v1/statement/executing/query_123/2",
        "columns": [
            {"name": "order_date", "type": "date"},
            {"name": "gross_revenue_vnd", "type": "bigint"},
        ],
        "data": [["2026-09-25", 10000000]],
    }

    mock_poll_resp_2 = MagicMock()
    mock_poll_resp_2.status_code = 200
    mock_poll_resp_2.json.return_value = {
        "id": "query_123",
        "data": [["2026-09-26", 15000000]],
    }

    client = TrinoClient(base_url="http://trino:8080")

    with patch("httpx.Client") as mock_client_cls:
        mock_http = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_http
        mock_http.post.return_value = mock_post_resp
        mock_http.get.side_effect = [mock_poll_resp_1, mock_poll_resp_2]

        rows = client.execute_query("SELECT order_date, gross_revenue_vnd FROM lakehouse.gold.mart_sales_daily")

        assert len(rows) == 2
        assert rows[0] == {"order_date": "2026-09-25", "gross_revenue_vnd": 10000000}
        assert rows[1] == {"order_date": "2026-09-26", "gross_revenue_vnd": 15000000}


def test_trino_client_execute_scalar_mock():
    mock_post_resp = MagicMock()
    mock_post_resp.status_code = 200
    mock_post_resp.json.return_value = {
        "id": "query_scalar",
        "columns": [{"name": "_col0", "type": "bigint"}],
        "data": [[42]],
    }

    client = TrinoClient(base_url="http://trino:8080")

    with patch("httpx.Client") as mock_client_cls:
        mock_http = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_http
        mock_http.post.return_value = mock_post_resp

        val = client.execute_scalar("SELECT COUNT(*) FROM lakehouse.gold.mart_sales_daily")
        assert val == 42


def test_trino_client_live_query():
    # If Trino is reachable on localhost:8084 or trino:8080, run live query test
    client = TrinoClient(base_url="http://localhost:8084")
    if not client.is_healthy():
        pytest.skip("Localhost Trino on 8084 not reachable")

    rows = client.execute_query("SELECT COUNT(*) AS total_count FROM lakehouse.gold.mart_sales_daily")
    assert len(rows) == 1
    assert "total_count" in rows[0]
    assert rows[0]["total_count"] >= 20
