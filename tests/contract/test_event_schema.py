"""FR-001: Kafka event contract (chapeco-traffic-event v1)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from tests.contract.conftest import EVENT_SCHEMA_PATH, load_json

FIXTURES = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def event_validator() -> Draft202012Validator:
    schema = load_json(EVENT_SCHEMA_PATH)
    return Draft202012Validator(schema, format_checker=FormatChecker())


def test_schema_file_is_valid_json_schema():
    schema = load_json(EVENT_SCHEMA_PATH)
    Draft202012Validator.check_schema(schema)


def test_example_from_schema_validates(event_validator: Draft202012Validator):
    schema = load_json(EVENT_SCHEMA_PATH)
    example = schema["examples"][0]
    event_validator.validate(example)


def test_fixture_valid_event(event_validator: Draft202012Validator):
    payload = json.loads((FIXTURES / "valid_event.json").read_text(encoding="utf-8"))
    event_validator.validate(payload)


@pytest.mark.parametrize(
    "bad_payload",
    [
        {"intersection_id": "x", "environment": {}, "telemetry": {}},
        {
            "event_id": "not-a-uuid",
            "intersection_id": "osm-1",
            "environment": {"timestamp": "2026-06-05T14:30:00Z", "source": "simulator"},
            "telemetry": {
                "current_signal_state": "RED",
                "avg_stop_duration_seconds": 1,
                "avg_vehicle_speed_kmh": 1,
            },
        },
        {
            "event_id": "550e8400-e29b-41d4-a716-446655440000",
            "intersection_id": "osm-1",
            "environment": {"timestamp": "2026-06-05T14:30:00Z", "source": "simulator"},
            "telemetry": {
                "current_signal_state": "BLUE",
                "avg_stop_duration_seconds": 1,
                "avg_vehicle_speed_kmh": 1,
            },
        },
    ],
)
def test_invalid_events_rejected(event_validator: Draft202012Validator, bad_payload):
    with pytest.raises(Exception):
        event_validator.validate(bad_payload)


def test_fixture_missing_telemetry_rejected(event_validator: Draft202012Validator):
    payload = json.loads(
        (FIXTURES / "invalid_event_missing_telemetry.json").read_text(encoding="utf-8")
    )
    with pytest.raises(Exception):
        event_validator.validate(payload)
