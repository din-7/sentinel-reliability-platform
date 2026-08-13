from time import perf_counter

import pytest
from fastapi.testclient import TestClient

from app_factory import FaultMode, create_app


@pytest.fixture
def client():
    return TestClient(create_app("test-service"))


def test_switching_fault_modes_is_visible_in_metrics(client):
    for mode in FaultMode:
        response = client.post("/fault", json={"mode": mode.value})

        assert response.status_code == 200
        assert response.json()["fault_mode"] == mode.value
        assert client.get("/metrics").json()["fault_mode"] == mode.value


def test_high_latency_delays_simulated_requests(monkeypatch):
    monkeypatch.setenv("FAULT_LATENCY_MS", "50")
    client = TestClient(create_app("test-service"))
    client.post("/fault", json={"mode": "HIGH_LATENCY"})

    started_at = perf_counter()
    response = client.get("/health")
    elapsed_ms = (perf_counter() - started_at) * 1000

    assert response.status_code == 200
    assert elapsed_ms >= 40
    assert client.get("/metrics").json()["average_latency_ms"] > 0


def test_high_error_rate_returns_500(monkeypatch):
    monkeypatch.setenv("FAULT_ERROR_PROBABILITY", "1.0")
    client = TestClient(create_app("test-service"))
    client.post("/fault", json={"mode": "HIGH_ERROR_RATE"})

    response = client.get("/health")

    assert response.status_code == 500
    assert response.json()["error"] == "injected server error"
    assert client.get("/metrics").json()["error_count"] == 1


def test_offline_health_is_unhealthy_and_requests_fail(client):
    client.post("/fault", json={"mode": "OFFLINE"})

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json() == {"service": "test-service", "status": "unhealthy"}


def test_resetting_to_normal_restores_service(client):
    client.post("/fault", json={"mode": "OFFLINE"})
    assert client.get("/health").status_code == 503

    response = client.post("/fault", json={"mode": "NORMAL"})

    assert response.status_code == 200
    assert response.json()["fault_mode"] == "NORMAL"
    assert client.get("/health").status_code == 200
