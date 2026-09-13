from __future__ import annotations

import json
import math
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from statistics import median
from typing import Iterable

import xlrd


HYDROMET_MODEL_VERSION = "hydromet-context-v1"
PREFERRED_SHEET = "2021~2026"
FIELD_COLUMNS = {
    "reservoir_level_m": 1,
    "tailwater_level_m": 2,
    "inflow_m3_s": 3,
    "outflow_m3_s": 4,
    "mean_temperature_c": 5,
    "daily_rainfall_mm": 6,
}


@dataclass(frozen=True)
class HydrometObservation:
    observed_at: str
    reservoir_level_m: float | None
    tailwater_level_m: float | None
    inflow_m3_s: float | None
    outflow_m3_s: float | None
    mean_temperature_c: float | None
    daily_rainfall_mm: float | None


def _number(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def _date(workbook: xlrd.book.Book, cell: xlrd.sheet.Cell) -> date | None:
    try:
        if cell.ctype == xlrd.XL_CELL_DATE or isinstance(cell.value, (int, float)):
            return xlrd.xldate_as_datetime(cell.value, workbook.datemode).date()
        return datetime.fromisoformat(str(cell.value).strip()).date()
    except (TypeError, ValueError, xlrd.XLDateError):
        return None


def read_hydromet_daily(path: str | Path) -> list[HydrometObservation]:
    """Read the reviewed daily table from the supplied legacy XLS without modifying it."""
    workbook = xlrd.open_workbook(str(path), on_demand=True)
    if PREFERRED_SHEET not in workbook.sheet_names():
        raise ValueError(f"Required daily sheet {PREFERRED_SHEET!r} was not found")
    sheet = workbook.sheet_by_name(PREFERRED_SHEET)
    observations: list[HydrometObservation] = []
    seen: set[date] = set()
    for row_index in range(3, sheet.nrows):
        observed_on = _date(workbook, sheet.cell(row_index, 0))
        if observed_on is None or observed_on in seen:
            continue
        seen.add(observed_on)
        values = {name: _number(sheet.cell_value(row_index, column)) for name, column in FIELD_COLUMNS.items()}
        observations.append(HydrometObservation(observed_at=observed_on.isoformat(), **values))
    return sorted(observations, key=lambda item: item.observed_at)


def _profile(values: list[float]) -> dict[str, float | int]:
    ordered = sorted(values)
    centre = median(ordered)
    mad = median([abs(value - centre) for value in ordered])
    robust_scale = max(mad * 1.4826, 1e-9)

    def quantile(fraction: float) -> float:
        position = fraction * (len(ordered) - 1)
        lower = int(position)
        upper = min(lower + 1, len(ordered) - 1)
        weight = position - lower
        return ordered[lower] * (1 - weight) + ordered[upper] * weight

    return {
        "count": len(ordered),
        "median": round(centre, 6),
        "mad": round(mad, 6),
        "robust_scale": round(robust_scale, 6),
        "q05": round(quantile(0.05), 6),
        "q95": round(quantile(0.95), 6),
    }


def build_hydromet_calibration(observations: Iterable[HydrometObservation]) -> dict:
    rows = list(observations)
    if not rows:
        raise ValueError("No valid daily hydrometeorological observations were found")
    groups: dict[tuple[int, str], list[float]] = defaultdict(list)
    for row in rows:
        month = datetime.fromisoformat(row.observed_at).month
        for field in FIELD_COLUMNS:
            value = getattr(row, field)
            if value is not None:
                groups[(month, field)].append(value)
    profiles = {
        f"{month:02d}|{field}": _profile(values)
        for (month, field), values in sorted(groups.items())
        if len(values) >= 12
    }
    dates = [datetime.fromisoformat(row.observed_at).date() for row in rows]
    missing_dates: list[str] = []
    cursor = min(dates)
    present = set(dates)
    while cursor <= max(dates):
        if cursor not in present:
            missing_dates.append(cursor.isoformat())
        cursor += timedelta(days=1)
    field_completeness = {
        field: round(sum(getattr(row, field) is not None for row in rows) / len(rows), 6)
        for field in FIELD_COLUMNS
    }
    latest = rows[-1]
    latest_date = datetime.fromisoformat(latest.observed_at).date()
    last_7 = [row for row in rows if 0 <= (latest_date - datetime.fromisoformat(row.observed_at).date()).days <= 6]
    first_7 = min(last_7, key=lambda row: row.observed_at)
    latest_context = asdict(latest)
    latest_context["rainfall_7d_mm"] = round(
        sum(row.daily_rainfall_mm or 0 for row in last_7), 6
    )
    latest_context["reservoir_change_7d_m"] = (
        round(latest.reservoir_level_m - first_7.reservoir_level_m, 6)
        if latest.reservoir_level_m is not None and first_7.reservoir_level_m is not None
        else None
    )
    return {
        "model_version": HYDROMET_MODEL_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_sheet": PREFERRED_SHEET,
        "row_count": len(rows),
        "date_start": min(dates).isoformat(),
        "date_end": max(dates).isoformat(),
        "missing_dates": missing_dates,
        "field_completeness": field_completeness,
        "monthly_profiles": profiles,
        "latest_context": latest_context,
        "usage": "Context only. It does not independently trigger a structural-risk alarm.",
    }


def save_hydromet_calibration(calibration: dict, path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(calibration, indent=2, ensure_ascii=False), encoding="utf-8")


def write_hydromet_jsonl(observations: Iterable[HydrometObservation], path: str | Path) -> int:
    rows = list(observations)
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("".join(json.dumps(asdict(row), ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    return len(rows)
