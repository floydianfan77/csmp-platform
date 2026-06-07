"""Read core_traffic_signals from DuckDB (latest window per intersection)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import duckdb

from csmp_monitor.schemas import GeoPoint, HealthResponse, IntersectionStatus

LATEST_PER_INTERSECTION_SQL = """
WITH ranked AS (
    SELECT
        intersection_id,
        display_name,
        signal_state,
        avg_stop_duration_seconds,
        avg_vehicle_speed_kmh,
        is_severe_bottleneck,
        window_end,
        latitude,
        longitude,
        ROW_NUMBER() OVER (
            PARTITION BY intersection_id
            ORDER BY window_end DESC
        ) AS _rn
    FROM core_traffic_signals
)
SELECT
    intersection_id,
    display_name,
    signal_state,
    avg_stop_duration_seconds,
    avg_vehicle_speed_kmh,
    is_severe_bottleneck,
    window_end,
    latitude,
    longitude
FROM ranked
WHERE _rn = 1
ORDER BY intersection_id
"""


class MonitorRepository:
    def __init__(self, connection: duckdb.DuckDBPyConnection) -> None:
        self._con = connection

    @classmethod
    def from_duckdb_file(cls, path: str | Path) -> MonitorRepository:
        return cls(duckdb.connect(str(path), read_only=True))

    @classmethod
    def from_connection(cls, connection: duckdb.DuckDBPyConnection) -> MonitorRepository:
        return cls(connection)

    def _row_to_status(self, row: tuple) -> IntersectionStatus:
        (
            intersection_id,
            display_name,
            signal_state,
            avg_stop,
            avg_speed,
            is_bottleneck,
            window_end,
            latitude,
            longitude,
        ) = row
        location = None
        if latitude is not None and longitude is not None:
            location = GeoPoint(latitude=float(latitude), longitude=float(longitude))
        window_str = window_end
        if isinstance(window_end, datetime):
            window_str = window_end.replace(tzinfo=UTC).isoformat().replace("+00:00", "Z")
        return IntersectionStatus(
            intersection_id=intersection_id,
            display_name=display_name,
            signal_state=signal_state,
            avg_stop_duration_seconds=avg_stop,
            avg_vehicle_speed_kmh=avg_speed,
            is_severe_bottleneck=bool(is_bottleneck),
            window_end=str(window_str),
            location=location,
        )

    def list_latest(self, *, bottleneck_only: bool = False) -> list[IntersectionStatus]:
        rows = self._con.execute(LATEST_PER_INTERSECTION_SQL).fetchall()
        items = [self._row_to_status(row) for row in rows]
        if bottleneck_only:
            items = [item for item in items if item.is_severe_bottleneck]
        return items

    def get_latest(self, intersection_id: str) -> IntersectionStatus | None:
        for item in self.list_latest():
            if item.intersection_id == intersection_id:
                return item
        return None

    def health(self, *, threshold_seconds: float = 120.0) -> HealthResponse:
        count = self._con.execute("SELECT COUNT(*) FROM core_traffic_signals").fetchone()[0]
        if count == 0:
            return HealthResponse(
                status="degraded",
                freshness_status="UNKNOWN",
                max_lag_seconds=0.0,
                intersection_count=0,
            )

        max_window = self._con.execute("SELECT MAX(window_end) FROM core_traffic_signals").fetchone()[0]
        if max_window is None:
            return HealthResponse(
                status="degraded",
                freshness_status="UNKNOWN",
                max_lag_seconds=0.0,
                intersection_count=0,
            )

        if isinstance(max_window, str):
            max_dt = datetime.fromisoformat(max_window.replace("Z", "+00:00"))
        else:
            max_dt = max_window
        if max_dt.tzinfo is None:
            max_dt = max_dt.replace(tzinfo=UTC)

        lag = max(0.0, (datetime.now(tz=UTC) - max_dt).total_seconds())
        fresh = lag <= threshold_seconds
        return HealthResponse(
            status="ok" if fresh else "degraded",
            freshness_status="FRESH" if fresh else "STALE",
            max_lag_seconds=lag,
            intersection_count=len(self.list_latest()),
        )
