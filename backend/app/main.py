"""Application entry point for the Sentinel backend."""

from fastapi import FastAPI

from app.routes import create_api_router
from app.store import TelemetryStore


def create_app(store: TelemetryStore | None = None) -> FastAPI:
    app = FastAPI(title="Sentinel Backend")
    telemetry_store = store or TelemetryStore()
    app.include_router(create_api_router(telemetry_store))

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"service": "sentinel-backend", "status": "healthy"}

    return app


app = create_app()
