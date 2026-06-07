"""Synthetic traffic telemetry for configured Chapecó intersections."""

from __future__ import annotations

import csv
import random
from dataclasses import dataclass
from pathlib import Path

from traffic_producer.models import ChapecoTrafficEvent, SignalState


@dataclass(frozen=True)
class Intersection:
    intersection_id: str
    display_name: str


SIGNAL_STATES = list(SignalState)


def load_intersections(seed_csv_path: str | Path) -> list[Intersection]:
    path = Path(seed_csv_path)
    rows: list[Intersection] = []
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            rows.append(
                Intersection(
                    intersection_id=row["intersection_id"],
                    display_name=row["display_name"],
                )
            )
    if not rows:
        raise ValueError(f"No intersections found in {path}")
    return rows


class TrafficSimulator:
    """Emit one valid event per intersection per batch (FR-001 rate)."""

    def __init__(self, intersections: list[Intersection], *, seed: int | None = None) -> None:
        self._intersections = intersections
        self._rng = random.Random(seed)

    @property
    def intersection_ids(self) -> list[str]:
        return [item.intersection_id for item in self._intersections]

    def generate_batch(self) -> list[ChapecoTrafficEvent]:
        events: list[ChapecoTrafficEvent] = []
        for intersection in self._intersections:
            signal = self._rng.choice(SIGNAL_STATES)
            stop_seconds = round(self._rng.uniform(5.0, 90.0), 1)
            speed = round(self._rng.uniform(2.0, 45.0), 1)
            events.append(
                ChapecoTrafficEvent.new_simulator_event(
                    intersection_id=intersection.intersection_id,
                    signal_state=signal,
                    avg_stop_duration_seconds=stop_seconds,
                    avg_vehicle_speed_kmh=speed,
                )
            )
        return events
