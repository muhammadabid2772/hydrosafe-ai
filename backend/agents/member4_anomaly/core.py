from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from .models import (
    Member4AnomalyResponse,
    Member4CurrentConditions,
    Member4HistoryQuality,
    Member4ParameterAssessment,
)


MODEL_VERSION = "member4-zscore-isolationforest-v1"
PARAMETERS = ["reservoir_level", "tailwater", "inflow", "rainfall", "temperature"]
LABELS = {
    "reservoir_level": "Reservoir Level",
    "tailwater": "Tailwater",
    "inflow": "Inflow",
    "rainfall": "Rainfall",
    "temperature": "Temperature",
}
UNITS = {
    "reservoir_level": "m",
    "tailwater": "m",
    "inflow": "m3/s",
    "rainfall": "mm",
    "temperature": "C",
}
COLUMN_ALIASES = {
    "Date": "date",
    "Reservoir water level": "reservoir_level",
    "Tail water level": "tailwater",
    "In flow": "inflow",
    "Daily rainfall": "rainfall",
    "Daily mean temperature": "temperature",
}


def normalize_history(frame: pd.DataFrame) -> tuple[pd.DataFrame, Member4HistoryQuality]:
    """Normalize the provided Member 4 CSV without changing its source rows."""
    renamed = frame.copy()
    rename = {
        source: target
        for source, target in COLUMN_ALIASES.items()
        if source in renamed.columns and target not in renamed.columns
    }
    renamed = renamed.rename(columns=rename)
    missing_columns = [column for column in PARAMETERS if column not in renamed.columns]
    if missing_columns:
        raise ValueError("Historical CSV is missing: " + ", ".join(missing_columns))

    raw_rows = len(renamed)
    for column in PARAMETERS:
        renamed[column] = pd.to_numeric(renamed[column], errors="coerce")

    warnings: list[str] = []
    parsed_dates = None
    if "date" in renamed.columns:
        parsed_dates = pd.to_datetime(renamed["date"], errors="coerce", format="mixed", dayfirst=False)
        invalid_dates = int(parsed_dates.isna().sum())
        if invalid_dates:
            warnings.append(f"{invalid_dates} row(s) have an invalid date; dates do not affect Member 4 scoring.")
        renamed["date"] = parsed_dates

    missing_by_parameter = {column: int(renamed[column].isna().sum()) for column in PARAMETERS}
    complete = renamed.dropna(subset=PARAMETERS).reset_index(drop=True)
    if len(complete) < 30:
        raise ValueError("Please provide at least 30 complete historical rows.")

    if (complete["rainfall"] < 0).any():
        warnings.append("Historical rainfall contains negative values; verify source units and quality flags.")
    if (complete["inflow"] < 0).any():
        warnings.append("Historical inflow contains negative values; verify source units and quality flags.")

    if parsed_dates is not None and parsed_dates.notna().any():
        dated = renamed.loc[parsed_dates.notna() & renamed["reservoir_level"].notna(), ["date", "reservoir_level"]]
        if not dated.empty:
            annual_means = dated.groupby(dated["date"].dt.year)["reservoir_level"].mean()
            if len(annual_means) > 1 and float(annual_means.max() - annual_means.min()) >= 10:
                warnings.append(
                    "Reservoir history contains materially different operating regimes; the original global baseline does not model them separately."
                )

    valid_dates = parsed_dates.dropna() if parsed_dates is not None else pd.Series(dtype="datetime64[ns]")
    quality = Member4HistoryQuality(
        raw_rows=raw_rows,
        complete_rows=len(complete),
        date_start=valid_dates.min().date().isoformat() if not valid_dates.empty else None,
        date_end=valid_dates.max().date().isoformat() if not valid_dates.empty else None,
        missing_by_parameter=missing_by_parameter,
        warnings=warnings,
    )
    return complete, quality


class Member4Detector:
    """Pure, cached equivalent of Member 4's deterministic screening calculation."""

    def __init__(self, history: pd.DataFrame):
        self.history, self.history_quality = normalize_history(history)
        values = self.history[PARAMETERS].astype(float)
        self.means = values.mean()
        self.stds = values.std(ddof=0).replace(0, np.nan).fillna(1.0)
        self.minimums = values.min()
        self.maximums = values.max()
        self.scaler = StandardScaler()
        scaled = self.scaler.fit_transform(values)
        self.contamination = min(max(1.0 / max(len(self.history), 100), 0.005), 0.05)
        self.model = IsolationForest(
            n_estimators=300,
            contamination=self.contamination,
            random_state=42,
        )
        self.model.fit(scaled)

    @classmethod
    def from_csv(cls, path: str | Path) -> "Member4Detector":
        return cls(pd.read_csv(path))

    def assess(
        self,
        current: Member4CurrentConditions,
        observed_at: datetime | None = None,
    ) -> Member4AnomalyResponse:
        current_values = current.model_dump()
        current_series = pd.Series(current_values, index=PARAMETERS, dtype=float)
        current_frame = pd.DataFrame([current_values], columns=PARAMETERS)
        current_scaled = self.scaler.transform(current_frame)
        z = ((current_series - self.means) / self.stds).abs()
        z_flags = z >= 3.0
        max_z = float(z.max())
        iso_label = int(self.model.predict(current_scaled)[0])
        iso_score = float(-self.model.score_samples(current_scaled)[0])
        anomaly = bool(z_flags.any() or (iso_label == -1 and max_z >= 2.0))
        if max_z >= 4.0 or int(z_flags.sum()) >= 2:
            severity = "High"
        elif anomaly:
            severity = "Moderate"
        else:
            severity = "Normal"

        assessments = [
            Member4ParameterAssessment(
                metric=parameter,
                label=LABELS[parameter],
                value=float(current_values[parameter]),
                unit=UNITS[parameter],
                historical_mean=float(self.means[parameter]),
                historical_std=float(self.stds[parameter]),
                historical_min=float(self.minimums[parameter]),
                historical_max=float(self.maximums[parameter]),
                abs_z=float(z[parameter]),
                flagged=bool(z_flags[parameter]),
            )
            for parameter in PARAMETERS
        ]
        drivers = sorted(assessments, key=lambda item: item.abs_z, reverse=True)
        if anomaly:
            driver_names = [item.label for item in drivers if item.flagged] or [drivers[0].label]
            named = ", ".join(driver_names)
            verb = "provides" if len(driver_names) == 1 else "provide"
            interpretation = (
                f"{severity} statistical anomaly detected. {named} {verb} the strongest deviation. "
                "Verify source readings, units and nearby structural instruments before drawing an engineering conclusion."
            )
        else:
            interpretation = (
                "No significant anomaly was detected in the five supplied hydrometeorological parameters. "
                "Continue the approved monitoring schedule and review structural instruments separately."
            )

        timestamp = observed_at or datetime.now(timezone.utc)
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        return Member4AnomalyResponse(
            model_version=MODEL_VERSION,
            observed_at=timestamp,
            anomaly=anomaly,
            severity=severity,
            max_abs_z=round(max_z, 6),
            isolation_forest_flag=iso_label == -1,
            isolation_forest_score=round(iso_score, 6),
            contamination=round(self.contamination, 6),
            parameters=assessments,
            history_quality=self.history_quality,
            engineering_interpretation=interpretation,
            limitations=[
                "This is a statistical screening result, not an approved dam-safety action level.",
                "The current model uses one global historical baseline and does not model seasonality or operating regimes separately.",
                "Hydrometeorological anomalies require structural corroboration and qualified engineering review.",
            ],
        )
