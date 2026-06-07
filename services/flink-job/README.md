# CSMP PyFlink aggregation (Phase 3)

1-minute **tumbling windows** over `chapeco-traffic-events` → SQLite landing table
(local substitute for BigQuery — OQ-2).

## Architecture

| Module | Role |
|--------|------|
| `window_state.py` | Window logic — `MAX_BY` via last timestamp (AT-002) |
| `batch_aggregate.py` | Same SQL in PyFlink batch mode (optional, Python \<3.13 + Java) |
| `stream_runner.py` | Kafka → aggregate → SQLite for local dev |
| `landing.py` | SQLite schema matching warehouse contract column order |

## Install

```powershell
cd services/flink-job
pip install -e ".[dev,stream]"
# Optional PyFlink (Python 3.10–3.12 + Java 11):
pip install -e ".[pyflink]"
```

## Run

```powershell
csmp-flink-job --mode stream --max-messages 20 --landing-db ../../data/landing.db
csmp-flink-job --mode freshness --landing-db ../../data/landing.db
```

## Tests

```powershell
pytest services/flink-job/tests/test_at002_window.py -v
pytest tests/acceptance/test_at002_aggregation.py -v -m integration
```

**Requirements:** FR-002, AT-002, NFR-001
