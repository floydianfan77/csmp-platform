# CSMP dbt project (Phase 1: seeds + sources only)

Warehouse transforms (`stg_traffic_signals`, `core_traffic_signals`) land in Phase 4.

## Layout

- `seeds/chapeco_intersection_locations.csv` — fallback intersections (FR-005)
- `models/staging/_sources.yml` — synced from `specs/contracts/warehouse/`

## Sync rule

When the warehouse contract changes, update:

1. `specs/contracts/warehouse/traffic_signals_aggregated_stream.yml`
2. `models/staging/_sources.yml` (copy)
3. `tests/contract/test_warehouse_contract.py` must pass

## Commands (Phase 4+)

Requires BigQuery credentials and `DBT_GCP_PROJECT`.

```bash
cd services/dbt
dbt seed
dbt run
dbt test
```
