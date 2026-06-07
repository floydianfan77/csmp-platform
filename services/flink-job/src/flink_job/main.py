"""CLI for CSMP stream aggregation job."""

from __future__ import annotations

import argparse
import sys

from flink_job import __version__
from flink_job.config import Settings
from flink_job.landing import max_landing_lag_seconds
from flink_job.stream_runner import StreamRunner


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="csmp-flink-job",
        description="CSMP 1-minute window aggregation (FR-002).",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "--mode",
        choices=["stream", "freshness"],
        default="stream",
        help="stream: Kafka → SQLite landing; freshness: print landing lag",
    )
    parser.add_argument("--bootstrap-servers", help="Kafka bootstrap servers")
    parser.add_argument("--landing-db", dest="landing_db_path", help="SQLite landing path")
    parser.add_argument(
        "--max-messages",
        type=int,
        default=None,
        help="Optional cap on Kafka messages (stream mode). Drains until idle if fewer exist.",
    )
    parser.add_argument(
        "--idle-seconds",
        type=float,
        default=2.0,
        help="Stop after this many seconds with no new messages (stream mode).",
    )
    parser.add_argument(
        "--from-earliest",
        action="store_true",
        help="Use earliest offset for new consumer groups (local drain after producer).",
    )
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    settings = Settings()
    if args.bootstrap_servers:
        settings.bootstrap_servers = args.bootstrap_servers
    if args.landing_db_path:
        settings.landing_db_path = args.landing_db_path

    if args.mode == "freshness":
        lag = max_landing_lag_seconds(settings.landing_db_path)
        if lag is None:
            print("No landing rows yet.", file=sys.stderr)
            sys.exit(1)
        print(f"max_landing_lag_seconds={lag:.1f}")
        return

    runner = StreamRunner(settings)
    runner.run(
        max_messages=args.max_messages,
        idle_seconds=args.idle_seconds,
        from_earliest=args.from_earliest,
    )


if __name__ == "__main__":
    main()
