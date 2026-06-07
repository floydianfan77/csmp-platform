"""AT-001 integration tests — require Redpanda on localhost:19092."""

from __future__ import annotations

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from tests.acceptance.kafka_helpers import DEFAULT_BOOTSTRAP, broker_available, consume_after_publish
from tests.contract.conftest import EVENT_SCHEMA_PATH, SEED_CSV_PATH, load_json

pytestmark = pytest.mark.integration


@pytest.fixture
def event_validator() -> Draft202012Validator:
    return Draft202012Validator(load_json(EVENT_SCHEMA_PATH), format_checker=FormatChecker())


@pytest.fixture
def bootstrap() -> str:
    if not broker_available():
        pytest.skip("Redpanda not reachable — run: docker compose -f infra/docker-compose.yml up -d")
    return DEFAULT_BOOTSTRAP


def test_valid_simulator_events_on_topic(bootstrap, event_validator):
    from traffic_producer.config import BrokerSettings, Settings
    from traffic_producer.publisher import EventPublisher
    from traffic_producer.simulator import TrafficSimulator, load_intersections

    intersections = load_intersections(SEED_CSV_PATH)
    simulator = TrafficSimulator(intersections, seed=99)
    publisher = EventPublisher(BrokerSettings(bootstrap_servers=bootstrap))
    expected_ids = set(simulator.intersection_ids)
    batch = simulator.generate_batch()

    def publish_batch() -> None:
        for event in batch:
            publisher.publish(event)
        publisher.flush()

    payloads = consume_after_publish(
        bootstrap=bootstrap,
        topic=Settings().broker.topic,
        publish=publish_batch,
        expected=len(expected_ids),
        match=lambda p: p.get("intersection_id") in expected_ids,
    )
    assert len(payloads) >= len(expected_ids)

    seen_ids: set[str] = set()
    for payload in payloads:
        event_validator.validate(payload)
        assert payload["environment"]["source"] == "simulator"
        seen_ids.add(payload["intersection_id"])

    assert expected_ids.issubset(seen_ids)


def test_invalid_event_routed_to_dlq(bootstrap):
    from traffic_producer.config import BrokerSettings
    from traffic_producer.publisher import EventPublisher
    from traffic_producer.topics import TRAFFIC_EVENTS_DLQ_TOPIC

    publisher = EventPublisher(BrokerSettings(bootstrap_servers=bootstrap))
    bad_payload = {
        "event_id": "550e8400-e29b-41d4-a716-446655440000",
        "intersection_id": "osm-test-invalid",
        "environment": {
            "timestamp": "2026-06-07T18:00:00Z",
            "source": "simulator",
        },
    }

    def publish_bad() -> None:
        topic = publisher.publish_payload(bad_payload)
        assert topic == TRAFFIC_EVENTS_DLQ_TOPIC
        publisher.flush()

    dlq_messages = consume_after_publish(
        bootstrap=bootstrap,
        topic=TRAFFIC_EVENTS_DLQ_TOPIC,
        publish=publish_bad,
        expected=1,
        match=lambda p: p.get("intersection_id") == "osm-test-invalid",
    )

    assert publisher.invalid_count == 1
    assert dlq_messages[0]["intersection_id"] == "osm-test-invalid"
    assert "telemetry" not in dlq_messages[0]
