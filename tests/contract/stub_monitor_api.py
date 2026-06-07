"""
Minimal monitor API stub for Phase 1 contract tests (FR-003).

Not the production service — only proves responses conform to monitor.v1.openapi.yaml.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="CSMP Monitor API (contract stub)", version="1.0.0")

_INTERSECTIONS = [
    {
        "intersection_id": "osm-287654321",
        "display_name": "Av. Getúlio Vargas × Av. Nereu Ramos",
        "signal_state": "GREEN",
        "avg_stop_duration_seconds": 22.0,
        "avg_vehicle_speed_kmh": 28.5,
        "is_severe_bottleneck": False,
        "window_end": "2026-06-07T18:00:00Z",
        "location": {"latitude": -27.0964, "longitude": -52.6181},
    },
    {
        "intersection_id": "osm-287654322",
        "display_name": "Av. São Pedro × Rua Coronel Passos Maia",
        "signal_state": "RED",
        "avg_stop_duration_seconds": 80.0,
        "avg_vehicle_speed_kmh": 3.0,
        "is_severe_bottleneck": True,
        "window_end": "2026-06-07T18:00:00Z",
        "location": {"latitude": -27.1012, "longitude": -52.6098},
    },
    {
        "intersection_id": "osm-287654323",
        "display_name": "Av. Fernando Machado × Rua Bahia",
        "signal_state": "YELLOW",
        "avg_stop_duration_seconds": 35.0,
        "avg_vehicle_speed_kmh": 15.0,
        "is_severe_bottleneck": False,
        "window_end": "2026-06-07T18:00:00Z",
        "location": {"latitude": -27.0948, "longitude": -52.6155},
    },
]

_BY_ID = {row["intersection_id"]: row for row in _INTERSECTIONS}


@app.get("/health")
def get_health() -> dict:
    return {
        "status": "ok",
        "freshness_status": "FRESH",
        "max_lag_seconds": 45.0,
        "intersection_count": len(_INTERSECTIONS),
    }


@app.get("/intersections")
def list_intersections(bottleneck_only: bool = False) -> dict:
    items = _INTERSECTIONS
    if bottleneck_only:
        items = [row for row in items if row["is_severe_bottleneck"]]
    return {"count": len(items), "items": items}


@app.get("/intersections/{intersection_id}")
def get_intersection(intersection_id: str):
    row = _BY_ID.get(intersection_id)
    if row is None:
        return JSONResponse(
            status_code=404,
            content={
                "code": "NOT_FOUND",
                "message": f"Unknown intersection: {intersection_id}",
            },
        )
    return row
