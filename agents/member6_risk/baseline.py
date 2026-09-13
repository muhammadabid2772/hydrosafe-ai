from __future__ import annotations

import json
import math
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .normalizer import NormalizedReading


MODEL_VERSION = "hydrosafe-risk-baseline-1.0.0"


def _quantile(sorted_values: list[float], q: float) -> float:
    if len(sorted_values) == 1:
        return sorted_values[0]
    position = (len(sorted_values) - 1) * q
    lower, upper = math.floor(position), math.ceil(position)
    if lower == upper:
        return sorted_values[lower]
    return sorted_values[lower] * (upper - position) + sorted_values[upper] * (position - lower)


def fit_baselines(readings: Iterable[NormalizedReading], minimum_samples: int = 12) -> dict:
    grouped: dict[tuple[str, str, str], list[NormalizedReading]] = defaultdict(list)
    for reading in readings:
        grouped[(reading.structure, reading.instrument_id, reading.metric)].append(reading)
    profiles: dict[str, dict] = {}
    skipped = 0
    for (structure, instrument_id, metric), group in sorted(grouped.items()):
        ordered = sorted(group, key=lambda item: item.timestamp)
        values = sorted(item.value for item in ordered)
        if len(values) < minimum_samples:
            skipped += 1
            continue
        median = statistics.median(values)
        mad = statistics.median(sorted(abs(value - median) for value in values))
        q25, q75 = _quantile(values, 0.25), _quantile(values, 0.75)
        robust_scale = max(1.4826 * mad, (q75 - q25) / 1.349, abs(median) * 1e-6, 1e-9)
        key = f"{structure}|{instrument_id}|{metric}"
        profiles[key] = {
            "structure": structure, "instrument_id": instrument_id,
            "instrument_type": ordered[0].instrument_type, "metric": metric, "unit": ordered[0].unit,
            "count": len(values), "median": median, "mad": mad, "robust_scale": robust_scale,
            "q01": _quantile(values, 0.01), "q05": _quantile(values, 0.05),
            "q25": q25, "q75": q75, "q95": _quantile(values, 0.95), "q99": _quantile(values, 0.99),
            "first_timestamp": ordered[0].timestamp, "last_timestamp": ordered[-1].timestamp,
            "source_file": ordered[0].source_file,
        }
    return {
        "model_version": MODEL_VERSION, "trained_at": datetime.now(timezone.utc).isoformat(),
        "method": "per-instrument robust median/MAD historical calibration", "profiles": profiles,
        "profile_count": len(profiles), "skipped_short_series": skipped,
        "label_status": "No verified incident/action-level labels found; this is not a supervised classifier.",
    }


def save_baselines(model: dict, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(model, ensure_ascii=False, indent=2), encoding="utf-8")


def load_baselines(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))
