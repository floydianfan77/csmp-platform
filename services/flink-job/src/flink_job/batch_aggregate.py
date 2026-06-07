"""PyFlink batch SQL — optional (requires Java + apache-flink, Python <3.13)."""

from __future__ import annotations

from datetime import datetime

try:
    from pyflink.table import EnvironmentSettings, TableEnvironment
except ImportError:  # pragma: no cover
    EnvironmentSettings = None  # type: ignore
    TableEnvironment = None  # type: ignore


def _sql_timestamp(ts: datetime) -> str:
    return ts.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def _values_row(
    intersection_id: str,
    event_timestamp: datetime,
    signal_state: str,
    avg_stop_duration_seconds: float,
    avg_vehicle_speed_kmh: float,
) -> str:
    return (
        f"('{intersection_id}', TIMESTAMP '{_sql_timestamp(event_timestamp)}', "
        f"'{signal_state}', {avg_stop_duration_seconds}, {avg_vehicle_speed_kmh})"
    )


def aggregate_events(
    events: list[tuple[str, datetime, str, float, float]],
) -> list[dict]:
    if EnvironmentSettings is None or TableEnvironment is None:
        raise RuntimeError("PyFlink not installed — pip install -e '.[pyflink]' on Python 3.11")

    if not events:
        return []

    values_sql = ",\n".join(_values_row(*event) for event in events)
    settings = EnvironmentSettings.new_instance().in_batch_mode().build()
    t_env = TableEnvironment.create(settings)

    t_env.execute_sql(
        f"""
        CREATE TEMPORARY VIEW source_events AS
        SELECT *
        FROM (VALUES {values_sql}) AS t(
            intersection_id,
            event_timestamp,
            signal_state,
            avg_stop_duration_seconds,
            avg_vehicle_speed_kmh
        )
        """
    )

    table = t_env.sql_query(
        """
        SELECT
            intersection_id,
            window_end,
            MAX_BY(signal_state, event_timestamp) AS signal_state,
            AVG(avg_stop_duration_seconds) AS avg_stop_duration_seconds,
            AVG(avg_vehicle_speed_kmh) AS avg_vehicle_speed_kmh,
            COUNT(*) AS event_count
        FROM TABLE(
            TUMBLE(
                TABLE source_events,
                DESCRIPTOR(event_timestamp),
                INTERVAL '1' MINUTE
            )
        )
        GROUP BY intersection_id, window_end
        ORDER BY intersection_id, window_end
        """
    )

    rows: list[dict] = []
    with table.execute().collect() as results:
        for row in results:
            rows.append(
                {
                    "intersection_id": row[0],
                    "window_end": row[1],
                    "signal_state": row[2],
                    "avg_stop_duration_seconds": float(row[3]),
                    "avg_vehicle_speed_kmh": float(row[4]),
                    "event_count": int(row[5]),
                }
            )
    return rows
