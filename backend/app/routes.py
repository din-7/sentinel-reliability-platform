"""HTTP routes for Sentinel telemetry."""

from fastapi import APIRouter, Query, status

from app.models import TelemetryEvent
from app.store import TelemetryStore


def create_api_router(store: TelemetryStore) -> APIRouter:
    router = APIRouter(prefix="/api/v1")

    @router.post(
        "/telemetry",
        response_model=TelemetryEvent,
        status_code=status.HTTP_201_CREATED,
    )
    async def receive_telemetry(event: TelemetryEvent) -> TelemetryEvent:
        return store.add(event)

    @router.get("/telemetry", response_model=list[TelemetryEvent])
    async def get_telemetry(
        limit: int = Query(default=100, ge=1, le=1_000),
    ) -> list[TelemetryEvent]:
        return store.recent(limit)

    return router
