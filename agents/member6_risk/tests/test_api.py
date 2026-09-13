from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_health_route():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_risk_route_schema():
    response = client.post(
        "/api/risk/assess",
        json={"project_id": "test", "structure": "ACCRD", "quality": {"score": 100}},
    )
    assert response.status_code == 200
    assert response.json()["level"] == "NORMAL"
    assert response.json()["assessment_status"] == "NOT_ASSESSED"


def test_member4_anomaly_route_uses_shared_history():
    response = client.post(
        "/api/anomaly/hydromet/assess",
        json={
            "observed_at": "2026-09-01T08:00:00Z",
            "current": {
                "reservoir_level": 459.04,
                "tailwater": 391.69,
                "inflow": 490,
                "rainfall": 49,
                "temperature": 24.8,
            },
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["source_agent"] == "member4_anomaly"
    assert payload["scope"] == "HYDROMET"
    assert payload["history_quality"]["raw_rows"] == 2800
    assert payload["direct_structural_risk_contribution"] == 0


def test_integrated_member4_high_screen_does_not_create_structural_alarm():
    response = client.post(
        "/api/risk/assess-with-member4",
        json={
            "risk": {
                "project_id": "test",
                "structure": "ACCRD",
                "quality": {"score": 100},
            },
            "observed_at": "2026-09-13T08:00:00Z",
            "current_hydromet": {
                "reservoir_level": 600,
                "tailwater": 450,
                "inflow": 5000,
                "rainfall": 300,
                "temperature": 50,
            },
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["anomaly"]["anomaly"] is True
    assert payload["risk"]["level"] == "NORMAL"
    assert payload["risk"]["score"] == 0
    assert payload["risk"]["assessment_status"] == "NOT_ASSESSED"
    assert payload["risk"]["hydromet_assessment"]["anomaly_detected"] is True


def test_integrated_member4_rejects_negative_rainfall():
    response = client.post(
        "/api/risk/assess-with-member4",
        json={
            "risk": {"project_id": "test", "structure": "ACCRD"},
            "observed_at": "2026-09-13T08:00:00Z",
            "current_hydromet": {
                "reservoir_level": 459,
                "tailwater": 391,
                "inflow": 500,
                "rainfall": -1,
                "temperature": 25,
            },
        },
    )
    assert response.status_code == 422


def test_manual_member4_input_stays_unvalidated_and_not_assessed():
    response = client.post(
        "/api/risk/assess-with-member4",
        json={
            "risk": {"project_id": "test", "structure": "ACCRD"},
            "observed_at": "2026-09-13T08:00:00Z",
            "current_hydromet": {
                "reservoir_level": 459.04,
                "tailwater": 391.69,
                "inflow": 490,
                "rainfall": 49,
                "temperature": 24.8,
            },
        },
    )
    assert response.status_code == 200
    payload = response.json()["risk"]
    assert payload["assessment_status"] == "NOT_ASSESSED"
    assert "not been assessed" in payload["warning_message"]
    quality = next(item for item in payload["contributing_factors"] if item["key"] == "data_quality")
    assert "missing" in quality["evidence"].lower()
