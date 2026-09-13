from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any, Mapping


def _as_dict(reading: Any) -> dict[str, Any]:
    if isinstance(reading, Mapping):
        return dict(reading)
    if hasattr(reading, "model_dump"):
        return reading.model_dump()
    return {
        "value": getattr(reading, "value", None),
        "timestamp": getattr(reading, "timestamp", None),
    }


def _timestamp(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)
    if value in (None, ""):
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc)
    except ValueError:
        return None


def _insufficient(message: str, points: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {
        "available": False,
        "status": "INSUFFICIENT_DATA",
        "trend": "insufficient_data",
        "percentage_change": 0,
        "rate_of_change": 0,
        "rate_unit": "per_observation",
        "sustained": False,
        "sudden_acceleration": False,
        "time_window": len(points or []),
        "score": 0,
        "confidence": 0,
        "evidence": message,
        "chart_points": points or [],
    }


def analyze_trends(readings: list[Any] | None) -> dict[str, Any]:
    """Analyze one instrument series using Member 3's stable public function.

    The original return keys remain intact. Timestamp-aware ordering, a daily
    rate and chart points are additive, backward-compatible fields.
    """
    if not readings:
        return _insufficient("Not enough observations to determine a trend.")

    clean: list[tuple[int, float, datetime | None]] = []
    for index, reading in enumerate(readings):
        row = _as_dict(reading)
        try:
            value = float(row.get("value"))
            if not math.isfinite(value):
                continue
        except (TypeError, ValueError):
            continue
        clean.append((index, value, _timestamp(row.get("timestamp") or row.get("date"))))

    if clean and all(item[2] is not None for item in clean):
        clean.sort(key=lambda item: item[2])

    chart_points = [
        {"timestamp": stamp.isoformat() if stamp else None, "value": value}
        for _, value, stamp in clean
    ]
    if len(clean) < 2:
        return _insufficient("Not enough valid observations to determine a trend.", chart_points)

    values = [item[1] for item in clean]
    first_value, last_value = values[0], values[-1]
    change = last_value - first_value
    percentage_change = (change / abs(first_value) * 100) if first_value != 0 else 0.0
    timestamps = [item[2] for item in clean]
    elapsed_days = None
    if timestamps[0] is not None and timestamps[-1] is not None:
        elapsed_days = (timestamps[-1] - timestamps[0]).total_seconds() / 86400
    if elapsed_days and elapsed_days > 0:
        rate_of_change = change / elapsed_days
        rate_unit = "per_day"
    else:
        rate_of_change = change / (len(values) - 1)
        rate_unit = "per_observation"

    tolerance = max(abs(first_value), abs(last_value), 1.0) * 1e-9
    trend = "increasing" if change > tolerance else "decreasing" if change < -tolerance else "stable"
    changes = [values[index] - values[index - 1] for index in range(1, len(values))]
    increasing_steps = sum(delta > tolerance for delta in changes)
    decreasing_steps = sum(delta < -tolerance for delta in changes)
    total_steps = len(changes)
    required_steps = max(1, math.ceil(total_steps * 0.7))
    sustained = increasing_steps >= required_steps or decreasing_steps >= required_steps

    sudden_acceleration = False
    if len(changes) >= 2:
        recent_change, previous_change = abs(changes[-1]), abs(changes[-2])
        sudden_acceleration = previous_change > tolerance and recent_change >= previous_change * 2

    score = min(100.0, abs(percentage_change) * 10)
    if sudden_acceleration:
        score = min(100.0, score + 20)
    consistency = max(increasing_steps, decreasing_steps) / total_steps
    confidence = min(1.0, 0.5 + consistency * 0.4)
    window_label = (
        f"{elapsed_days:.1f} days across {len(values)} observations"
        if elapsed_days and elapsed_days > 0
        else f"{len(values)} observations"
    )
    evidence = f"The {trend} trend changed by {percentage_change:.2f}% over {window_label}."
    if sustained:
        evidence += " The movement is sustained."
    if sudden_acceleration:
        evidence += " A sudden acceleration was detected."

    return {
        "available": True,
        "status": "READY",
        "trend": trend,
        "percentage_change": round(percentage_change, 2),
        "rate_of_change": round(rate_of_change, 6),
        "rate_unit": rate_unit,
        "sustained": sustained,
        "sudden_acceleration": sudden_acceleration,
        "time_window": len(values),
        "window_start": timestamps[0].isoformat() if timestamps[0] else None,
        "window_end": timestamps[-1].isoformat() if timestamps[-1] else None,
        "score": round(score, 2),
        "confidence": round(confidence, 2),
        "evidence": evidence,
        "chart_points": chart_points,
    }
