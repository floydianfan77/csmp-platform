"""AT-004 — Monitor API (FR-003, NFR-001)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from csmp_monitor.app import create_app
from csmp_monitor.repository import MonitorRepository
from local.engine import run_pipeline
from local.fixtures import write_landing_rows
from tests.contract.openapi_helpers import assert_valid, load_openapi_spec, validator_for_schema
from tests.contract.conftest import OPENAPI_PATH

ROOT = Path(__file__).resolve().parents[2]
SEED_CSV = ROOT / "services" / "dbt" / "seeds" / "chapeco_intersection_locations.csv"

SEED_IDS = [
    "osm-287654321",
    "osm-287654322",
    "osm-287654323",
    "osm-287654324",
]


def _recent_window_end(seconds_ago: float = 30.0) -> str:
    ts = datetime.now(tz=UTC) - timedelta(seconds=seconds_ago)
    return ts.strftime("%Y-%m-%dT%H:%M:%SZ")


def _landing_row(
    intersection_id: str,
    *,
    stop: float,
    speed: float,
    state: str = "GREEN",
    window_end: str | None = None,
) -> dict:
    return {
        "intersection_id": intersection_id,
        "window_end": window_end or _recent_window_end(),
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
        _landing_row(SEED_IDS[0], stop=22.0, speed=28.5, state="GREEN"),
        _landing_row(SEED_IDS[1], stop=80.0, speed=3.0, state="RED"),
        _landing_row(SEED_IDS[2], stop=35.0, speed=15.0, state="YELLOW"),
        _landing_row(SEED_IDS[3], stop=10.0, speed=40.0, state="GREEN"),
    ]
    write_landing_rows(landing_db, rows)
    con = run_pipeline(landing_db=landing_db, seed_csv=SEED_CSV)
    repo = MonitorRepository.from_connection(con)
    app = create_app(repository=repo)
    with TestClient(app) as client:
        yield client, repo


@pytest.fixture
def openapi_spec():
    return load_openapi_spec(OPENAPI_PATH)


def test_at004_health_reports_freshness(monitor_client, openapi_spec):
    client, _repo = monitor_client
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert_valid(body, validator_for_schema(openapi_spec, "HealthResponse"))
    assert body["freshness_status"] == "FRESH"
    assert body["max_lag_seconds"] <= 120


def test_at004_list_intersections(monitor_client, openapi_spec):
    client, _repo = monitor_client
    response = client.get("/intersections")
    assert response.status_code == 200
    body = response.json()
    assert body["count"] >= 3
    item_validator = validator_for_schema(openapi_spec, "IntersectionStatus")
    for item in body["items"]:
        assert_valid(item, item_validator)
        assert "location" in item and item["location"] is not None
        assert "latitude" in item["location"]
        assert "longitude" in item["location"]


def test_at004_filter_bottlenecks_only(monitor_client, openapi_spec):
    client, _repo = monitor_client
    response = client.get("/intersections", params={"bottleneck_only": True})
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["items"][0]["is_severe_bottleneck"] is True
    assert_valid(body["items"][0], validator_for_schema(openapi_spec, "IntersectionStatus"))


def test_at004_unknown_intersection_returns_404(monitor_client, openapi_spec):
    client, _repo = monitor_client
    response = client.get("/intersections/nonexistent-id")
    assert response.status_code == 404
    assert_valid(response.json(), validator_for_schema(openapi_spec, "Error"))
