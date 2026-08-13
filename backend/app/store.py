"""In-memory telemetry storage."""

from collections import deque
from threading import Lock

from app.models import TelemetryEvent


class TelemetryStore:
    def __init__(self, capacity: int = 1_000) -> None:
        self._events: deque[TelemetryEvent] = deque(maxlen=capacity)
        self._lock = Lock()

    def add(self, event: TelemetryEvent) -> TelemetryEvent:
        with self._lock:
            self._events.append(event)
        return event

    def recent(self, limit: int) -> list[TelemetryEvent]:
        with self._lock:
            return list(reversed(self._events))[:limit]
