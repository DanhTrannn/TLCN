import json
from datetime import UTC, datetime
from pathlib import Path

from tlcn_generator import __version__
from tlcn_generator.config import GeneratorConfig


SUPPORTED_MODES = {
    "seed_master",
    "historical_transactions",
    "failure_fixtures",
    "repurchase_history",
}


def run(config: GeneratorConfig, output_directory: Path) -> Path:
    unsupported = set(config.modes) - SUPPORTED_MODES
    if unsupported:
        raise ValueError(f"unsupported generator modes: {sorted(unsupported)}")
    output_directory.mkdir(parents=True, exist_ok=True)
    manifest = {
        "scenario_id": config.scenario_id,
        "dataset_size": config.dataset_size,
        "logical_identity": config.logical_identity,
        "seed": config.seed,
        "anchor_time": config.anchor_time.isoformat(),
        "history_months": config.history_months,
        "modes": list(config.modes),
        "scale": config.scale,
        "generator_version": __version__,
        "data_origin": "synthetic",
        "generated_at": datetime.now(UTC).isoformat(),
        "implementation_status": "sql_export_available",
    }
    path = output_directory / f"{config.scenario_id}-{config.logical_identity}.manifest.json"
    temporary_path = path.with_suffix(".tmp")
    temporary_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    temporary_path.replace(path)
    return path

