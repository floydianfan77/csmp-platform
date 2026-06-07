"""AT-002 — events → landing table (SQLite)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from flink_job.landing import LANDING_COLUMN_ORDER, fetch_rows
from flink_job.pipeline import write_kafka_payloads_to_landing

pytestmark = pytest.mark.integration


@pytest.fixture
def landing_db(tmp_path):
    return str(tmp_path / "landing.db")


def _event(intersection_id: str, minute: int, second: int, state: str) -> dict:
    ts = datetime(2026, 6, 7, 18, minute, second, tzinfo=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "event_id": f"550e8400-e29b-41d4-a716-4466{minute:02d}{second:02d}",
        "intersection_id": intersection_id,
        "environment": {"timestamp": ts, "source": "simulator"},
        "telemetry": {
            "current_signal_state": state,
            "avg_stop_duration_seconds": 10.0,
            "avg_vehicle_speed_kmh": 20.0,
        },
    }


def test_events_landing_two_windows_and_last_state(landing_db):
    events = [
        _event("osm-test-1", 0, 0, "RED"),
        _event("osm-test-1", 0, 30, "GREEN"),
        _event("osm-test-1", 0, 50, "RED"),
        _event("osm-test-1", 1, 5, "YELLOW"),
    ]

    row_count = write_kafka_payloads_to_landing(events, landing_db)
    assert row_count == 2

    rows = fetch_rows(landing_db, "osm-test-1")
    assert len(rows) == 2
    assert tuple(rows[0].keys()) == LANDING_COLUMN_ORDER
    minute_zero = next(r for r in rows if "18:01:00" in r["window_end"])
    assert minute_zero["signal_state"] == "RED"
    assert minute_zero["event_count"] == 3
