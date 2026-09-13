from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .baseline import fit_baselines
from .engine import _z_to_score
from .normalizer import NormalizedReading


def evaluate_temporal_holdout(readings: Iterable[NormalizedReading], minimum_samples: int = 20) -> dict:
    grouped: dict[tuple[str, str, str], list[NormalizedReading]] = defaultdict(list)
    for reading in readings:
        grouped[(reading.structure, reading.instrument_id, reading.metric)].append(reading)
    train: list[NormalizedReading] = []
    test: list[NormalizedReading] = []
    for series in grouped.values():
        ordered = sorted(series, key=lambda item: item.timestamp)
        if len(ordered) < minimum_samples:
            continue
        cut = max(12, int(len(ordered) * 0.8))
        train.extend(ordered[:cut])
        test.extend(ordered[cut:])
    model = fit_baselines(train, minimum_samples=12)
    bands = Counter()
    scores: list[float] = []
    missing_profiles = 0
    for reading in test:
        key = f"{reading.structure}|{reading.instrument_id}|{reading.metric}"
        profile = model["profiles"].get(key)
        if not profile:
            missing_profiles += 1
            continue
        score = _z_to_score((reading.value - profile["median"]) / profile["robust_scale"])
        scores.append(score)
        bands["CRITICAL" if score >= 70 else "WARNING" if score >= 50 else "WATCH" if score >= 30 else "NORMAL"] += 1
    synthetic = {}
    for z_score in (0, 2, 3, 5, 8):
        synthetic[str(z_score)] = round(_z_to_score(z_score), 2)
    total = len(scores)
    return {
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "evaluation_type": "chronological 80/20 stability check; no ground-truth risk labels",
        "series_evaluated": len(model["profiles"]),
        "training_readings": len(train),
        "holdout_readings": len(test),
        "scored_holdout_readings": total,
        "missing_profile_readings": missing_profiles,
        "holdout_band_counts": dict(bands),
        "holdout_band_percent": {key: round(value * 100 / total, 2) for key, value in bands.items()} if total else {},
        "synthetic_robust_z_response": synthetic,
        "synthetic_monotonic": list(synthetic.values()) == sorted(synthetic.values()),
        "interpretation": "Holdout bands measure deviation from earlier history, not false-positive rate or safety accuracy.",
    }


def save_evaluation(report: dict, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
