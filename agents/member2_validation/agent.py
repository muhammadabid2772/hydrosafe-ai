import pandas as pd
import numpy as np
from typing import Union, Dict, Any

DATE_COLUMN = "Date"

SENSOR_COLUMNS = {
    "reservoir_water_level": {"source": "Reservoir water level", "min": 0.0, "max": None},
    "tail_water_level": {"source": "Tail water level", "min": 0.0, "max": None},
    "in_flow": {"source": "In flow", "min": 0.0, "max": None},
    "daily_mean_temperature": {"source": "Daily mean temperature", "min": -50.0, "max": 60.0},
    "daily_rainfall": {"source": "Daily rainfall", "min": 0.0, "max": None},
}

HEALTHY_MAX_MISSING_RATIO = 0.02
WATCH_MAX_MISSING_RATIO = 0.10
RELATION_TOLERANCE_M = 0.5


def validate_data(data: Union[pd.DataFrame, str, list, dict]) -> Dict[str, Any]:
    """
    Member 2 Data Validation Agent.
    Accepts a DataFrame, CSV file path, or list of dicts.
    Returns data quality score, sensor health status, and flagged records.
    """
    # Parse input formats
    if isinstance(data, str):
        try:
            df = pd.read_csv(data)
        except Exception as e:
            return _empty_report(None, f"Failed to read CSV file: {str(e)}")
    elif isinstance(data, (list, dict)):
        df = pd.DataFrame(data)
    elif isinstance(data, pd.DataFrame):
        df = data
    else:
        df = None

    if df is None or df.empty:
        return _empty_report(df, "Empty or invalid dataset provided.")

    total_records = len(df)
    flags = []
    sensor_health = {}

    # 1. Sensor completeness & health classification
    for key, spec in SENSOR_COLUMNS.items():
        col = spec["source"]
        if col in df.columns:
            missing_count = int(df[col].isna().sum())
            missing_ratio = missing_count / total_records if total_records > 0 else 1.0

            if missing_ratio <= HEALTHY_MAX_MISSING_RATIO:
                status = "HEALTHY"
            elif missing_ratio <= WATCH_MAX_MISSING_RATIO:
                status = "WATCH"
            else:
                status = "POOR"

            sensor_health[key] = {
                "missing_count": missing_count,
                "missing_ratio": round(float(missing_ratio), 4),
                "status": status,
            }

    # 2. Range and hydraulic checks
    for idx, row in df.iterrows():
        # Check physical range limits
        for key, spec in SENSOR_COLUMNS.items():
            col = spec["source"]
            if col in df.columns and pd.notna(row[col]):
                try:
                    val = float(row[col])
                    if spec["min"] is not None and val < spec["min"]:
                        flags.append({"row": idx, "column": col, "reason": "out_of_bounds_low"})
                    if spec["max"] is not None and val > spec["max"]:
                        flags.append({"row": idx, "column": col, "reason": "out_of_bounds_high"})
                except (ValueError, TypeError):
                    flags.append({"row": idx, "column": col, "reason": "non_numeric_value"})

        # Hydraulic relation check: Tail water level <= Reservoir water level + 0.5m
        if "Reservoir water level" in df.columns and "Tail water level" in df.columns:
            res_val = row["Reservoir water level"]
            tail_val = row["Tail water level"]
            if pd.notna(res_val) and pd.notna(tail_val):
                try:
                    if float(tail_val) > (float(res_val) + RELATION_TOLERANCE_M):
                        flags.append({"row": idx, "column": "Tail water level", "reason": "implausible_relation"})
                except (ValueError, TypeError):
                    pass

    flagged_rows = len(set(f["row"] for f in flags))
    valid_count = total_records - flagged_rows
    quality_score = round((valid_count / total_records * 100), 2) if total_records > 0 else 0.0

    if quality_score >= 90.0:
        q_status = "GOOD"
    elif quality_score >= 70.0:
        q_status = "WARNING"
    else:
        q_status = "POOR"

    warning_msg = f"{flagged_rows} records flagged during validation." if flagged_rows > 0 else None

    return {
        "agent": "member2_validation",
        "status": "ok" if flagged_rows == 0 else "ok_with_warning",
        "score": quality_score,
        "total_records": total_records,
        "valid_count": valid_count,
        "flagged_count": flagged_rows,
        "quality_status": q_status,
        "sensor_health": sensor_health,
        "flags": flags[:50],  # Cap output size
        "warning": warning_msg,
    }


def _empty_report(df: Any, message: str) -> Dict[str, Any]:
    return {
        "agent": "member2_validation",
        "status": "ok_with_warning",
        "score": 0.0,
        "total_records": 0 if df is None else len(df),
        "valid_count": 0,
        "flagged_count": 0 if df is None else len(df),
        "quality_status": "POOR",
        "sensor_health": {},
        "flags": [],
        "warning": message,
    }