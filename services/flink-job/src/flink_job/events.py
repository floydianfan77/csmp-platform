"""In-memory event for window aggregation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class TrafficEvent:
    intersection_id: str
    event_timestamp: datetime
    signal_state: str
    avg_stop_duration_seconds: float
    avg_vehicle_speed_kmh: float


def window_end_for(ts: datetime) -> datetime:
    """Exclusive end of 1-minute tumbling bucket (UTC, naive or aware)."""
    floored = ts.replace(second=0, microsecond=0)
    minute = floored.minute + 1
    hour = floored.hour
    if minute >= 60:
        minute = 0
        hour += 1
    return floored.replace(minute=minute % 60, hour=hour % 24)  # simplified
