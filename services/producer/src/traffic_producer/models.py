"""Pydantic model aligned with specs/contracts/events/chapeco-traffic-event.v1.schema.json."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class SignalState(str, Enum):
    GREEN = "GREEN"
    RED = "RED"
    YELLOW = "YELLOW"
    FLASHING_YELLOW = "FLASHING_YELLOW"
    UNKNOWN = "UNKNOWN"


class EventSource(str, Enum):
    SIMULATOR = "simulator"
    MUNICIPAL_FEED = "municipal_feed"
    OSM_PROBE = "osm_probe"


class Environment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    timestamp: datetime
    source: EventSource


class Telemetry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_signal_state: SignalState
    avg_stop_duration_seconds: float = Field(ge=0)
    avg_vehicle_speed_kmh: float = Field(ge=0)


class ChapecoTrafficEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: UUID
    intersection_id: str = Field(pattern=r"^[A-Za-z0-9_-]+$")
    environment: Environment
    telemetry: Telemetry
    metadata: dict | None = None

    @classmethod
    def new_simulator_event(
        cls,
        *,
        intersection_id: str,
        signal_state: SignalState,
        avg_stop_duration_seconds: float,
        avg_vehicle_speed_kmh: float,
        timestamp: datetime | None = None,
    ) -> ChapecoTrafficEvent:
        return cls(
            event_id=uuid4(),
            intersection_id=intersection_id,
            environment=Environment(
                timestamp=(timestamp or datetime.now(tz=UTC)),
                source=EventSource.SIMULATOR,
            ),
            telemetry=Telemetry(
                current_signal_state=signal_state,
                avg_stop_duration_seconds=avg_stop_duration_seconds,
                avg_vehicle_speed_kmh=avg_vehicle_speed_kmh,
            ),
        )
