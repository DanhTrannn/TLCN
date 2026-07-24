from __future__ import annotations

import json
import sys
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_PATHS = (
    "apps/storefront/package.json",
    "services/ecommerce-api/app/main.py",
    "services/event-collector/app/main.py",
    "database/alembic.ini",
    "generator/configs/small.yml",
    "pipelines/batch/src/tlcn_pipeline/stages.py",
    "ml/repurchase/src/repurchase_ml/stages.py",
    "airflow/dags/tlcn_core_batch.py",
    "airflow/dags/tlcn_repurchase_ml.py",
    "quality/rules/core.yml",
    "dashboards/business-overview/README.md",
    "docker-compose.yml",
    "PROJECT_STRUCTURE.md",
)


def validate_required_paths(errors: list[str]) -> None:
    for relative_path in REQUIRED_PATHS:
        if not (ROOT / relative_path).exists():
            errors.append(f"missing required path: {relative_path}")


def validate_json(errors: list[str]) -> None:
    for path in ROOT.rglob("*.json"):
        if any(part in {"node_modules", ".next"} for part in path.parts):
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except Exception as error:
            errors.append(f"invalid JSON {path.relative_to(ROOT)}: {error}")


def validate_toml(errors: list[str]) -> None:
    for path in ROOT.rglob("*.toml"):
        try:
            tomllib.loads(path.read_text(encoding="utf-8"))
        except Exception as error:
            errors.append(f"invalid TOML {path.relative_to(ROOT)}: {error}")


def validate_python(errors: list[str]) -> None:
    for path in ROOT.rglob("*.py"):
        if any(part in {".venv", "venv", "__pycache__"} for part in path.parts):
            continue
        try:
            compile(path.read_text(encoding="utf-8"), str(path), "exec")
        except Exception as error:
            errors.append(f"invalid Python {path.relative_to(ROOT)}: {error}")


def validate_compose(errors: list[str]) -> None:
    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    for profile in ("core", "batch", "bi", "tools"):
        if f'profiles: ["{profile}"]' not in compose:
            errors.append(f"compose profile missing: {profile}")
    if ":latest" in compose:
        errors.append("docker-compose.yml must not use latest image tags")


def validate_stage_contracts(errors: list[str]) -> None:
    core_dag = (ROOT / "airflow/dags/tlcn_core_batch.py").read_text(encoding="utf-8")
    ml_dag = (ROOT / "airflow/dags/tlcn_repurchase_ml.py").read_text(encoding="utf-8")
    core_stages = (ROOT / "pipelines/batch/src/tlcn_pipeline/stages.py").read_text(encoding="utf-8")
    ml_stages = (ROOT / "ml/repurchase/src/repurchase_ml/stages.py").read_text(encoding="utf-8")
    for required in ("commit_cursors", "publish_pipeline_audit"):
        if required not in core_dag or required not in core_stages:
            errors.append(f"core stage contract missing: {required}")
    for required in ("validate_ml_dataset", "publish_ml_audit"):
        if required not in ml_dag or required not in ml_stages:
            errors.append(f"ML stage contract missing: {required}")


def main() -> int:
    errors: list[str] = []
    validate_required_paths(errors)
    validate_json(errors)
    validate_toml(errors)
    validate_python(errors)
    validate_compose(errors)
    validate_stage_contracts(errors)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    python_count = sum(1 for _ in ROOT.rglob("*.py"))
    print(f"Structure validation passed: {len(REQUIRED_PATHS)} required paths, {python_count} Python files")
    return 0


if __name__ == "__main__":
    sys.exit(main())

