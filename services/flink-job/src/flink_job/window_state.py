"""Pure-Python window aggregation — mirrors PyFlink SQL (MAX_BY, not MAX)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from itertools import groupby

from flink_job.events import TrafficEvent


def window_end_for(ts: datetime) -> datetime:
    bucket_start = ts.replace(second=0, microsecond=0)
    return bucket_start + timedelta(minutes=1)


def aggregate_events(events: list[TrafficEvent]) -> list[dict]:
    """Aggregate all events into 1-minute tumbling windows."""
    if not events:
        return []

    sorted_events = sorted(events, key=lambda e: (e.intersection_id, e.event_timestamp))
    rows: list[dict] = []

    for intersection_id, group in groupby(sorted_events, key=lambda e: e.intersection_id):
        bucket: dict[datetime, list[TrafficEvent]] = {}
        for event in group:
            end = window_end_for(event.event_timestamp)
            bucket.setdefault(end, []).append(event)

        for end, bucket_events in sorted(bucket.items()):
            last = max(bucket_events, key=lambda e: e.event_timestamp)
            rows.append(
                {
                    "intersection_id": intersection_id,
                    "window_end": end,
                    "signal_state": last.signal_state,
                    "avg_stop_duration_seconds": sum(e.avg_stop_duration_seconds for e in bucket_events)
                    / len(bucket_events),
                    "avg_vehicle_speed_kmh": sum(e.avg_vehicle_speed_kmh for e in bucket_events)
                    / len(bucket_events),
                    "event_count": len(bucket_events),
                }
            )

    return rows


def parse_kafka_json(payload: dict) -> TrafficEvent:
    ts_raw = payload["environment"]["timestamp"]
    ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
    if ts.tzinfo is not None:
        ts = ts.astimezone(UTC).replace(tzinfo=None)
    return TrafficEvent(
        intersection_id=payload["intersection_id"],
        event_timestamp=ts,
        signal_state=payload["telemetry"]["current_signal_state"],
        avg_stop_duration_seconds=float(payload["telemetry"]["avg_stop_duration_seconds"]),
        avg_vehicle_speed_kmh=float(payload["telemetry"]["avg_vehicle_speed_kmh"]),
    )


def rows_to_landing(rows: list[dict], ingested_at: datetime | None = None) -> list[dict]:
    ingested = (ingested_at or datetime.now(tz=UTC)).replace(tzinfo=None).isoformat(timespec="seconds")
    landing: list[dict] = []
    for row in rows:
        landing.append(
            {
                "intersection_id": row["intersection_id"],
                "window_end": row["window_end"].isoformat(timespec="seconds"),
                "signal_state": row["signal_state"],
                "avg_stop_duration_seconds": row["avg_stop_duration_seconds"],
                "avg_vehicle_speed_kmh": row["avg_vehicle_speed_kmh"],
                "event_count": row["event_count"],
                "ingested_at": ingested,
            }
        )
    return landing
