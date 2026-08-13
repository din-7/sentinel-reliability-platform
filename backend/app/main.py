"""Application entry point for the Sentinel backend."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import create_database_engine, create_session_factory
from app.db_models import Base
from app.routes import create_api_router
from app.store import SQLAlchemyTelemetryRepository, TelemetryRepository


def create_app(repository: TelemetryRepository | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = None
        if repository is None:
            engine = create_database_engine()
            Base.metadata.create_all(engine)
            app.state.telemetry_repository = SQLAlchemyTelemetryRepository(
                create_session_factory(engine)
            )
        else:
            app.state.telemetry_repository = repository

        yield

        if engine is not None:
            engine.dispose()

    app = FastAPI(title="Sentinel Backend", lifespan=lifespan)
    app.include_router(create_api_router())

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"service": "sentinel-backend", "status": "healthy"}

    return app


app = create_app()
