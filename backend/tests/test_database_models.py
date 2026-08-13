from sqlalchemy import create_mock_engine
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable

from app.db_models import Base, Service, TelemetryEventRecord


def test_database_schema_compiles_for_postgresql():
    statements = []
    engine = create_mock_engine(
        "postgresql+psycopg://",
        lambda sql, *args, **kwargs: statements.append(str(sql)),
    )

    Base.metadata.create_all(engine)

    assert {Service.__tablename__, TelemetryEventRecord.__tablename__} == {
        "services",
        "telemetry_events",
    }
    assert statements


def test_service_name_is_unique_and_telemetry_has_expected_indexes():
    service_ddl = str(
        CreateTable(Service.__table__).compile(dialect=postgresql.dialect())
    )
    index_names = {index.name for index in TelemetryEventRecord.__table__.indexes}

    assert "UNIQUE (name)" in service_ddl
    assert index_names == {
        "ix_telemetry_created_at_desc",
        "ix_telemetry_service_timestamp_desc",
    }
