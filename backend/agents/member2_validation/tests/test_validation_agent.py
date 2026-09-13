import pandas as pd

from backend.agents.member2_validation import validate_data, validate_readings


def test_submitted_hydromet_dataset_reproduces_member2_report():
    frame = pd.read_csv("backend/datasets/hydromet/member2_hydromet.csv")
    result = validate_data(frame)
    assert result["score"] == 97.0
    assert result["valid_count"] == 2679
    assert result["flagged_count"] == 121
    assert result["sensor_health"]["reservoir_water_level"]["status"] == "WATCH"


def test_structural_adapter_rejects_duplicate_and_missing_rows():
    result = validate_readings([
        {"instrument_id": "P1", "metric": "pressure", "value": 0, "timestamp": "2026-01-01T00:00:00Z"},
        {"instrument_id": "P1", "metric": "pressure", "value": 1, "timestamp": "2026-01-01T00:00:00Z"},
        {"instrument_id": "P1", "metric": "pressure", "value": None, "timestamp": "2026-01-02T00:00:00Z"},
    ])
    assert result["available"] is True
    assert result["valid_count"] == 0
    assert {flag["reason"] for flag in result["flags"]} >= {"duplicate_timestamp", "missing"}


def test_empty_structural_input_is_unavailable_not_a_zero_quality_result():
    result = validate_readings([])
    assert result["available"] is False
    assert result["score"] is None
