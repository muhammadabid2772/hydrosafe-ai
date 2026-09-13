from __future__ import annotations

import math
from collections import defaultdict
from datetime import datetime
from typing import Any, Iterable, Mapping

import pandas as pd


DATE_COLUMN = "Date"
SENSOR_COLUMNS = {
    "reservoir_water_level": {"source": "Reservoir water level", "min": 0.0, "max": None},
    "tail_water_level": {"source": "Tail water level", "min": 0.0, "max": None},
    "in_flow": {"source": "In flow", "min": 0.0, "max": None},
    "daily_mean_temperature": {"source": "Daily mean temperature", "min": -50.0, "max": 60.0},
    "daily_rainfall": {"source": "Daily rainfall", "min": 0.0, "max": None},
}
VALIDATION_WEIGHTS = {"completeness": 0.5, "validity": 0.5}
HEALTHY_MAX_MISSING_RATIO = 0.02
WATCH_MAX_MISSING_RATIO = 0.10
RELATION_TOLERANCE_M = 0.5


def _empty_report(total: int, message: str, scope: str) -> dict[str, Any]:
    return {
        "agent": "member2_validation",
        "status": "validation_failed",
        "available": False,
        "scope": scope,
        "score": None,
        "total_records": total,
        "valid_count": 0,
        "flagged_count": total,
        "quality_status": "UNAVAILABLE",
        "sensor_health": {},
        "flags": [],
        "warning": message,
    }


def _health_status(missing_ratio: float, invalid_count: int) -> str:
    if missing_ratio <= HEALTHY_MAX_MISSING_RATIO:
        status = "HEALTHY"
    elif missing_ratio <= WATCH_MAX_MISSING_RATIO:
        status = "WATCH"
    else:
        status = "POOR"
    if invalid_count and status == "HEALTHY":
        return "WATCH"
    return status


