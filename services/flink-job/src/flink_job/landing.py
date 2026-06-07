"""Local SQLite landing store (BigQuery substitute for dev — OQ-2)."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

# Must match specs/contracts/warehouse and tests/contract/conftest.py (FR-002)
LANDING_COLUMN_ORDER = (
    "intersection_id",
    "window_end",
    "signal_state",
    "avg_stop_duration_seconds",
    "avg_vehicle_speed_kmh",
    "event_count",
    "ingested_at",
)

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS traffic_signals_aggregated_stream (
    intersection_id TEXT NOT NULL,
    window_end TEXT NOT NULL,
    signal_state TEXT NOT NULL,
    avg_stop_duration_seconds REAL NOT NULL,
    avg_vehicle_speed_kmh REAL NOT NULL,
    event_count INTEGER NOT NULL,
    ingested_at TEXT,
    PRIMARY KEY (intersection_id, window_end)
);
"""


def init_landing_db(db_path: str | Path) -> Path:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute(CREATE_TABLE_SQL)
        conn.commit()
    return path


def upsert_landing_rows(db_path: str | Path, rows: list[dict]) -> None:
    if not rows:
        return
    columns = LANDING_COLUMN_ORDER
    placeholders = ", ".join("?" for _ in columns)
    updates = ", ".join(
        f"{col}=excluded.{col}" for col in columns if col not in ("intersection_id", "window_end")
    )
    sql = f"""
        INSERT INTO traffic_signals_aggregated_stream ({", ".join(columns)})
        VALUES ({placeholders})
        ON CONFLICT(intersection_id, window_end) DO UPDATE SET {updates}
    """
    with sqlite3.connect(db_path) as conn:
        conn.executemany(sql, [tuple(row[col] for col in columns) for row in rows])
        conn.commit()


def upsert_landing_row(db_path: str | Path, row: dict) -> None:
    upsert_landing_rows(db_path, [row])


def fetch_rows(db_path: str | Path, intersection_id: str | None = None) -> list[dict]:
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        if intersection_id:
            cur = conn.execute(
                "SELECT * FROM traffic_signals_aggregated_stream WHERE intersection_id = ? ORDER BY window_end",
                (intersection_id,),
            )
        else:
            cur = conn.execute(
                "SELECT * FROM traffic_signals_aggregated_stream ORDER BY intersection_id, window_end"
            )
        return [dict(row) for row in cur.fetchall()]


def max_landing_lag_seconds(db_path: str | Path) -> float | None:
    """NFR-001 helper: seconds from latest window_end to now (UTC)."""
    rows = fetch_rows(db_path)
    if not rows:
        return None
    latest = max(datetime.fromisoformat(r["window_end"].replace("Z", "+00:00")) for r in rows)
    if latest.tzinfo is None:
        latest = latest.replace(tzinfo=UTC)
    return max(0.0, (datetime.now(tz=UTC) - latest).total_seconds())
