"""Trino distributed query engine REST client for Lakehouse Iceberg DWH."""

import logging
import os
import time
from typing import Any
import httpx

from app.core.errors import INTERNAL_ERROR, AppError

logger = logging.getLogger(__name__)


class TrinoClient:
    """HTTP REST client to query Trino Coordinator."""

    def __init__(
        self,
        base_url: str | None = None,
        catalog: str = "lakehouse",
        schema: str = "gold",
        user: str = "admin",
    ) -> None:
        self.base_url = (
            base_url
            or os.getenv("API_TRINO_URL")
            or os.getenv("TRINO_URL")
            or "http://trino:8080"
        ).rstrip("/")
        self.catalog = catalog
        self.schema = schema
        self.user = user

    def _get_headers(self) -> dict[str, str]:
        return {
            "X-Trino-User": self.user,
            "X-Trino-Catalog": self.catalog,
            "X-Trino-Schema": self.schema,
            "Content-Type": "text/plain",
        }

    def is_healthy(self, timeout: float = 2.0) -> bool:
        """Check if Trino coordinator is reachable and active."""
        try:
            with httpx.Client(timeout=timeout) as client:
                resp = client.get(f"{self.base_url}/v1/info")
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("coordinator") is True and not data.get("starting", False)
                return False
        except Exception:
            return False

    def execute_query(self, sql: str, timeout: float = 30.0) -> list[dict[str, Any]]:
        """Execute SQL query against Trino and return list of dictionaries."""
        clean_sql = sql.strip().rstrip(";")
        url = f"{self.base_url}/v1/statement"
        headers = self._get_headers()

        try:
            with httpx.Client(timeout=timeout) as client:
                post_resp = client.post(url, headers=headers, content=clean_sql.encode("utf-8"))
                if post_resp.status_code != 200:
                    raise AppError(
                        INTERNAL_ERROR,
                        f"Lỗi khởi tạo truy vấn Trino ({post_resp.status_code}): {post_resp.text}",
                        status_code=500,
                    )

                body = post_resp.json()
                next_uri = body.get("nextUri")
                columns: list[str] = [c["name"] for c in body.get("columns", [])]
                all_rows: list[list[Any]] = body.get("data", [])

                start_time = time.time()
                while next_uri:
                    if time.time() - start_time > timeout:
                        raise AppError(
                            INTERNAL_ERROR,
                            f"Trino query timed out after {timeout} seconds",
                            status_code=504,
                        )

                    poll_resp = client.get(next_uri)
                    if poll_resp.status_code != 200:
                        raise AppError(
                            INTERNAL_ERROR,
                            f"Lỗi polling kết quả Trino: {poll_resp.status_code}",
                            status_code=500,
                        )

                    poll_body = poll_resp.json()

                    if "error" in poll_body:
                        err = poll_body["error"]
                        err_msg = err.get("message", "Unknown Trino execution error")
                        logger.error("Trino SQL execution failed for %s: %s", clean_sql, err_msg)
                        raise AppError(
                            INTERNAL_ERROR,
                            f"Lỗi thực thi Trino DWH: {err_msg}",
                            status_code=500,
                        )

                    if not columns and "columns" in poll_body:
                        columns = [c["name"] for c in poll_body["columns"]]

                    if "data" in poll_body:
                        all_rows.extend(poll_body["data"])

                    next_uri = poll_body.get("nextUri")

                if not columns and not all_rows:
                    return []

                return [dict(zip(columns, row)) for row in all_rows]

        except AppError:
            raise
        except Exception as exc:
            logger.error("Failed to connect or execute Trino statement: %s", exc)
            raise AppError(
                INTERNAL_ERROR,
                f"Không thể kết nối đến Trino DWH Coordinator ({self.base_url}): {exc}",
                status_code=500,
            ) from exc

    def execute_scalar(self, sql: str, timeout: float = 30.0) -> Any:
        """Execute SQL query and return first column of the first row."""
        rows = self.execute_query(sql, timeout=timeout)
        if not rows:
            return None
        first_row = rows[0]
        return next(iter(first_row.values())) if first_row else None


# Default singleton instance
default_trino_client = TrinoClient()
