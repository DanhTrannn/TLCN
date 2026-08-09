import json
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from generator.config import GeneratorConfig
from generator.runner import run


class ManifestRunnerTest(unittest.TestCase):
    def test_manifest_uses_deterministic_uuid_identity(self) -> None:
        config = GeneratorConfig(
            scenario_id="manifest-unit",
            dataset_size="unit",
            seed=11,
            anchor_time=datetime(2026, 7, 1, tzinfo=UTC),
            history_months=3,
            modes=("seed_master",),
            scale={"customers": 2, "products": 2, "variants": 4, "orders": 1},
        )

        with tempfile.TemporaryDirectory() as directory:
            first_path = run(config, Path(directory))
            first_manifest = json.loads(first_path.read_text(encoding="utf-8"))
            second_path = run(config, Path(directory))
            second_manifest = json.loads(second_path.read_text(encoding="utf-8"))

        self.assertEqual(first_path, second_path)
        self.assertEqual(
            first_manifest["identifier_strategy"],
            "uuid5-deterministic-v1",
        )
        self.assertEqual(
            first_manifest["logical_identity"],
            second_manifest["logical_identity"],
        )
        self.assertEqual(
            first_manifest["generation_run_id"],
            second_manifest["generation_run_id"],
        )
        self.assertEqual(
            str(UUID(first_manifest["logical_identity"])),
            first_manifest["logical_identity"],
        )
        self.assertEqual(
            str(UUID(first_manifest["generation_run_id"])),
            first_manifest["generation_run_id"],
        )


if __name__ == "__main__":
    unittest.main()
