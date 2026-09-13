from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RiskConfig:
    weights: dict[str, float] = field(default_factory=lambda: {
        "data_quality": 0.15,
        "baseline_deviation": 0.25,
        "trend": 0.20,
        "anomaly": 0.25,
        "correlation": 0.15,
    })
    levels: dict[str, int] = field(default_factory=lambda: {"watch": 30, "warning": 50, "critical": 70})
    minimum_baseline_samples: int = 12
    strongest_factor_floor: float = 0.75
    stale_days: int = 45

    def __post_init__(self) -> None:
        if abs(sum(self.weights.values()) - 1) > 1e-9:
            raise ValueError("Risk factor weights must sum to 1.0")
        if not 0 <= self.strongest_factor_floor <= 1:
            raise ValueError("strongest_factor_floor must be between 0 and 1")

    @classmethod
    def from_json(cls, path: str | Path | None = None) -> "RiskConfig":
        if path is None:
            return cls()
        payload: dict[str, Any] = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(**payload)

    def level_for(self, score: float) -> str:
        if score >= self.levels["critical"]:
            return "CRITICAL"
        if score >= self.levels["warning"]:
            return "WARNING"
        if score >= self.levels["watch"]:
            return "WATCH"
        return "NORMAL"
