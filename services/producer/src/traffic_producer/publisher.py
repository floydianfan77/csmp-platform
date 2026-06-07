"""Publish traffic events to stdout or Redpanda with schema validation + DLQ routing."""

from __future__ import annotations

import json
import sys
from typing import Any

from pydantic import ValidationError

from traffic_producer.config import BrokerSettings, Settings
from traffic_producer.models import ChapecoTrafficEvent
from traffic_producer.topics import TRAFFIC_EVENTS_DLQ_TOPIC, TRAFFIC_EVENTS_TOPIC


class EventPublisher:
    """Valid events → main topic; invalid payloads → DLQ (NFR-004)."""

    def __init__(self, settings: BrokerSettings) -> None:
        self._settings = settings
        self._producer = None
        self.invalid_count = 0
        self._connect()

    def _connect(self) -> None:
        try:
            from confluent_kafka import Producer
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                'Broker sink requires: pip install -e ".[broker]"'
            ) from exc

        self._producer = Producer(
            {
                "bootstrap.servers": self._settings.bootstrap_servers,
                "client.id": self._settings.client_id,
                "enable.idempotence": True,
            }
        )

    def publish(self, event: ChapecoTrafficEvent) -> str:
        payload = json.loads(event.model_dump_json(exclude_none=True))
        return self.publish_payload(payload)

    def publish_payload(self, payload: dict[str, Any]) -> str:
        assert self._producer is not None
        try:
            event = ChapecoTrafficEvent.model_validate(payload)
            topic = self._settings.topic
            key = event.intersection_id
            body = event.model_dump_json(exclude_none=True)
        except ValidationError:
            self.invalid_count += 1
            topic = self._settings.dlq_topic
            key = str(payload.get("intersection_id", "unknown"))
            body = json.dumps(payload)

        self._producer.produce(
            topic=topic,
            key=key.encode("utf-8"),
            value=body.encode("utf-8"),
        )
        self._producer.poll(0)
        return topic

    def flush(self) -> None:
        if self._producer is not None:
            self._producer.flush()

    def close(self) -> None:
        self.flush()


class StdoutPublisher:
    """Local dev sink — prints JSON lines, no broker required."""

    def __init__(self) -> None:
        self.invalid_count = 0

    def publish(self, event: ChapecoTrafficEvent) -> str:
        print(event.model_dump_json())
        return TRAFFIC_EVENTS_TOPIC

    def publish_payload(self, payload: dict[str, Any]) -> str:
        try:
            event = ChapecoTrafficEvent.model_validate(payload)
        except ValidationError:
            self.invalid_count += 1
            print(json.dumps({"dlq": payload}))
            return TRAFFIC_EVENTS_DLQ_TOPIC
        print(event.model_dump_json())
        return TRAFFIC_EVENTS_TOPIC

    def flush(self) -> None:
        return

    def close(self) -> None:
        return


def build_publisher(settings: Settings) -> EventPublisher | StdoutPublisher:
    if settings.sink == "broker":
        return EventPublisher(settings.broker)
    if settings.sink == "stdout":
        return StdoutPublisher()
    raise ValueError(f"Unknown sink: {settings.sink!r}")
