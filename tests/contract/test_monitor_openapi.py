"""FR-003: Monitor API OpenAPI contract against stub responses."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from openapi_spec_validator import validate

from tests.contract.conftest import OPENAPI_PATH, load_yaml
from tests.contract.openapi_helpers import assert_valid, load_openapi_spec, validator_for_schema
from tests.contract.stub_monitor_api import app


@pytest.fixture
def openapi_spec():
    return load_openapi_spec(OPENAPI_PATH)


@pytest.fixture
def client():
    return TestClient(app)


def test_openapi_document_is_valid(openapi_spec):
    validate(openapi_spec)


def test_openapi_matches_repo_file(openapi_spec):
    assert openapi_spec["info"]["title"] == "CSMP Monitor API"
    assert openapi_spec["openapi"] == "3.1.0"


def test_health_response_matches_schema(client, openapi_spec):
    response = client.get("/health")
    assert response.status_code == 200
    assert_valid(response.json(), validator_for_schema(openapi_spec, "HealthResponse"))


def test_list_intersections_response_matches_schema(client, openapi_spec):
    response = client.get("/intersections")
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == len(body["items"]) == 3
    item_validator = validator_for_schema(openapi_spec, "IntersectionStatus")
    for item in body["items"]:
        assert_valid(item, item_validator)


def test_bottleneck_filter(client, openapi_spec):
    response = client.get("/intersections", params={"bottleneck_only": True})
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["items"][0]["is_severe_bottleneck"] is True
    assert_valid(body["items"][0], validator_for_schema(openapi_spec, "IntersectionStatus"))


def test_get_intersection_found(client, openapi_spec):
    response = client.get("/intersections/osm-287654321")
    assert response.status_code == 200
    assert_valid(response.json(), validator_for_schema(openapi_spec, "IntersectionStatus"))


def test_get_intersection_not_found(client, openapi_spec):
    response = client.get("/intersections/nonexistent-id")
    assert response.status_code == 404
    assert_valid(response.json(), validator_for_schema(openapi_spec, "Error"))