def validate_data(data: pd.DataFrame | None, config: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Run Member 2's submitted hydrometeorological validation contract.

    ``config`` remains accepted for notebook compatibility. This validator never
    converts hydrometeorological quality into structural safety evidence.
    """
    del config
    if data is None or len(data) == 0:
        return _empty_report(0 if data is None else len(data), "Empty input: no records received for validation.", "HYDROMET")

    frame = data.copy()
    missing_sources = [spec["source"] for spec in SENSOR_COLUMNS.values() if spec["source"] not in frame.columns]
    if missing_sources:
        return _empty_report(
            len(frame),
            f"Expected sensor columns are missing from input: {missing_sources}.",
            "HYDROMET",
        )
    if DATE_COLUMN not in frame.columns:
        return _empty_report(len(frame), f"Expected timestamp column '{DATE_COLUMN}' is missing.", "HYDROMET")

    total = len(frame)
    timestamps = pd.to_datetime(frame[DATE_COLUMN], errors="coerce")
    duplicated = set(timestamps[timestamps.duplicated(keep=False) & timestamps.notna()].index.tolist())
    flags: list[dict[str, Any]] = []
    flagged_rows: set[int] = set()

    for position, index in enumerate(frame.index):
        stamp = timestamps.at[index]
        stamp_text = stamp.strftime("%Y-%m-%d %H:%M:%S") if pd.notna(stamp) else str(frame.at[index, DATE_COLUMN])
        if pd.isna(stamp):
            flagged_rows.add(position)
            flags.append({"row": position, "timestamp": stamp_text, "sensor": DATE_COLUMN, "reason": "invalid_datetime", "detail": "Value could not be parsed as a timestamp."})

        for name, spec in SENSOR_COLUMNS.items():
            raw = frame.at[index, spec["source"]]
            numeric = pd.to_numeric(pd.Series([raw]), errors="coerce").iloc[0]
            if pd.isna(numeric):
                flagged_rows.add(position)
                reason = "missing" if pd.isna(raw) else "not_numeric"
                detail = f"Empty {name.replace('_', ' ')} reading." if reason == "missing" else f"Non-numeric value {raw!r}."
                flags.append({"row": position, "timestamp": stamp_text, "sensor": name, "reason": reason, "detail": detail})
            elif numeric < spec.get("min", -math.inf) or (spec.get("max") is not None and numeric > spec["max"]):
                flagged_rows.add(position)
                reason = "below_minimum" if numeric < spec.get("min", -math.inf) else "above_maximum"
                flags.append({"row": position, "timestamp": stamp_text, "sensor": name, "reason": reason, "detail": f"{numeric} is outside the configured validation range."})

        reservoir = pd.to_numeric(pd.Series([frame.at[index, "Reservoir water level"]]), errors="coerce").iloc[0]
        tailwater = pd.to_numeric(pd.Series([frame.at[index, "Tail water level"]]), errors="coerce").iloc[0]
        if pd.notna(reservoir) and pd.notna(tailwater) and tailwater > reservoir + RELATION_TOLERANCE_M:
            flagged_rows.add(position)
            flags.append({"row": position, "timestamp": stamp_text, "sensor": "tail_water_level", "reason": "implausible_relation", "detail": f"Tail water level {tailwater} exceeds reservoir level {reservoir} beyond the {RELATION_TOLERANCE_M} m tolerance."})
        if index in duplicated:
            flagged_rows.add(position)
            flags.append({"row": position, "timestamp": stamp_text, "sensor": DATE_COLUMN, "reason": "duplicate_timestamp", "detail": "Timestamp appears more than once."})

    sensor_health: dict[str, Any] = {}
    for name, spec in SENSOR_COLUMNS.items():
        column = frame[spec["source"]]
        numeric = pd.to_numeric(column, errors="coerce")
        missing = int(column.isna().sum())
        non_numeric = int((numeric.isna() & column.notna()).sum())
        below = int(((numeric < spec.get("min", -math.inf)) & numeric.notna()).sum())
        upper = spec.get("max")
        above = int((numeric > upper).sum()) if upper is not None else 0
        missing_ratio = round(missing / total, 4)
        sensor_health[name] = {
            "total": total,
            "missing": missing,
            "missing_ratio": missing_ratio,
            "non_numeric": non_numeric,
            "out_of_range": below + above,
            "status": _health_status(missing_ratio, non_numeric + below + above),
        }

    flagged_count = len(flagged_rows)
    valid_count = total - flagged_count
    completeness = sum(1.0 - item["missing_ratio"] for item in sensor_health.values()) / len(sensor_health)
    validity = valid_count / total
    score = round(100 * (VALIDATION_WEIGHTS["completeness"] * completeness + VALIDATION_WEIGHTS["validity"] * validity), 1)
    quality_status = "GOOD" if score >= 90 else "WATCH" if score >= 70 else "POOR"
    warning = None
    if flagged_count:
        worst_sensor = max(sensor_health, key=lambda key: sensor_health[key]["missing_ratio"])
        warning = f"{flagged_count} of {total} records ({100 * flagged_count / total:.1f}%) are flagged; sensor '{worst_sensor}' carries the most missing readings."
    return {
        "agent": "member2_validation", "status": "ok" if score >= 90 else "ok_with_warning",
        "available": True, "scope": "HYDROMET", "score": score, "total_records": total,
        "valid_count": valid_count, "flagged_count": flagged_count, "quality_status": quality_status,
        "sensor_health": sensor_health, "flags": flags, "warning": warning,
    }


def _reading_dict(reading: Any) -> dict[str, Any]:
    if isinstance(reading, Mapping):
        return dict(reading)
    if hasattr(reading, "model_dump"):
        return reading.model_dump()
    return {key: getattr(reading, key, None) for key in ("instrument_id", "metric", "value", "timestamp", "unit")}


def validate_readings(readings: Iterable[Any] | None) -> dict[str, Any]:
    """Validate the generic structural series Member 3 and Member 6 consume.

    This is a compatibility adapter around Member 2's quality rules. It checks
    completeness, numeric finiteness, timestamps and duplicates. Physical
    action limits remain an engineer-owned threshold input.
    """
    rows = [_reading_dict(item) for item in (readings or [])]
    if not rows:
        return _empty_report(0, "Empty input: no structural readings received for validation.", "STRUCTURAL")

    flags: list[dict[str, Any]] = []
    flagged_rows: set[int] = set()
    grouped: dict[str, list[int]] = defaultdict(list)
    seen: dict[tuple[str, str, str], int] = {}
    missing_cells = 0

    for index, row in enumerate(rows):
        instrument_id = str(row.get("instrument_id") or "").strip()
        metric = str(row.get("metric") or "").strip()
        value = row.get("value")
        timestamp = row.get("timestamp")
        group_key = instrument_id or "unknown"
        grouped[group_key].append(index)
        for field, raw in (("instrument_id", instrument_id), ("metric", metric), ("value", value), ("timestamp", timestamp)):
            if raw is None or raw == "":
                missing_cells += 1
                flagged_rows.add(index)
                flags.append({"row": index, "timestamp": str(timestamp or ""), "sensor": group_key, "reason": "missing", "detail": f"Required field '{field}' is missing."})
        try:
            numeric = float(value)
            if not math.isfinite(numeric):
                raise ValueError
        except (TypeError, ValueError):
            if value not in (None, ""):
                flagged_rows.add(index)
                flags.append({"row": index, "timestamp": str(timestamp or ""), "sensor": group_key, "reason": "not_numeric", "detail": "Reading value is not a finite number."})
        parsed_timestamp: datetime | None = None
        if timestamp not in (None, ""):
            try:
                parsed_timestamp = timestamp if isinstance(timestamp, datetime) else datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
            except ValueError:
                flagged_rows.add(index)
                flags.append({"row": index, "timestamp": str(timestamp), "sensor": group_key, "reason": "invalid_datetime", "detail": "Timestamp could not be parsed."})
        if instrument_id and metric and parsed_timestamp:
            duplicate_key = (instrument_id, metric, parsed_timestamp.isoformat())
            if duplicate_key in seen:
                for duplicate_index in (seen[duplicate_key], index):
                    flagged_rows.add(duplicate_index)
                    flags.append({"row": duplicate_index, "timestamp": parsed_timestamp.isoformat(), "sensor": instrument_id, "reason": "duplicate_timestamp", "detail": "Instrument timestamp appears more than once."})
            else:
                seen[duplicate_key] = index

    total = len(rows)
    sensor_health: dict[str, Any] = {}
    for instrument_id, indices in grouped.items():
        instrument_flags = [item for item in flags if item["row"] in indices]
        affected = len({item["row"] for item in instrument_flags})
        missing = len({item["row"] for item in instrument_flags if item["reason"] == "missing"})
        ratio = round(missing / len(indices), 4) if indices else 0.0
        invalid = affected - missing
        sensor_health[instrument_id] = {
            "total": len(indices), "missing": missing, "missing_ratio": ratio,
            "invalid": invalid, "flagged": affected,
            "status": _health_status(ratio, invalid),
        }

    flagged_count = len(flagged_rows)
    valid_count = total - flagged_count
    completeness = 1 - (missing_cells / (total * 4))
    validity = valid_count / total
    score = round(100 * (VALIDATION_WEIGHTS["completeness"] * completeness + VALIDATION_WEIGHTS["validity"] * validity), 1)
    quality_status = "GOOD" if score >= 90 else "WATCH" if score >= 70 else "POOR"
    warning = None if not flagged_count else f"{flagged_count} of {total} structural readings were excluded before trend and risk analysis."
    return {
        "agent": "member2_validation", "status": "ok" if score >= 90 else "ok_with_warning",
        "available": True, "scope": "STRUCTURAL", "score": score, "total_records": total,
        "valid_count": valid_count, "flagged_count": flagged_count, "quality_status": quality_status,
        "sensor_health": sensor_health, "flags": flags, "warning": warning,
        "checks": ["required_fields", "finite_numeric_value", "valid_timestamp", "duplicate_timestamp"],
        "limitations": ["No engineer-approved physical range was supplied, so physical plausibility is not scored."],
    }
