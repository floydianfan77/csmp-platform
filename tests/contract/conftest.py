"""Shared fixtures for CSMP contract tests (Phase 1)."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SPECS = ROOT / "specs" / "contracts"

EVENT_SCHEMA_PATH = SPECS / "events" / "chapeco-traffic-event.v1.schema.json"
SEED_SCHEMA_PATH = SPECS / "seeds" / "chapeco_intersection_locations.v1.schema.json"
WAREHOUSE_CONTRACT_PATH = SPECS / "warehouse" / "traffic_signals_aggregated_stream.yml"
DBT_SOURCES_PATH = ROOT / "services" / "dbt" / "models" / "staging" / "_sources.yml"
OPENAPI_PATH = SPECS / "api" / "monitor.v1.openapi.yaml"
SEED_CSV_PATH = ROOT / "services" / "dbt" / "seeds" / "chapeco_intersection_locations.csv"

# Flink INSERT / landing DDL column order (FR-002)
LANDING_COLUMN_ORDER = [
    "intersection_id",
    "window_end",
    "signal_state",
    "avg_stop_duration_seconds",
    "avg_vehicle_speed_kmh",
    "event_count",
    "ingested_at",
]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))
