from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class GeoPoint(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class IntersectionStatus(BaseModel):
    intersection_id: str
    display_name: str | None = None
    signal_state: Literal["GREEN", "RED", "YELLOW", "FLASHING_YELLOW", "UNKNOWN"]
    avg_stop_duration_seconds: float | None = None
    avg_vehicle_speed_kmh: float | None = None
    is_severe_bottleneck: bool
    window_end: str
    location: GeoPoint | None = None


class IntersectionListResponse(BaseModel):
    count: int
    items: list[IntersectionStatus]


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    freshness_status: Literal["FRESH", "STALE", "UNKNOWN"]
    max_lag_seconds: float
    intersection_count: int | None = None


class ErrorResponse(BaseModel):
    code: str
    message: str
