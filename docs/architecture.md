# Architecture

## Overview

The Chapecó Smart Mobility Platform (CSMP) is a **realtime event-driven** pipeline
that turns per-intersection traffic telemetry into a **monitor API** showing current
signal state and bottleneck flags for Chapecó, SC.

This document grows with the project. Today it covers **Phases 0–1** (spec + contracts)
and the target shape for Phases 2–5.

## Components

| Component | Status | Responsibility |
|-----------|--------|----------------|
| `specs/` | ✅ Phase 0 | Requirements, contracts, acceptance criteria |
| contract tests | ✅ Phase 1 | Validate events, API, warehouse, seeds |
| `producer` | ✅ Phase 2 | Emit `chapeco-traffic-event` v1 to Redpanda |
| Redpanda | ✅ Phase 2 | Durable event log (`chapeco-traffic-events`) |
| `flink-job` | ✅ Phase 3 | 1-min windows → SQLite landing (local dev) |
| BigQuery landing | 🔜 cloud target | `stg_raw_landing.traffic_signals_aggregated_stream` |
| `dbt` | 🔜 Phase 4 | Staging + core models, bottleneck flag, GIS join |
| `monitor-api` | 🔜 Phase 5 | FastAPI read API from core tables |
| Monitor UI | ⏳ Phase 6 | Map layer (optional v0.2) |

## Key decisions

- **Contract-first.** Event, warehouse, and API shapes live in
  [`../specs/contracts/`](../specs/contracts/). See
  [`adr/0003-spec-first-contracts.md`](adr/0003-spec-first-contracts.md).
- **Redpanda backbone.** Kafka-protocol broker for local dev; see
  [`adr/0002-redpanda-event-backbone.md`](adr/0002-redpanda-event-backbone.md).
- **Last-in-window signal state.** `signal_state` uses the **last event by timestamp**
  in each 1-minute window — never `MAX(string)`.
- **Medallion-ish warehouse.** Landing (Flink) → staging view (dbt) → core incremental
  (dbt) with merge on `(intersection_id, window_end)`.
- **API reads core only.** The monitor never reads Kafka directly; freshness SLAs apply
  end-to-end (NFR-001: ≤120s to API).

## Event flow (target)

```
simulator/producer --> topic: chapeco-traffic-events
                              |
                         Flink (1-min windows)
                              |
              stg_raw_landing.traffic_signals_aggregated_stream
                              |
                         dbt staging + core
                              |
                         monitor-api (FastAPI)
                              |
                         monitor UI (Phase 6)
```

Detailed diagram: [`../specs/02-architecture.md`](../specs/02-architecture.md).

## Data contracts

| Contract | Path |
|----------|------|
| Kafka event v1 | [`../specs/contracts/events/chapeco-traffic-event.v1.schema.json`](../specs/contracts/events/chapeco-traffic-event.v1.schema.json) |
| Landing table | [`../specs/contracts/warehouse/traffic_signals_aggregated_stream.yml`](../specs/contracts/warehouse/traffic_signals_aggregated_stream.yml) |
| Monitor API v1 | [`../specs/contracts/api/monitor.v1.openapi.yaml`](../specs/contracts/api/monitor.v1.openapi.yaml) |
| Intersection seed | [`../specs/contracts/seeds/chapeco_intersection_locations.v1.schema.json`](../specs/contracts/seeds/chapeco_intersection_locations.v1.schema.json) |

## Why stream processing (Phase 3)

- **Volume:** Raw telemetry is too noisy to expose directly to the monitor.
- **Windowing:** 1-minute tumbling buckets give stable, comparable intersection state.
- **Event time:** Watermarks handle out-of-order simulator (and future municipal) feeds.
- **Replay:** Reprocess history when aggregation logic changes.

## Local dev network

| Service | Host port | Internal |
|---------|-----------|----------|
| Redpanda Kafka | 19092 | redpanda:9092 |
| Monitor API | 8000 | api:8000 |
| Flink JobManager UI | 8081 | optional |
