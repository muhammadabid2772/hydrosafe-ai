from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_latest_connects_member2_member3_and_member6():
    response = client.get("/api/analysis/latest?project_id=test-dam")
    assert response.status_code == 200
    payload = response.json()
    assert payload["data_mode"] == "HISTORICAL_REPLAY"
    assert payload["quality"]["available"] is True
    assert payload["quality"]["reference_dataset"]["score"] == 97.0
    assert payload["trends"]["available"] is True
    assert len(payload["trends"]["series"][0]["chart_points"]) == 10
    assert payload["risk"]["assessment_status"] == "ASSESSED"
    assert payload["report"]["member4_required"] is False


def test_empty_run_returns_unavailable_results_without_mock_substitution():
    response = client.post("/api/analysis/run", json={"project_id": "test", "structure": "ACCRD"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["quality"]["available"] is False
    assert payload["quality"]["score"] is None
    assert payload["trends"]["available"] is False
    assert payload["risk"]["assessment_status"] == "NOT_ASSESSED"


def test_valid_zero_series_is_not_misread_as_unavailable():
    response = client.post("/api/analysis/run", json={
        "project_id": "test",
        "structure": "ACCRD",
        "readings": [
            {"instrument_id": "P1", "metric": "pressure", "value": 0, "timestamp": "2026-01-01T00:00:00Z", "unit": "MPa"},
            {"instrument_id": "P1", "metric": "pressure", "value": 0, "timestamp": "2026-01-02T00:00:00Z", "unit": "MPa"},
        ],
    })
    assert response.status_code == 200
    payload = response.json()
    assert payload["quality"]["score"] == 100
    assert payload["trends"]["series"][0]["score"] == 0
    assert payload["trends"]["series"][0]["available"] is True
    assert payload["risk"]["assessment_status"] == "ASSESSED"


def test_unified_pipeline_generates_member5_correlation_evidence():
    readings = []
    for day in range(1, 7):
        stamp = f"2026-01-{day:02d}T00:00:00Z"
        readings.extend([
            {"instrument_id": "P1", "metric": "pressure", "value": day, "timestamp": stamp, "unit": "MPa"},
            {"instrument_id": "S1", "metric": "seepage", "value": day * 2, "timestamp": stamp, "unit": "L/min"},
        ])
    response = client.post("/api/analysis/run", json={"project_id": "corr", "structure": "ACCRD", "readings": readings})
    assert response.status_code == 200, response.text
    payload = response.json()
    assert any(item["correlation_detected"] for item in payload["correlations"])
    factor = next(item for item in payload["risk"]["contributing_factors"] if item["key"] == "correlation")
    assert factor["score"] >= 50
