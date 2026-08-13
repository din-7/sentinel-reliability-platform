import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.store import TelemetryStore


@pytest.fixture
def client():
    return TestClient(create_app(TelemetryStore()))


@pytest.fixture
def valid_event():
    return {
        "service": "payment-service",
        "timestamp": "2026-08-13T18:42:20Z",
        "request_count": 120,
        "error_count": 3,
        "average_latency_ms": 183.4,
        "fault_mode": "NORMAL",
    }


def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "service": "sentinel-backend",
        "status": "healthy",
    }


def test_receive_and_list_telemetry(client, valid_event):
    created = client.post("/api/v1/telemetry", json=valid_event)

    assert created.status_code == 201
    assert created.json()["service"] == "payment-service"
    assert client.get("/api/v1/telemetry").json() == [created.json()]


def test_recent_telemetry_respects_limit(client, valid_event):
    client.post("/api/v1/telemetry", json=valid_event)
    second = {**valid_event, "service": "checkout-service"}
    client.post("/api/v1/telemetry", json=second)

    response = client.get("/api/v1/telemetry", params={"limit": 1})

    assert response.status_code == 200
    assert [event["service"] for event in response.json()] == ["checkout-service"]


def test_recent_telemetry_preserves_service_fault_mode_pairs(client, valid_event):
    expected = [
        ("checkout-service", "HIGH_LATENCY"),
        ("payment-service", "NORMAL"),
        ("inventory-service", "OFFLINE"),
    ]
    for service, fault_mode in expected:
        response = client.post(
            "/api/v1/telemetry",
            json={**valid_event, "service": service, "fault_mode": fault_mode},
        )
        assert response.status_code == 201
        assert (response.json()["service"], response.json()["fault_mode"]) == (
            service,
            fault_mode,
        )

    events = client.get("/api/v1/telemetry").json()

    assert [(event["service"], event["fault_mode"]) for event in events] == list(
        reversed(expected)
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"service": ""},
        {"timestamp": "2026-08-13T18:42:20"},
        {"request_count": -1},
        {"error_count": -1},
        {"average_latency_ms": -0.1},
        {"fault_mode": "UNKNOWN"},
        {"request_count": 2, "error_count": 3},
        {"unexpected": "field"},
    ],
)
def test_malformed_telemetry_is_rejected(client, valid_event, changes):
    response = client.post("/api/v1/telemetry", json={**valid_event, **changes})

    assert response.status_code == 422


def test_missing_required_field_is_rejected(client, valid_event):
    valid_event.pop("service")

    response = client.post("/api/v1/telemetry", json=valid_event)

    assert response.status_code == 422
