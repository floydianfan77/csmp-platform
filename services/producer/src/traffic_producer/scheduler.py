"""Run the simulator on an interval until interrupted or max batches reached."""

from __future__ import annotations

import signal
import sys
import time
from types import FrameType

from traffic_producer.publisher import EventPublisher, StdoutPublisher
from traffic_producer.simulator import TrafficSimulator


class ProducerScheduler:
    def __init__(
        self,
        simulator: TrafficSimulator,
        publisher: EventPublisher | StdoutPublisher,
        *,
        interval_seconds: float,
        max_batches: int | None = None,
    ) -> None:
        self._simulator = simulator
        self._publisher = publisher
        self._interval = interval_seconds
        self._max_batches = max_batches
        self._stop = False

    def _handle_signal(self, _signum: int, _frame: FrameType | None) -> None:
        self._stop = True

    def run(self) -> int:
        signal.signal(signal.SIGINT, self._handle_signal)
        if hasattr(signal, "SIGTERM"):
            signal.signal(signal.SIGTERM, self._handle_signal)

        total = 0
        batches = 0
        try:
            while not self._stop:
                events = self._simulator.generate_batch()
                for event in events:
                    self._publisher.publish(event)
                    total += 1
                self._publisher.flush()
                batches += 1

                if self._max_batches is not None and batches >= self._max_batches:
                    break
                if self._interval > 0 and not self._stop:
                    time.sleep(self._interval)
        finally:
            self._publisher.close()

        print(
            f"[traffic-producer] stopped. emitted {total} events "
            f"({self._publisher.invalid_count} invalid → DLQ).",
            file=sys.stderr,
        )
        return total


def build_scheduler(
    *,
    seed_csv_path: str,
    seed: int | None,
    publisher: EventPublisher | StdoutPublisher,
    interval_seconds: float,
    max_batches: int | None,
) -> ProducerScheduler:
    from traffic_producer.simulator import load_intersections

    intersections = load_intersections(seed_csv_path)
    simulator = TrafficSimulator(intersections, seed=seed)
    return ProducerScheduler(
        simulator,
        publisher,
        interval_seconds=interval_seconds,
        max_batches=max_batches,
    )
