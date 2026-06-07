"""AT-002 window aggregation tests (pure Python — mirrors PyFlink MAX_BY SQL)."""

from __future__ import annotations

from datetime import datetime

import pytest

from flink_job.events import TrafficEvent
from flink_job.landing import LANDING_COLUMN_ORDER
from flink_job.window_state import aggregate_events


def _ts(minute: int, second: int = 0) -> datetime:
    return datetime(2026, 6, 7, 18, minute, second)


def test_two_windows_produce_two_rows():
    events = [
        TrafficEvent("osm-test-1", _ts(0, 10), "RED", 10.0, 20.0),
        TrafficEvent("osm-test-1", _ts(0, 40), "GREEN", 12.0, 18.0),
        TrafficEvent("osm-test-1", _ts(1, 10), "YELLOW", 8.0, 25.0),
    ]
    rows = aggregate_events(events)
    assert len(rows) == 2
    assert all(r["intersection_id"] == "osm-test-1" for r in rows)
    assert all(r["event_count"] >= 1 for r in rows)
    ends = {r["window_end"].isoformat() for r in rows}
    assert len(ends) == 2


def test_last_signal_state_by_timestamp_not_max_lex():
    events = [
        TrafficEvent("osm-test-1", _ts(0, 0), "RED", 10.0, 20.0),
        TrafficEvent("osm-test-1", _ts(0, 30), "GREEN", 10.0, 20.0),
        TrafficEvent("osm-test-1", _ts(0, 50), "RED", 10.0, 20.0),
    ]
    rows = aggregate_events(events)
    assert len(rows) == 1
    assert rows[0]["signal_state"] == "RED"


def test_landing_column_mapping_order():
    assert LANDING_COLUMN_ORDER == (
        "intersection_id",
        "window_end",
        "signal_state",
        "avg_stop_duration_seconds",
        "avg_vehicle_speed_kmh",
        "event_count",
        "ingested_at",
    )


@pytest.mark.flink
def test_pyflink_batch_matches_python():
    pytest.importorskip("pyflink")
    from flink_job.batch_aggregate import aggregate_events as flink_aggregate

    tuples = [
        ("osm-test-1", _ts(0, 0), "RED", 10.0, 20.0),
        ("osm-test-1", _ts(0, 30), "GREEN", 30.0, 40.0),
        ("osm-test-2", _ts(0, 15), "YELLOW", 5.0, 15.0),
    ]
    py_rows = aggregate_events(
        [TrafficEvent(row[0], row[1], row[2], row[3], row[4]) for row in tuples]
    )
    flink_rows = flink_aggregate(tuples)
    assert len(flink_rows) == len(py_rows)
