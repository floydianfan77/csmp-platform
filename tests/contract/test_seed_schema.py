"""FR-005: Intersection seed contract."""

from __future__ import annotations

import csv

import pytest
from jsonschema import Draft202012Validator

from tests.contract.conftest import SEED_CSV_PATH, SEED_SCHEMA_PATH, load_json


@pytest.fixture
def seed_validator() -> Draft202012Validator:
    return Draft202012Validator(load_json(SEED_SCHEMA_PATH))


def test_seed_schema_is_valid():
    Draft202012Validator.check_schema(load_json(SEED_SCHEMA_PATH))


def test_seed_csv_exists():
    assert SEED_CSV_PATH.is_file(), f"Missing seed file: {SEED_CSV_PATH}"


def test_seed_csv_rows_validate(seed_validator: Draft202012Validator):
    with SEED_CSV_PATH.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) >= 3, "Need at least 3 fallback intersections for local dev"
    for row in rows:
        payload = {
            "intersection_id": row["intersection_id"],
            "display_name": row["display_name"],
            "latitude": float(row["latitude"]),
            "longitude": float(row["longitude"]),
            "source": row["source"],
        }
        if row.get("osm_node_id"):
            payload["osm_node_id"] = int(row["osm_node_id"])
        seed_validator.validate(payload)


def test_seed_coordinates_in_chapeco_bbox(seed_validator: Draft202012Validator):
    """Rough bounding box for Chapecó, SC (~27.05–27.15 S, 52.55–52.70 W)."""
    lat_min, lat_max = -27.15, -27.05
    lon_min, lon_max = -52.70, -52.55
    with SEED_CSV_PATH.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            lat = float(row["latitude"])
            lon = float(row["longitude"])
            assert lat_min <= lat <= lat_max, row["intersection_id"]
            assert lon_min <= lon <= lon_max, row["intersection_id"]
