import pytest
from fastapi.testclient import TestClient

from api.main import app

TEST_API_KEY = "test-key"
AUTH_HEADERS = {"X-API-Key": TEST_API_KEY}

SAMPLE_FLIGHT = {
    "Time": 1296,
    "Length": 141,
    "Airline": "DL",
    "AirportFrom": "ATL",
    "AirportTo": "HOU",
    "DayOfWeek": 1,
}


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setenv("ML_API_KEY", TEST_API_KEY)
    with TestClient(app) as c:
        yield c


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["model_loaded"] is True


def test_model_info(client):
    resp = client.get("/model/info", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert "model_name" in body
    assert "test_metrics" in body


def test_model_info_requires_api_key(client):
    resp = client.get("/model/info")
    assert resp.status_code == 401


def test_predict_valid_payload(client):
    resp = client.post("/predict", json=SAMPLE_FLIGHT, headers=AUTH_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert body["predicted_class"] in (0, 1)
    assert body["predicted_label"] in ("On-time", "Delayed")
    assert 0.0 <= body["probability_delayed"] <= 1.0


def test_predict_invalid_payload_returns_422(client):
    bad_payload = dict(SAMPLE_FLIGHT)
    bad_payload["DayOfWeek"] = 9  # out of range 1-7
    resp = client.post("/predict", json=bad_payload, headers=AUTH_HEADERS)
    assert resp.status_code == 422


def test_predict_batch(client):
    resp = client.post(
        "/predict/batch",
        json={"records": [SAMPLE_FLIGHT, SAMPLE_FLIGHT]},
        headers=AUTH_HEADERS,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["predictions"]) == 2
