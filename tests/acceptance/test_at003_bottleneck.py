"""AT-003 — bottleneck detection (FR-004)."""

from __future__ import annotations

from pathlib import Path

import pytest

from local.engine import is_severe_bottleneck, run_pipeline
from local.fixtures import write_landing_rows

ROOT = Path(__file__).resolve().parents[2]
SEED_CSV = ROOT / "services" / "dbt" / "seeds" / "chapeco_intersection_locations.csv"


def _sample_id() -> str:
    import csv

    with SEED_CSV.open(encoding="utf-8", newline="") as handle:
        row = next(csv.DictReader(handle))
    return row["intersection_id"]


@pytest.fixture
def warehouse(tmp_path):
    landing_db = tmp_path / "landing.db"
    return landing_db, SEED_CSV


def _row(intersection_id: str, stop: float, speed: float) -> dict:
    return {
        "intersection_id": intersection_id,
        "window_end": "2026-06-07T18:01:00Z",
        "signal_state": "RED",
        "avg_stop_duration_seconds": stop,
        "avg_vehicle_speed_kmh": speed,
        "event_count": 1,
        "ingested_at": "2026-06-07T18:01:05Z",
    }


def _flag(warehouse, stop: float, speed: float) -> bool:
    landing_db, seed_csv = warehouse
    sample_id = _sample_id()
    write_landing_rows(landing_db, [_row(sample_id, stop, speed)])
    con = run_pipeline(landing_db=landing_db, seed_csv=seed_csv)
    return bool(
        con.execute(
            f"""
            SELECT is_severe_bottleneck
            FROM core_traffic_signals
            WHERE intersection_id = '{sample_id}'
            """
        ).fetchone()[0]
    )


def test_is_severe_bottleneck_helper():
    assert is_severe_bottleneck(80.0, 3.0) is True
    assert is_severe_bottleneck(90.0, 15.0) is False
    assert is_severe_bottleneck(30.0, 2.0) is False
    assert is_severe_bottleneck(75.0, 5.0) is False


def test_at003_severe_bottleneck_flagged(warehouse):
    assert _flag(warehouse, 80.0, 3.0) is True


def test_at003_high_stop_alone_not_severe(warehouse):
    assert _flag(warehouse, 90.0, 15.0) is False


def test_at003_low_speed_alone_not_severe(warehouse):
    assert _flag(warehouse, 30.0, 2.0) is False


def test_at003_boundary_values_not_severe(warehouse):
    assert _flag(warehouse, 75.0, 5.0) is False
