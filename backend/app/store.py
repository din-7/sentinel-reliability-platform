"""PostgreSQL repository for telemetry storage."""

from typing import Protocol

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session, joinedload, sessionmaker

from app.db_models import Service, TelemetryEventRecord
from app.models import TelemetryEvent


class TelemetryRepository(Protocol):
    def add(self, event: TelemetryEvent) -> TelemetryEvent: ...

    def recent(self, limit: int) -> list[TelemetryEvent]: ...


class SQLAlchemyTelemetryRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def add(self, event: TelemetryEvent) -> TelemetryEvent:
        with self._session_factory() as session:
            service_id = session.execute(
                insert(Service)
                .values(name=event.service)
                .on_conflict_do_nothing(index_elements=[Service.name])
                .returning(Service.id)
            ).scalar_one_or_none()

            if service_id is None:
                service_id = session.scalar(
                    select(Service.id).where(Service.name == event.service)
                )

            record = TelemetryEventRecord(
                service_id=service_id,
                timestamp=event.timestamp,
                request_count=event.request_count,
                error_count=event.error_count,
                average_latency_ms=event.average_latency_ms,
                fault_mode=event.fault_mode.value,
            )
            session.add(record)
            session.commit()
        return event

    def recent(self, limit: int) -> list[TelemetryEvent]:
        with self._session_factory() as session:
            records = session.scalars(
                select(TelemetryEventRecord)
                .options(joinedload(TelemetryEventRecord.service))
                .order_by(
                    TelemetryEventRecord.created_at.desc(),
                    TelemetryEventRecord.id.desc(),
                )
                .limit(limit)
            ).all()

            return [
                TelemetryEvent(
                    service=record.service.name,
                    timestamp=record.timestamp,
                    request_count=record.request_count,
                    error_count=record.error_count,
                    average_latency_ms=record.average_latency_ms,
                    fault_mode=record.fault_mode,
                )
                for record in records
            ]
