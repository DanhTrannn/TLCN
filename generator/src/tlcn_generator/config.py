import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class GeneratorConfig:
    scenario_id: str
    dataset_size: str
    seed: int
    anchor_time: datetime
    history_months: int
    modes: tuple[str, ...]
    scale: dict[str, int]

    @property
    def logical_identity(self) -> str:
        payload = json.dumps(
            {
                "scenario_id": self.scenario_id,
                "dataset_size": self.dataset_size,
                "seed": self.seed,
                "anchor_time": self.anchor_time.isoformat(),
                "history_months": self.history_months,
                "modes": self.modes,
                "scale": self.scale,
            },
            sort_keys=True,
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def load_config(path: Path) -> GeneratorConfig:
    raw: dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8"))
    anchor_time = datetime.fromisoformat(str(raw["anchor_time"]).replace("Z", "+00:00"))
    if anchor_time.tzinfo is None:
        raise ValueError("anchor_time must include timezone")
    return GeneratorConfig(
        scenario_id=str(raw["scenario_id"]),
        dataset_size=str(raw["dataset_size"]),
        seed=int(raw["seed"]),
        anchor_time=anchor_time,
        history_months=int(raw["history_months"]),
        modes=tuple(str(mode) for mode in raw["modes"]),
        scale={str(key): int(value) for key, value in raw["scale"].items()},
    )

