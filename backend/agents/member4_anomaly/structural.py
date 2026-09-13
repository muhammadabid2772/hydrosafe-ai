from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from math import log10
from typing import Any

import numpy as np
from sklearn.ensemble import IsolationForest

from backend.agents.member6_risk.models import SignalInput


MODEL_VERSION = "member4-structural-robust-v1"
MIN_BASELINE_POINTS = 3
MIN_ISOLATION_POINTS = 12


def _iso_timestamp(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def _robust_scale(values: np.ndarray) -> tuple[float, float]:
    median = float(np.median(values))
    mad = float(np.median(np.abs(values - median)))
    robust = 1.4826 * mad
    if robust <= 1e-12:
        robust = float(np.std(values, ddof=0))
    if robust <= 1e-12:
        robust = 1.0
    return median, robust


def analyze_structural_anomalies(rows: list[dict[str, Any]]) -> tuple[dict[str, Any], list[SignalInput]]:
    """Screen validated structural series for unusual latest observations.

    This intentionally uses only statistical evidence. It does not create or infer
    site action levels. A signal is emitted only when the latest point is unusual
    relative to the preceding points in the same instrument/metric series.
    """
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["instrument_id"]), str(row["metric"]))].append(row)

    assessments: list[dict[str, Any]] = []
    signals: list[SignalInput] = []

    for (instrument_id, metric), items in sorted(grouped.items()):
        items.sort(key=lambda item: _iso_timestamp(item["timestamp"]))
        if len(items) < MIN_BASELINE_POINTS + 1:
            assessments.append({
                "instrument_id": instrument_id,
                "metric": metric,
                "available": False,
                "status": "INSUFFICIENT_HISTORY",
                "sample_count": len(items),
                "message": f"At least {MIN_BASELINE_POINTS + 1} validated observations are required.",
            })
            continue

        current = items[-1]
        baseline = np.asarray([float(item["value"]) for item in items[:-1]], dtype=float)
        current_value = float(current["value"])
        median, robust_scale = _robust_scale(baseline)
        robust_z = abs(current_value - median) / robust_scale

        rolling = baseline[-min(len(baseline), 12):]
        rolling_mean = float(np.mean(rolling))
        rolling_std = float(np.std(rolling, ddof=0))
        rolling_z = abs(current_value - rolling_mean) / rolling_std if rolling_std > 1e-12 else 0.0

        isolation_flag = False
        isolation_score = None
        if len(baseline) >= MIN_ISOLATION_POINTS and float(np.std(baseline, ddof=0)) > 1e-12:
            contamination = min(max(1.0 / len(baseline), 0.02), 0.1)
            model = IsolationForest(n_estimators=200, contamination=contamination, random_state=42)
            model.fit(baseline.reshape(-1, 1))
            isolation_flag = bool(model.predict([[current_value]])[0] == -1)
            isolation_score = float(-model.score_samples([[current_value]])[0])

        anomaly = bool(robust_z >= 3.0 or rolling_z >= 3.0 or (isolation_flag and max(robust_z, rolling_z) >= 2.0))
        deviation = max(robust_z, rolling_z)
        score = min(100.0, deviation * 20.0 + (10.0 if isolation_flag else 0.0))
        if anomaly:
            score = max(score, 55.0)
        severity = "High" if score >= 80 else "Moderate" if anomaly else "Normal"
        confidence = min(0.95, 0.55 + 0.1 * log10(max(len(baseline), 1)))
        observed_at = _iso_timestamp(current["timestamp"])
        evidence = (
            f"{instrument_id} {metric} latest value {current_value:g} is {robust_z:.2f} robust SD from the prior median "
            f"and {rolling_z:.2f} rolling SD from the recent mean across {len(baseline)} baseline observations."
        )

        assessment = {
            "instrument_id": instrument_id,
            "instrument_type": current.get("instrument_type"),
            "metric": metric,
            "unit": current.get("unit"),
            "available": True,
            "status": "ANOMALY" if anomaly else "NORMAL",
            "sample_count": len(items),
            "baseline_count": len(baseline),
            "current_value": current_value,
            "baseline_median": round(median, 8),
            "robust_scale": round(robust_scale, 8),
            "robust_z": round(float(robust_z), 6),
            "rolling_z": round(float(rolling_z), 6),
            "isolation_forest_flag": isolation_flag,
            "isolation_forest_score": round(isolation_score, 6) if isolation_score is not None else None,
            "anomaly": anomaly,
            "severity": severity,
            "score": round(score, 2),
            "confidence": round(confidence, 3),
            "observed_at": observed_at.isoformat(),
            "evidence": evidence,
            "model_version": MODEL_VERSION,
        }
        assessments.append(assessment)

        if anomaly:
            signals.append(SignalInput(
                instrument_id=instrument_id,
                metric=metric,
                score=round(score, 2),
                confidence=round(confidence, 3),
                evidence=evidence,
                scope="STRUCTURAL",
                source_agent="member4_structural_anomaly",
                observed_at=observed_at,
                details={
                    "severity": severity,
                    "robust_z": round(float(robust_z), 6),
                    "rolling_z": round(float(rolling_z), 6),
                    "isolation_forest_flag": isolation_flag,
                    "model_version": MODEL_VERSION,
                },
            ))

    ready = [item for item in assessments if item.get("available")]
    return {
        "available": bool(ready),
        "status": "READY" if ready else "UNAVAILABLE",
        "agent": "member4_structural_anomaly",
        "model_version": MODEL_VERSION,
        "series_count": len(assessments),
        "ready_series_count": len(ready),
        "anomaly_count": sum(1 for item in ready if item.get("anomaly")),
        "assessments": assessments,
        "limitations": [
            "Statistical anomaly screening is not an engineer-approved action level.",
            "The latest point is compared only with validated history supplied for the same instrument and metric.",
            "Short series use robust and rolling deviation only; Isolation Forest is enabled when at least 12 baseline points exist.",
        ],
    }, signals
