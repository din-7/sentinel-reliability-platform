"""HTTP routes for Sentinel telemetry."""

from fastapi import APIRouter, Query, Request, WebSocket, WebSocketDisconnect, status

from app.models import TelemetryEvent
from app.store import TelemetryRepository
from app.websocket import TelemetryConnectionManager


def create_api_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1")

    @router.post(
        "/telemetry",
        response_model=TelemetryEvent,
        status_code=status.HTTP_201_CREATED,
    )
    async def receive_telemetry(
        event: TelemetryEvent, request: Request
    ) -> TelemetryEvent:
        repository: TelemetryRepository = request.app.state.telemetry_repository
        stored_event = repository.add(event)
        manager: TelemetryConnectionManager = request.app.state.telemetry_connections
        await manager.broadcast(stored_event)
        return stored_event

    @router.get("/telemetry", response_model=list[TelemetryEvent])
    async def get_telemetry(
        request: Request,
        limit: int = Query(default=100, ge=1, le=1_000),
    ) -> list[TelemetryEvent]:
        repository: TelemetryRepository = request.app.state.telemetry_repository
        return repository.recent(limit)

    return router


def create_websocket_router() -> APIRouter:
    router = APIRouter()

    @router.websocket("/ws/telemetry")
    async def telemetry_websocket(websocket: WebSocket) -> None:
        manager: TelemetryConnectionManager = (
            websocket.app.state.telemetry_connections
        )
        await manager.connect(websocket)
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            manager.disconnect(websocket)

    return router
