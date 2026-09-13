from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from backend.agents.member4_anomaly.core import Member4Detector, PARAMETERS, normalize_history
from backend.agents.member4_anomaly.models import Member4CurrentConditions


ROOT = Path(__file__).parents[4]
DATASET = ROOT / "backend" / "datasets" / "hydromet" / "member4_hydromet.csv"
ORIGINAL_APP = Path(__file__).parents[1] / "original" / "app.py"


def test_original_member4_app_is_frozen():
    digest = hashlib.sha256(ORIGINAL_APP.read_bytes()).hexdigest()
    assert digest == "ef2439630840992b7343e43aa2cd2efbe4c5a6e8d4eb263affa0433f87278075"


def test_provided_human_headers_are_normalized_without_mutating_input():
    frame = pd.DataFrame(
        {
            "Date": pd.date_range("2025-01-01", periods=30),
            "Reservoir water level": np.arange(30) + 450,
            "Tail water level": np.arange(30) + 390,
            "In flow": np.arange(30) + 100,
            "Daily rainfall": np.arange(30),
            "Daily mean temperature": np.arange(30) + 10,
        }
    )
    original_columns = list(frame.columns)
    normalized, quality = normalize_history(frame)
    assert list(frame.columns) == original_columns
    assert set(PARAMETERS).issubset(normalized.columns)
    assert quality.raw_rows == quality.complete_rows == 30


def test_shared_dataset_matches_reviewed_coverage_and_completeness():
    history, quality = normalize_history(pd.read_csv(DATASET))
    assert quality.raw_rows == 2800
    assert quality.complete_rows == 2679
    assert quality.date_start == "2019-01-01"
    assert quality.date_end == "2026-09-01"
    assert quality.missing_by_parameter == {
        "reservoir_level": 120,
        "tailwater": 120,
        "inflow": 0,
        "rainfall": 0,
        "temperature": 1,
    }
    assert len(history) == 2679


def test_pure_detector_matches_member4_original_formula():
    history, _ = normalize_history(pd.read_csv(DATASET))
    detector = Member4Detector(history)
    current = Member4CurrentConditions(
        reservoir_level=461.0,
        tailwater=394.0,
        inflow=2200.0,
        rainfall=90.0,
        temperature=34.0,
    )
    result = detector.assess(current)

    values = history[PARAMETERS].astype(float)
    scaler = StandardScaler()
    scaled = scaler.fit_transform(values)
    current_frame = pd.DataFrame([current.model_dump()], columns=PARAMETERS)
    current_scaled = scaler.transform(current_frame)
    means = values.mean()
    stds = values.std(ddof=0).replace(0, np.nan).fillna(1.0)
    expected_z = ((pd.Series(current.model_dump()) - means) / stds).abs()
    contamination = min(max(1.0 / max(len(history), 100), 0.005), 0.05)
    model = IsolationForest(n_estimators=300, contamination=contamination, random_state=42)
    model.fit(scaled)
    expected_label = int(model.predict(current_scaled)[0])
    expected_anomaly = bool((expected_z >= 3.0).any() or (expected_label == -1 and float(expected_z.max()) >= 2.0))

    assert result.max_abs_z == pytest.approx(float(expected_z.max()), abs=1e-6)
    assert result.isolation_forest_flag is (expected_label == -1)
    assert result.anomaly is expected_anomaly


def test_current_negative_hydrology_is_rejected():
    with pytest.raises(ValueError):
        Member4CurrentConditions(
            reservoir_level=459,
            tailwater=391,
            inflow=-1,
            rainfall=0,
            temperature=25,
        )


def test_structural_screen_flags_large_latest_deviation():
    from datetime import datetime, timezone
    from backend.agents.member4_anomaly.structural import analyze_structural_anomalies

    rows = [
        {"instrument_id": "P1", "metric": "pressure", "value": 10 + (index % 2) * 0.1, "timestamp": datetime(2026, 1, index + 1, tzinfo=timezone.utc)}
        for index in range(12)
    ]
    rows.append({"instrument_id": "P1", "metric": "pressure", "value": 30, "timestamp": datetime(2026, 1, 13, tzinfo=timezone.utc)})
    summary, signals = analyze_structural_anomalies(rows)
    assert summary["anomaly_count"] == 1
    assert signals[0].scope == "STRUCTURAL"
    assert signals[0].source_agent == "member4_structural_anomaly"
