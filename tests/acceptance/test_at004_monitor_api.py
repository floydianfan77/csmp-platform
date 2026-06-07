"""AT-004 — Monitor API (FR-003, NFR-001)."""

from __future__ import annotations

import pytest

from tests.contract.openapi_helpers import assert_valid, load_openapi_spec, validator_for_schema
from tests.contract.conftest import OPENAPI_PATH


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
