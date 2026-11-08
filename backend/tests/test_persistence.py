"""Deterministic tests for the sensor persistence service."""

from datetime import datetime, timezone

import pytest

from app.models.postgres_models import SensorDataORM
from app.schemas.sensor import SensorDataInput
from app.services.sensor_service import SensorService


class _Result:
    """Minimal SQLAlchemy-result substitute for service tests."""

    def __init__(self, rows: list[SensorDataORM]) -> None:
        self._rows = rows

    def scalars(self) -> "_Result":
        """Return this result for chained scalar access."""
        return self

    def all(self) -> list[SensorDataORM]:
        """Return the rows supplied by the fake session."""
        return self._rows


class _Session:
    """Small session double that records inserts and serves reads."""

    def __init__(self) -> None:
        self.rows: list[SensorDataORM] = []

    def add(self, row: SensorDataORM) -> None:
        """Record a row added by the service."""
        self.rows.append(row)

    async def commit(self) -> None:
        """Match the async session commit interface."""

    async def refresh(self, row: SensorDataORM) -> None:
        """Assign the database-generated id used by the response."""
        row.id = len(self.rows)

    async def execute(self, _statement: object) -> _Result:
        """Return recorded rows for service query assertions."""
        return _Result(self.rows)


@pytest.mark.asyncio
async def test_sensor_reading_is_stored_and_queryable() -> None:
    """Store one reading and verify the same data is returned by a query."""
    session = _Session()
    service = SensorService(session)  # type: ignore[arg-type]
    timestamp = datetime.now(timezone.utc)
    payload = SensorDataInput(
        user_id="USER_00001",
        heart_rate=82,
        spo2=98.0,
        heart_rate_variability=55,
        timestamp=timestamp,
    )

    stored = await service.store_reading(payload)
    readings = await service.get_user_readings("USER_00001")

    assert stored["id"] == 1
    assert stored["stored"] is True
    assert len(readings) == 1
    assert readings[0]["user_id"] == "USER_00001"
    assert readings[0]["heart_rate"] == 82
    assert readings[0]["spo2"] == 98.0
    assert readings[0]["timestamp"] == timestamp
