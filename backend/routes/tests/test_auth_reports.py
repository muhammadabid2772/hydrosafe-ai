import uuid

from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def create_user():
    email = f"tester-{uuid.uuid4().hex[:10]}@example.com"
    response = client.post("/api/auth/signup", json={"name": "Test Operator", "email": email, "password": "InitialSafe1"})
    assert response.status_code == 200, response.text
    return email, response.json()["access_token"]


def test_real_auth_profile_and_password_flow():
    email, token = create_user()
    headers = {"Authorization": f"Bearer {token}"}
    assert client.get("/api/auth/me", headers=headers).json()["email"] == email
    profile = client.put("/api/settings/profile", headers=headers, json={"name": "Updated Operator"})
    assert profile.status_code == 200
    assert profile.json()["user"]["name"] == "Updated Operator"
    changed = client.put("/api/settings/password", headers=headers, json={"current_password": "InitialSafe1", "new_password": "ChangedSafe2"})
    assert changed.status_code == 200
    login = client.post("/api/auth/login", json={"email": email, "password": "ChangedSafe2"})
    assert login.status_code == 200


def test_report_generation_persists_grounded_fallback(monkeypatch):
    _, token = create_user()
    headers = {"Authorization": f"Bearer {token}"}
    analysis = client.get("/api/analysis/latest?project_id=report-test").json()
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    generated = client.post("/api/reports/generate", headers=headers, json={"analysis": analysis})
    assert generated.status_code == 200, generated.text
    payload = generated.json()
    assert payload["provider_status"] == "DETERMINISTIC_FALLBACK"
    assert "ENGINEERING MONITORING REPORT" in payload["content"]
    history = client.get("/api/reports", headers=headers)
    assert history.status_code == 200
    assert any(item["report_id"] == payload["report_id"] for item in history.json())
