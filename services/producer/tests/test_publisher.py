"""Publisher validation and DLQ routing."""

from traffic_producer.models import ChapecoTrafficEvent, SignalState
from traffic_producer.publisher import StdoutPublisher
from traffic_producer.topics import TRAFFIC_EVENTS_DLQ_TOPIC, TRAFFIC_EVENTS_TOPIC


def test_valid_event_uses_main_topic():
    publisher = StdoutPublisher()
    event = ChapecoTrafficEvent.new_simulator_event(
        intersection_id="osm-1",
        signal_state=SignalState.GREEN,
        avg_stop_duration_seconds=10.0,
        avg_vehicle_speed_kmh=20.0,
    )
    topic = publisher.publish(event)
    assert topic == TRAFFIC_EVENTS_TOPIC
    assert publisher.invalid_count == 0


def test_invalid_payload_routed_to_dlq():
    publisher = StdoutPublisher()
    topic = publisher.publish_payload(
        {
            "event_id": "550e8400-e29b-41d4-a716-446655440000",
            "intersection_id": "osm-1",
            "environment": {
                "timestamp": "2026-06-07T18:00:00Z",
                "source": "simulator",
            },
        }
    )
    assert topic == TRAFFIC_EVENTS_DLQ_TOPIC
    assert publisher.invalid_count == 1
