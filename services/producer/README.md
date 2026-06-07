# CSMP traffic producer (Phase 2)

Simulates per-intersection telemetry and publishes **chapeco-traffic-event v1** to
Redpanda (or stdout for local debugging).

## Install

```powershell
cd services/producer
pip install -e ".[broker,dev]"
```

## Run (stdout)

```powershell
traffic-producer --sink stdout --max-batches 1
```

## Run (broker)

Start Redpanda first:

```powershell
docker compose -f infra/docker-compose.yml up -d
```

Then:

```powershell
traffic-producer --sink broker --bootstrap-servers localhost:19092 --max-batches 3
```

## Environment

See [`.env.example`](.env.example). Key variables:

| Variable | Default | Purpose |
|----------|---------|---------|
| `PRODUCER_SINK` | `stdout` | `stdout` or `broker` |
| `BROKER_BOOTSTRAP_SERVERS` | `localhost:19092` | Kafka bootstrap |
| `PRODUCER_INTERVAL_SECONDS` | `5` | Seconds between batches |
| `PRODUCER_SEED_CSV_PATH` | `../dbt/seeds/...` | Intersection inventory |

## DLQ

Invalid payloads are routed to `chapeco-traffic-events-dlq` (NFR-004). The publisher
increments `invalid_count` for observability.

**Requirement:** FR-001, AT-001
