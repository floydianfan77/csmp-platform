"""Local DuckDB warehouse pipeline (BigQuery substitute for dev — OQ-2)."""

from __future__ import annotations

from pathlib import Path

import duckdb


def is_severe_bottleneck(stop_duration: float, speed: float) -> bool:
    return stop_duration > 75.0 and speed < 5.0


def bootstrap(
    con: duckdb.DuckDBPyConnection,
    *,
    landing_db: Path,
    seed_csv: Path,
) -> None:
    con.execute("INSTALL sqlite; LOAD sqlite;")
    con.execute("INSTALL spatial; LOAD spatial;")
    con.execute(f"ATTACH '{landing_db.as_posix()}' AS sqlite_landing (TYPE SQLITE)")
    con.execute(
        """
        CREATE OR REPLACE TABLE raw_landing AS
        SELECT * FROM sqlite_landing.traffic_signals_aggregated_stream
        """
    )
    con.execute(
        f"""
        CREATE OR REPLACE TABLE chapeco_intersection_locations AS
        SELECT * FROM read_csv_auto('{seed_csv.as_posix()}', header=true)
        """
    )


def run_models(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(
        """
        CREATE OR REPLACE VIEW stg_traffic_signals AS
        SELECT
            intersection_id,
            CAST(window_end AS TIMESTAMP) AS window_end,
            upper(signal_state) AS signal_state,
            avg_stop_duration_seconds,
            avg_vehicle_speed_kmh,
            event_count,
            CAST(ingested_at AS TIMESTAMP) AS ingested_at
        FROM raw_landing
        """
    )
    con.execute(
        """
        CREATE OR REPLACE TABLE core_traffic_signals AS
        SELECT
            stg.intersection_id,
            seed.display_name,
            stg.window_end,
            stg.signal_state,
            stg.avg_stop_duration_seconds,
            stg.avg_vehicle_speed_kmh,
            stg.event_count,
            stg.ingested_at,
            (stg.avg_stop_duration_seconds > 75.0 AND stg.avg_vehicle_speed_kmh < 5.0)
                AS is_severe_bottleneck,
            seed.latitude,
            seed.longitude,
            CASE
                WHEN seed.latitude IS NOT NULL AND seed.longitude IS NOT NULL
                THEN ST_Point(seed.longitude, seed.latitude)
            END AS spatial_geography_point
        FROM stg_traffic_signals stg
        LEFT JOIN chapeco_intersection_locations seed
            ON stg.intersection_id = seed.intersection_id
        """
    )
    con.execute(
        """
        CREATE OR REPLACE VIEW rpt_orphan_intersections AS
        SELECT
            stg.intersection_id,
            COUNT(*) AS orphan_row_count,
            MIN(stg.window_end) AS first_seen_window,
            MAX(stg.window_end) AS last_seen_window
        FROM stg_traffic_signals stg
        LEFT JOIN chapeco_intersection_locations seed
            ON stg.intersection_id = seed.intersection_id
        WHERE seed.intersection_id IS NULL
        GROUP BY stg.intersection_id
        """
    )


def run_pipeline(
    *,
    landing_db: Path,
    seed_csv: Path,
    duckdb_path: Path | None = None,
) -> duckdb.DuckDBPyConnection:
    if duckdb_path:
        duckdb_path.parent.mkdir(parents=True, exist_ok=True)
        con = duckdb.connect(str(duckdb_path))
    else:
        con = duckdb.connect(":memory:")
    bootstrap(con, landing_db=landing_db, seed_csv=seed_csv)
    run_models(con)
    return con
