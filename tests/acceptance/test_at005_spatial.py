"""AT-005 — spatial enrichment and orphan reporting (FR-005)."""

from __future__ import annotations

from pathlib import Path

import pytest

from local.engine import run_pipeline
from local.fixtures import write_landing_rows

ROOT = Path(__file__).resolve().parents[2]
SEED_CSV = ROOT / "services" / "dbt" / "seeds" / "chapeco_intersection_locations.csv"

KNOWN_ID = "osm-287654321"
ORPHAN_ID = "unknown-999"


def _landing_row(intersection_id: str) -> dict:
    return {
        "intersection_id": intersection_id,
        "window_end": "2026-06-07T18:01:00Z",
        "signal_state": "GREEN",
        "avg_stop_duration_seconds": 10.0,
        "avg_vehicle_speed_kmh": 30.0,
        "event_count": 2,
        "ingested_at": "2026-06-07T18:01:05Z",
    }


def test_at005_known_intersection_gets_geography(tmp_path):
    landing_db = tmp_path / "landing.db"
    write_landing_rows(landing_db, [_landing_row(KNOWN_ID)])
    con = run_pipeline(landing_db=landing_db, seed_csv=SEED_CSV)

    seed = con.execute(
        f"""
        SELECT latitude, longitude
        FROM chapeco_intersection_locations
        WHERE intersection_id = '{KNOWN_ID}'
        """
    ).fetchone()
    core = con.execute(
        f"""
        SELECT
            spatial_geography_point IS NOT NULL AS has_point,
            ST_X(spatial_geography_point) AS lon,
            ST_Y(spatial_geography_point) AS lat
        FROM core_traffic_signals
        WHERE intersection_id = '{KNOWN_ID}'
        """
    ).fetchone()

    assert core[0] is True
    assert core[1] == pytest.approx(seed[1], abs=1e-6)
    assert core[2] == pytest.approx(seed[0], abs=1e-6)


def test_at005_orphan_intersection_reported(tmp_path):
    landing_db = tmp_path / "landing.db"
    write_landing_rows(landing_db, [_landing_row(ORPHAN_ID)])
    con = run_pipeline(landing_db=landing_db, seed_csv=SEED_CSV)

    orphans = con.execute(
        "SELECT intersection_id FROM rpt_orphan_intersections ORDER BY intersection_id"
    ).fetchall()
    core_count = con.execute(
        f"SELECT COUNT(*) FROM core_traffic_signals WHERE intersection_id = '{ORPHAN_ID}'"
    ).fetchone()[0]

    assert [row[0] for row in orphans] == [ORPHAN_ID]
    assert core_count == 1
