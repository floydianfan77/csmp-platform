"""CLI entry point for the CSMP traffic producer."""

from __future__ import annotations

import argparse

from traffic_producer import __version__
from traffic_producer.config import Settings
from traffic_producer.publisher import build_publisher
from traffic_producer.scheduler import build_scheduler


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="traffic-producer",
        description="Simulate Chapecó traffic signal telemetry (chapeco-traffic-event v1).",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "--sink",
        choices=["stdout", "broker"],
        help="Output destination (default: PRODUCER_SINK or stdout).",
    )
    parser.add_argument(
        "--interval",
        type=float,
        dest="interval_seconds",
        help="Seconds between batches (one event per intersection per batch).",
    )
    parser.add_argument("--seed", type=int, help="RNG seed for reproducible telemetry.")
    parser.add_argument(
        "--seed-csv",
        dest="seed_csv_path",
        help="Path to chapeco_intersection_locations.csv.",
    )
    parser.add_argument(
        "--max-batches",
        type=int,
        default=None,
        help="Stop after N batches (default: run until interrupted).",
    )
    parser.add_argument(
        "--bootstrap-servers",
        help="Kafka bootstrap (overrides BROKER_BOOTSTRAP_SERVERS).",
    )
    return parser


def _merge_settings(args: argparse.Namespace) -> Settings:
    settings = Settings()
    overrides = {
        "sink": args.sink,
        "interval_seconds": args.interval_seconds,
        "seed": args.seed,
        "seed_csv_path": args.seed_csv_path,
    }
    for key, value in overrides.items():
        if value is not None:
            setattr(settings, key, value)
    if args.bootstrap_servers is not None:
        settings.broker.bootstrap_servers = args.bootstrap_servers
    return settings


def main() -> None:
    args = _build_parser().parse_args()
    settings = _merge_settings(args)
    publisher = build_publisher(settings)
    scheduler = build_scheduler(
        seed_csv_path=settings.seed_csv_path,
        seed=settings.seed,
        publisher=publisher,
        interval_seconds=settings.interval_seconds,
        max_batches=args.max_batches,
    )
    scheduler.run()


if __name__ == "__main__":
    main()
