"""Kafka helpers for acceptance tests (AT-001)."""

from __future__ import annotations

import json
import os
import socket
import time
import uuid
from collections.abc import Callable
from typing import Any

DEFAULT_BOOTSTRAP = os.environ.get("BROKER_BOOTSTRAP_SERVERS", "localhost:19092")


def broker_available(bootstrap: str = DEFAULT_BOOTSTRAP) -> bool:
    host, _, port = bootstrap.partition(":")
    if not port:
        return False
    try:
        with socket.create_connection((host, int(port)), timeout=2):
            return True
    except OSError:
        return False


def _wait_for_assignment(consumer, timeout_seconds: float = 10.0) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        consumer.poll(0.5)
        if consumer.assignment():
            return
    raise TimeoutError("Kafka consumer partition assignment timed out")


def consume_after_publish(
    *,
    bootstrap: str,
    topic: str,
    publish: Callable[[], None],
    expected: int,
    timeout_seconds: float = 20.0,
    match: Callable[[dict[str, Any]], bool] | None = None,
) -> list[dict[str, Any]]:
    """Subscribe with latest offset, publish, then collect new messages."""
    from confluent_kafka import Consumer

    consumer = Consumer(
        {
            "bootstrap.servers": bootstrap,
            "group.id": f"csmp-test-{uuid.uuid4()}",
            "auto.offset.reset": "latest",
            "enable.auto.commit": False,
        }
    )
    consumer.subscribe([topic])
    try:
        _wait_for_assignment(consumer)
        publish()

        messages: list[dict[str, Any]] = []
        deadline = time.time() + timeout_seconds
        while len(messages) < expected and time.time() < deadline:
            record = consumer.poll(1.0)
            if record is None or record.error():
                continue
            payload = json.loads(record.value().decode("utf-8"))
            if match is None or match(payload):
                messages.append(payload)
        return messages
    finally:
        consumer.close()
