"""Shared fixtures for monitor API / UI acceptance tests."""

from __future__ import annotations

import csv
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from csmp_monitor.app import create_app
from csmp_monitor.repository import MonitorRepository
from local.engine import run_pipeline
from local.fixtures import write_landing_rows

ROOT = Path(__file__).resolve().parents[2]
SEED_CSV = ROOT / "services" / "dbt" / "seeds" / "chapeco_intersection_locations.csv"


def _load_seed_ids(limit: int = 4) -> list[str]:
    with SEED_CSV.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) < limit:
        raise RuntimeError(f"Need at least {limit} rows in {SEED_CSV}")
    return [row["intersection_id"] for row in rows[:limit]]


SEED_IDS = _load_seed_ids(4)


def recent_window_end(seconds_ago: float = 30.0) -> str:
    ts = datetime.now(tz=UTC) - timedelta(seconds=seconds_ago)
    return ts.strftime("%Y-%m-%dT%H:%M:%SZ")


def landing_row(
    intersection_id: str,
    *,
    stop: float,
    speed: float,
    state: str = "GREEN",
    window_end: str | None = None,
) -> dict:
    return {
        "intersection_id": intersection_id,
        "window_end": window_end or recent_window_end(),
        "signal_state": state,
        "avg_stop_duration_seconds": stop,
        "avg_vehicle_speed_kmh": speed,
        "event_count": 1,
        "ingested_at": datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


@pytest.fixture
def monitor_client(tmp_path):
    landing_db = tmp_path / "landing.db"
    rows = [
        landing_row(SEED_IDS[0], stop=22.0, speed=28.5, state="GREEN"),
        landing_row(SEED_IDS[1], stop=80.0, speed=3.0, state="RED"),
        landing_row(SEED_IDS[2], stop=35.0, speed=15.0, state="YELLOW"),
        landing_row(SEED_IDS[3], stop=10.0, speed=40.0, state="GREEN"),
    ]
    write_landing_rows(landing_db, rows)
    con = run_pipeline(landing_db=landing_db, seed_csv=SEED_CSV)
    repo = MonitorRepository.from_connection(con)
    app = create_app(repository=repo)
    with TestClient(app) as client:
        yield client, repo
