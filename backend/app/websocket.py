"""WebSocket connection management for live telemetry."""

from fastapi import WebSocket

from app.models import TelemetryEvent


class TelemetryConnectionManager:
    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self._connections.discard(websocket)

    async def broadcast(self, event: TelemetryEvent) -> None:
        message = event.model_dump(mode="json")
        broken_connections: list[WebSocket] = []

        for websocket in tuple(self._connections):
            try:
                await websocket.send_json(message)
            except Exception:
                broken_connections.append(websocket)

        for websocket in broken_connections:
            self.disconnect(websocket)
