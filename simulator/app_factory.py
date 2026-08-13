"""Shared application setup for Sentinel's simulated services."""

import asyncio
import os
import random
from datetime import datetime, timezone
from enum import Enum
from threading import Lock
from time import perf_counter

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class FaultMode(str, Enum):
    NORMAL = "NORMAL"
    HIGH_LATENCY = "HIGH_LATENCY"
    HIGH_ERROR_RATE = "HIGH_ERROR_RATE"
    OFFLINE = "OFFLINE"


class FaultRequest(BaseModel):
    mode: FaultMode


def create_app(service_name: str) -> FastAPI:
    """Create a small service with health and in-memory metrics endpoints."""
    app = FastAPI(title=service_name)
    lock = Lock()
    request_count = 0
    error_count = 0
    total_latency_ms = 0.0
    fault_mode = FaultMode.NORMAL
    artificial_latency_ms = max(0.0, float(os.getenv("FAULT_LATENCY_MS", "500")))
    error_probability = min(
        1.0, max(0.0, float(os.getenv("FAULT_ERROR_PROBABILITY", "0.5")))
    )

    @app.middleware("http")
    async def record_request_metrics(request: Request, call_next):
        nonlocal request_count, error_count, total_latency_ms
        started_at = perf_counter()
        failed = False

        try:
            with lock:
                current_fault_mode = fault_mode

            fault_exempt = request.url.path in {"/fault", "/metrics"}

            if not fault_exempt and current_fault_mode == FaultMode.HIGH_LATENCY:
                await asyncio.sleep(artificial_latency_ms / 1000)

            if (
                not fault_exempt
                and current_fault_mode == FaultMode.HIGH_ERROR_RATE
                and random.random() < error_probability
            ):
                response = JSONResponse(
                    status_code=500,
                    content={"service": service_name, "error": "injected server error"},
                )
            elif not fault_exempt and current_fault_mode == FaultMode.OFFLINE:
                if request.url.path == "/health":
                    content = {"service": service_name, "status": "unhealthy"}
                else:
                    content = {"service": service_name, "error": "service offline"}
                response = JSONResponse(status_code=503, content=content)
            else:
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

    @app.post("/fault")
    async def set_fault(fault: FaultRequest) -> dict[str, str]:
        nonlocal fault_mode
        with lock:
            fault_mode = fault.mode
        return {"service": service_name, "fault_mode": fault_mode.value}

    @app.get("/metrics")
    async def metrics() -> dict[str, str | int | float]:
        with lock:
            current_request_count = request_count
            current_error_count = error_count
            current_fault_mode = fault_mode
            average_latency_ms = (
                total_latency_ms / request_count if request_count else 0.0
            )

        return {
            "service": service_name,
            "request_count": current_request_count,
            "error_count": current_error_count,
            "average_latency_ms": round(average_latency_ms, 3),
            "fault_mode": current_fault_mode.value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    return app
