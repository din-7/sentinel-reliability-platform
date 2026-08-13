"""HTTP routes for Sentinel telemetry."""

from fastapi import APIRouter, Query, Request, status

from app.models import TelemetryEvent
from app.store import TelemetryRepository


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
        return repository.add(event)

    @router.get("/telemetry", response_model=list[TelemetryEvent])
    async def get_telemetry(
        request: Request,
        limit: int = Query(default=100, ge=1, le=1_000),
    ) -> list[TelemetryEvent]:
        repository: TelemetryRepository = request.app.state.telemetry_repository
        return repository.recent(limit)

    return router
