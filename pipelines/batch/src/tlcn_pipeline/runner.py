import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from tlcn_pipeline import __version__
from tlcn_pipeline.stages import CORE_STAGES


def run_stage(
    stage_name: str,
    run_id: str,
    logical_date: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if stage_name not in CORE_STAGES:
        raise ValueError(f"unsupported pipeline stage: {stage_name}")
    safe_run_id = re.sub(r"[^a-zA-Z0-9_.-]", "_", run_id)
    run_directory = Path(os.getenv("PIPELINE_RUN_DIRECTORY", "/data/pipeline-runs")) / safe_run_id
    run_directory.mkdir(parents=True, exist_ok=True)
    record = {
        "pipeline": "tlcn_core_batch",
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

