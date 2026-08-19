import gzip
import hashlib
import json
import tempfile
import unittest
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from generator.config import DEFAULT_DISTRIBUTIONS, GeneratorConfig
from generator.log_export import (
    ROUTES,
    _active_customer_indices,
    _window_weight,
    export_logs,
)


class LogExportTest(unittest.TestCase):
    def setUp(self) -> None:
        self.config = GeneratorConfig(
            scenario_id="unit-logs-v1",
            dataset_size="unit",
            seed=42,
            anchor_time=datetime(2026, 4, 1, tzinfo=UTC),
            history_months=1,
            modes=("seed_master", "historical_transactions"),
            scale={"customers": 20, "products": 12, "variants": 36, "orders": 30},
        )

    @staticmethod
    def _files(root: Path) -> dict[str, bytes]:
        return {
            path.relative_to(root).as_posix(): path.read_bytes()
            for path in root.rglob("*")
            if path.is_file()
        }

    @staticmethod
    def _events(root: Path) -> list[dict]:
        events = []
        for path in sorted(root.rglob("*.jsonl.gz")):
            with gzip.open(path, "rt", encoding="utf-8") as stream:
                events.extend(json.loads(line) for line in stream)
        return events

    def test_export_is_deterministic_and_matches_live_layout(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            first = Path(temporary_directory) / "first"
            second = Path(temporary_directory) / "second"
            first_summary = export_logs(self.config, first, expected_requests=180)
            second_summary = export_logs(self.config, second, expected_requests=180)

            self.assertEqual(first_summary.logical_identity, second_summary.logical_identity)
            self.assertEqual(self._files(first), self._files(second))
            self.assertGreater(first_summary.files, 0)
            self.assertEqual(first_summary.manifests, 0)

            # Check that files follow ingest_date=.../ingest_hour=.../<uuid>.jsonl.gz
            for file_path in first.rglob("*.jsonl.gz"):
                rel = file_path.relative_to(first).as_posix()
                self.assertRegex(
                    rel,
                    r"^landing/logs/ingest_date=\d{4}-\d{2}-\d{2}/ingest_hour=\d{2}/service=ecommerce-api/[0-9a-f-]+\.jsonl\.gz$",
                )
                self.assertFalse(file_path.name.startswith("part-"))

            events = self._events(first)
            self.assertEqual(len(events), first_summary.emitted_requests)
            self.assertEqual(len(events), len({event["request"]["id"] for event in events}))
            self.assertTrue(events)

            allowed_route_actions = {
                (route.method, route.route, route.action) for route in ROUTES
            }
            for event in events:
                self.assertEqual(event["schema"], {"name": "ecommerce.access", "version": "1.0.0"})
                self.assertEqual(event["data_origin"], "observed")
                self.assertEqual(event["service"]["environment"], "local")
                self.assertEqual(len(event["service"]["instance_id"]), 12)
                self.assertTrue(all(c in "0123456789abcdef" for c in event["service"]["instance_id"]))
                self.assertNotIn("synthetic", json.dumps(event))
                self.assertIn(
                    (
                        event["http"]["request_method"],
                        event["http"]["route"],
                        event["ecommerce"]["action"],
                    ),
                    allowed_route_actions,
                )
                self.assertNotIn("?", event["http"]["route"])

    def test_double_day_is_covered_and_weighted_above_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            export_logs(self.config, root, expected_requests=80)
            local_zone = ZoneInfo(DEFAULT_DISTRIBUTIONS.business_timezone)
            local_dates = {
                datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))
                .astimezone(local_zone)
                .date()
                for event in self._events(root)
            }
            self.assertIn(datetime(2026, 3, 3).date(), local_dates)

        sale_window = datetime(2026, 3, 2, 17, tzinfo=UTC)  # 00:00 on 3/3 in Vietnam
        baseline_window = sale_window - timedelta(days=1)
        self.assertGreater(
            _window_weight(sale_window, self.config),
            _window_weight(baseline_window, self.config) * 4,
        )

    def test_authenticated_actors_use_active_oltp_customer_ids(self) -> None:
        active_indices = _active_customer_indices(self.config)
        namespace = uuid.UUID(self.config.logical_identity)
        expected_keys = {
            str(uuid.uuid5(namespace, f"customer:{index}")) for index in active_indices
        }
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            export_logs(self.config, root, expected_requests=240)
            actor_keys = {
                event["actor"]["key"]
                for event in self._events(root)
                if event["actor"]["type"] == "customer"
            }
        self.assertTrue(actor_keys)
        self.assertTrue(actor_keys <= expected_keys)


if __name__ == "__main__":
    unittest.main()
