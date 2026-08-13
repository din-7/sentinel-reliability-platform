"""SQLAlchemy models for persisted Sentinel telemetry."""

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    telemetry_events: Mapped[list["TelemetryEventRecord"]] = relationship(
        back_populates="service", cascade="all, delete-orphan"
    )


class TelemetryEventRecord(Base):
    __tablename__ = "telemetry_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    service_id: Mapped[int] = mapped_column(
        ForeignKey("services.id", ondelete="CASCADE"), nullable=False
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    request_count: Mapped[int] = mapped_column(Integer, nullable=False)
    error_count: Mapped[int] = mapped_column(Integer, nullable=False)
    average_latency_ms: Mapped[float] = mapped_column(Float, nullable=False)
    fault_mode: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint("request_count >= 0", name="ck_request_count_nonnegative"),
        CheckConstraint("error_count >= 0", name="ck_error_count_nonnegative"),
        CheckConstraint(
            "error_count <= request_count", name="ck_errors_not_above_requests"
        ),
        CheckConstraint(
            "average_latency_ms >= 0", name="ck_average_latency_nonnegative"
        ),
        Index("ix_telemetry_created_at_desc", created_at.desc()),
        Index("ix_telemetry_service_timestamp_desc", service_id, timestamp.desc()),
    )

    service: Mapped[Service] = relationship(back_populates="telemetry_events")
