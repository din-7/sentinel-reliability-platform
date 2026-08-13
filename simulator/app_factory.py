"""Shared application setup for Sentinel's simulated services."""

from datetime import datetime, timezone
from threading import Lock
from time import perf_counter

from fastapi import FastAPI, Request


def create_app(service_name: str) -> FastAPI:
    """Create a small service with health and in-memory metrics endpoints."""
    app = FastAPI(title=service_name)
    lock = Lock()
    request_count = 0
    error_count = 0
    total_latency_ms = 0.0

    @app.middleware("http")
    async def record_request_metrics(request: Request, call_next):
        nonlocal request_count, error_count, total_latency_ms
        started_at = perf_counter()
        failed = False

        try:
            response = await call_next(request)
            failed = response.status_code >= 400
            return response
        except Exception:
            failed = True
            raise
        finally:
            latency_ms = (perf_counter() - started_at) * 1000
            with lock:
                request_count += 1
                error_count += int(failed)
                total_latency_ms += latency_ms

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"service": service_name, "status": "healthy"}

    @app.get("/metrics")
    async def metrics() -> dict[str, str | int | float]:
        with lock:
            current_request_count = request_count
            current_error_count = error_count
            average_latency_ms = (
                total_latency_ms / request_count if request_count else 0.0
            )

        return {
            "service": service_name,
            "request_count": current_request_count,
            "error_count": current_error_count,
            "average_latency_ms": round(average_latency_ms, 3),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    return app
