"""Kafka → window aggregate → SQLite landing (local streaming path)."""

from __future__ import annotations

import json
import signal
import sys
import time
from datetime import UTC, datetime

from flink_job.config import Settings
from flink_job.landing import init_landing_db, upsert_landing_rows
from flink_job.window_state import aggregate_events, parse_kafka_json, rows_to_landing


class StreamRunner:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._stop = False
        self._buffer: list = []

    def _handle_signal(self, _signum: int, _frame: object) -> None:
        self._stop = True

    def run(self, *, max_messages: int | None = None, idle_seconds: float = 2.0) -> int:
        from confluent_kafka import Consumer

        signal.signal(signal.SIGINT, self._handle_signal)
        if hasattr(signal, "SIGTERM"):
            signal.signal(signal.SIGTERM, self._handle_signal)

        init_landing_db(self._settings.landing_db_path)
        consumer = Consumer(
            {
                "bootstrap.servers": self._settings.bootstrap_servers,
                "group.id": self._settings.consumer_group,
                "auto.offset.reset": "earliest" if max_messages else "latest",
                "enable.auto.commit": True,
            }
        )
        consumer.subscribe([self._settings.source_topic])

        written = 0
        idle_deadline: float | None = None
        try:
            while not self._stop:
                msg = consumer.poll(1.0)
                if msg is not None and not msg.error():
                    payload = json.loads(msg.value().decode("utf-8"))
                    self._buffer.append(parse_kafka_json(payload))
                    written += 1
                    idle_deadline = None
                    if max_messages is not None and written >= max_messages:
                        break
                elif max_messages is not None and written >= max_messages:
                    break
                elif max_messages is None and written > 0 and idle_deadline is None:
                    idle_deadline = time.time() + idle_seconds
                elif idle_deadline is not None and time.time() >= idle_deadline:
                    break
        finally:
            consumer.close()

        rows = rows_to_landing(aggregate_events(self._buffer))
        upsert_landing_rows(self._settings.landing_db_path, rows)

        print(
            f"[csmp-flink-job] consumed {len(self._buffer)} events → {len(rows)} landing rows",
            file=sys.stderr,
        )
        return len(rows)
