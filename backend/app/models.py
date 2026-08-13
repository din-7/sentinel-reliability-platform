"""API models for telemetry ingestion."""

from enum import Enum

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator


class FaultMode(str, Enum):
    NORMAL = "NORMAL"
    HIGH_LATENCY = "HIGH_LATENCY"
    HIGH_ERROR_RATE = "HIGH_ERROR_RATE"
    OFFLINE = "OFFLINE"


class TelemetryEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    service: str = Field(min_length=1, max_length=100)
    timestamp: AwareDatetime
    request_count: int = Field(ge=0)
    error_count: int = Field(ge=0)
    average_latency_ms: float = Field(ge=0, allow_inf_nan=False)
    fault_mode: FaultMode

    @model_validator(mode="after")
    def errors_cannot_exceed_requests(self):
        if self.error_count > self.request_count:
            raise ValueError("error_count cannot exceed request_count")
        return self
