"""End-to-end landing write path."""

from __future__ import annotations

from flink_job.events import TrafficEvent
from flink_job.landing import init_landing_db, upsert_landing_rows
from flink_job.window_state import aggregate_events, parse_kafka_json, rows_to_landing


def write_events_to_landing(events: list[TrafficEvent], db_path: str) -> int:
    init_landing_db(db_path)
    rows = rows_to_landing(aggregate_events(events))
    upsert_landing_rows(db_path, rows)
    return len(rows)


def write_kafka_payloads_to_landing(payloads: list[dict], db_path: str) -> int:
    events = [parse_kafka_json(payload) for payload in payloads]
    return write_events_to_landing(events, db_path)
