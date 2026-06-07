"""Build DuckDB warehouse from SQLite landing (Phase 4 local path)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from local.engine import run_pipeline

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_LANDING = PROJECT_ROOT / "data" / "landing.db"
DEFAULT_DUCKDB = PROJECT_ROOT / "data" / "csmp.duckdb"
DEFAULT_SEED = PROJECT_ROOT / "services" / "dbt" / "seeds" / "chapeco_intersection_locations.csv"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build csmp.duckdb from landing.db")
    parser.add_argument("--landing-db", type=Path, default=DEFAULT_LANDING)
    parser.add_argument("--duckdb-path", type=Path, default=DEFAULT_DUCKDB)
    parser.add_argument("--seed-csv", type=Path, default=DEFAULT_SEED)
    args = parser.parse_args()

    if not args.landing_db.is_file():
        print(
            f"[warehouse] missing {args.landing_db} — run .\\Makefile.ps1 producer then aggregate first",
            file=sys.stderr,
        )
        sys.exit(1)

    run_pipeline(
        landing_db=args.landing_db,
        seed_csv=args.seed_csv,
        duckdb_path=args.duckdb_path,
    )
    row_count = __import__("duckdb").connect(str(args.duckdb_path)).execute(
        "SELECT COUNT(*) FROM core_traffic_signals"
    ).fetchone()[0]
    print(f"[warehouse] wrote {args.duckdb_path} ({row_count} core rows)")


if __name__ == "__main__":
    main()
