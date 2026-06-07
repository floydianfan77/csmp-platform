"""Read core_traffic_signals from DuckDB (latest window per intersection)."""

from __future__ import annotations

import csv
from datetime import UTC, datetime
from pathlib import Path

import duckdb

from csmp_monitor.config import settings
from csmp_monitor.schemas import GeoPoint, HealthResponse, IntersectionStatus

NO_TELEMETRY_WINDOW = "1970-01-01T00:00:00Z"

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

    def _load_seed_inventory(self) -> list[dict]:
        path = Path(settings.seed_csv_path)
        if not path.is_file():
            return []
        with path.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def _list_core_latest(self) -> list[IntersectionStatus]:
        rows = self._con.execute(LATEST_PER_INTERSECTION_SQL).fetchall()
        return [self._row_to_status(row) for row in rows]

    def _status_from_seed(self, seed_row: dict) -> IntersectionStatus:
        return IntersectionStatus(
            intersection_id=seed_row["intersection_id"],
            display_name=seed_row["display_name"],
            signal_state="UNKNOWN",
            avg_stop_duration_seconds=None,
            avg_vehicle_speed_kmh=None,
            is_severe_bottleneck=False,
            window_end=NO_TELEMETRY_WINDOW,
            location=GeoPoint(
                latitude=float(seed_row["latitude"]),
                longitude=float(seed_row["longitude"]),
            ),
        )

    def list_latest(self, *, bottleneck_only: bool = False) -> list[IntersectionStatus]:
        core_by_id = {item.intersection_id: item for item in self._list_core_latest()}
        seed_rows = self._load_seed_inventory()

        if seed_rows:
            items: list[IntersectionStatus] = []
            for seed_row in seed_rows:
                intersection_id = seed_row["intersection_id"]
                item = core_by_id.get(intersection_id) or self._status_from_seed(seed_row)
                if item.location is None and seed_row.get("latitude") and seed_row.get("longitude"):
                    item = item.model_copy(
                        update={
                            "location": GeoPoint(
                                latitude=float(seed_row["latitude"]),
                                longitude=float(seed_row["longitude"]),
                            )
                        }
                    )
                items.append(item)
        else:
            items = list(core_by_id.values())

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
        inventory = self.list_latest()
        if count == 0:
            return HealthResponse(
                status="degraded",
                freshness_status="UNKNOWN",
                max_lag_seconds=0.0,
                intersection_count=len(inventory),
            )

        max_window = self._con.execute("SELECT MAX(window_end) FROM core_traffic_signals").fetchone()[0]
        if max_window is None:
            return HealthResponse(
                status="degraded",
                freshness_status="UNKNOWN",
                max_lag_seconds=0.0,
                intersection_count=len(inventory),
            )

        if isinstance(max_window, str):
            max_dt = datetime.fromisoformat(max_window.replace("Z", "+00:00"))
        else:
            max_dt = max_window
        if max_dt.tzinfo is None:
            max_dt = max_dt.replace(tzinfo=UTC)

        lag = max(0.0, (datetime.now(tz=UTC) - max_dt).total_seconds())
        fresh = lag <= threshold_seconds
        with_telemetry = sum(1 for item in inventory if item.window_end != NO_TELEMETRY_WINDOW)
        return HealthResponse(
            status="ok" if fresh and with_telemetry > 0 else "degraded",
            freshness_status="FRESH" if fresh and with_telemetry > 0 else "UNKNOWN",
            max_lag_seconds=lag if with_telemetry > 0 else 0.0,
            intersection_count=len(inventory),
        )
