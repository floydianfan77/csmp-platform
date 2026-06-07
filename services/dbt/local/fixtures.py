"""Insert fixture rows into a SQLite landing database."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from flink_job.landing import CREATE_TABLE_SQL, upsert_landing_rows


def write_landing_rows(db_path: Path, rows: list[dict]) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.executescript(CREATE_TABLE_SQL)
    upsert_landing_rows(db_path, rows)
