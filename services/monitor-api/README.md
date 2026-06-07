# CSMP Monitor API

Read-only FastAPI service backed by `core_traffic_signals` in DuckDB (local) or BigQuery
via dbt export (cloud).

## Endpoints

| Path | Description |
|------|-------------|
| `GET /health` | Service + data freshness (NFR-001: ≤120s = FRESH) |
| `GET /intersections` | Latest row per intersection |
| `GET /intersections/{id}` | Single intersection or 404 |

Contract: `specs/contracts/api/monitor.v1.openapi.yaml`

## Run locally

Bootstrap warehouse data first (Phase 3 + 4), then:

```powershell
pip install -e "services/monitor-api"
$env:CSMP_MONITOR_DUCKDB_PATH = "data/csmp.duckdb"
csmp-monitor-api
```

Or use the DuckDB pipeline to build `data/csmp.duckdb` from `data/landing.db`:

```powershell
python -c "from pathlib import Path; from local.engine import run_pipeline; run_pipeline(landing_db=Path('data/landing.db'), seed_csv=Path('services/dbt/seeds/chapeco_intersection_locations.csv'), duckdb_path=Path('data/csmp.duckdb'))"
```

Open http://localhost:8000/app/ for the map UI (Phase 6) or `/docs` for Swagger.

## Tests

```powershell
pytest tests/acceptance/test_at004_monitor_api.py -v
```
