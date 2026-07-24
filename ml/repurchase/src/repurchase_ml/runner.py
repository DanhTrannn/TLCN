import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from repurchase_ml import __version__
from repurchase_ml.stages import ML_STAGES


def run_stage(
    stage_name: str,
    run_id: str,
    logical_date: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if stage_name not in ML_STAGES:
        raise ValueError(f"unsupported ML stage: {stage_name}")
    safe_run_id = re.sub(r"[^a-zA-Z0-9_.-]", "_", run_id)
    base = Path(os.getenv("PIPELINE_RUN_DIRECTORY", "/data/pipeline-runs"))
    run_directory = base / "ml" / safe_run_id
    run_directory.mkdir(parents=True, exist_ok=True)
    record = {
        "pipeline": "tlcn_repurchase_ml",
        "stage": stage_name,
        "run_id": run_id,
        "logical_date": logical_date,
        "executed_at": datetime.now(UTC).isoformat(),
        "code_version": __version__,
        "status": "scaffold",
        "metadata": metadata or {},
    }
    target = run_directory / f"{stage_name}.json"
    temporary = target.with_suffix(".tmp")
    temporary.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    temporary.replace(target)
    print(json.dumps(record, ensure_ascii=False))
    return record

