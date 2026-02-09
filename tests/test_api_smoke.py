from app import app


def test_scenarios_endpoint():
    client = app.test_client()
    response = client.get("/api/scenarios")
    assert response.status_code == 200
    payload = response.get_json()
    assert "default" in payload
