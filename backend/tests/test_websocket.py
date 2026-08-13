import asyncio

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.models import TelemetryEvent
from app.websocket import TelemetryConnectionManager


class FakeTelemetryRepository:
    def __init__(self):
        self.events = []

    def add(self, event):
        self.events.append(event)
        return event

    def recent(self, limit):
        return list(reversed(self.events))[:limit]


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


def test_stored_telemetry_is_broadcast_to_multiple_clients(valid_event):
    with TestClient(create_app(FakeTelemetryRepository())) as client:
        with client.websocket_connect("/ws/telemetry") as first:
            with client.websocket_connect("/ws/telemetry") as second:
                response = client.post("/api/v1/telemetry", json=valid_event)

                assert response.status_code == 201
                assert first.receive_json() == response.json()
                assert second.receive_json() == response.json()


def test_failed_storage_is_not_broadcast(valid_event):
    class FailingRepository(FakeTelemetryRepository):
        def add(self, event):
            raise RuntimeError("database unavailable")

    app = create_app(FailingRepository())
    broadcasts = []

    async def record_broadcast(event):
        broadcasts.append(event)

    app.state.telemetry_connections.broadcast = record_broadcast
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post("/api/v1/telemetry", json=valid_event)

    assert response.status_code == 500
    assert broadcasts == []


def test_broken_client_does_not_stop_other_clients(valid_event):
    class Socket:
        def __init__(self, broken=False):
            self.broken = broken
            self.messages = []

        async def send_json(self, message):
            if self.broken:
                raise RuntimeError("disconnected")
            self.messages.append(message)

    manager = TelemetryConnectionManager()
    broken = Socket(broken=True)
    healthy = Socket()
    manager._connections.update({broken, healthy})
    event = TelemetryEvent.model_validate(valid_event)

    asyncio.run(manager.broadcast(event))

    assert healthy.messages == [event.model_dump(mode="json")]
    assert broken not in manager._connections
