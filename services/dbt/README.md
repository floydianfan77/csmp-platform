# CSMP dbt project

Warehouse transforms: staging → core enrichment → orphan report.

## Layout

- `seeds/chapeco_intersection_locations.csv` — fallback intersections (FR-005)
- `models/staging/stg_traffic_signals.sql` — cast/normalize landing (FR-002)
- `models/core/core_traffic_signals.sql` — bottleneck + GIS (FR-004, FR-005)
- `models/core/rpt_orphan_intersections.sql` — IDs missing from seed (FR-005)
- `macros/is_severe_bottleneck.sql` — shared bottleneck logic
- `local/engine.py` — DuckDB pipeline for local dev / acceptance tests (OQ-2)

## Profiles

| Target | Adapter | Use |
|--------|---------|-----|
| `dev` (default) | DuckDB `data/csmp.duckdb` | Local; reads `data/landing.db` via engine |
| `cloud` | BigQuery | Production |

## Local acceptance tests (no dbt CLI required)

```powershell
.\Makefile.ps1 test-warehouse
```

Runs AT-003 and AT-005 against DuckDB + SQLite landing fixtures.

## dbt CLI (optional)

Requires `dbt-duckdb` (dev) or BigQuery credentials (cloud):

```bash
pip install dbt-duckdb
cd services/dbt
dbt seed --profiles-dir .
dbt run --profiles-dir . --target dev
dbt test --profiles-dir .
```

For DuckDB, bootstrap landing from Phase 3 first (`.\Makefile.ps1 aggregate`) or use
`local/engine.py` which attaches SQLite automatically.

## Sync rule

When the warehouse contract changes, update:

1. `specs/contracts/warehouse/traffic_signals_aggregated_stream.yml`
2. `models/staging/_sources.yml` (copy)
3. `tests/contract/test_warehouse_contract.py` must pass
