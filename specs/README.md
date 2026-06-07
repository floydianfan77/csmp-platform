# CSMP — Specification index

This folder is the **single source of truth** for the Chapecó Smart Mobility Platform.
Implementation code must trace to requirement IDs and contracts defined here.

## Read order

1. [`constitution.md`](constitution.md) — non-negotiable principles
2. [`01-requirements.md`](01-requirements.md) — FR/NFR with IDs
3. [`02-architecture.md`](02-architecture.md) — components and data flow
4. [`03-implementation-plan.md`](03-implementation-plan.md) — phased build (no code yet)
5. [`contracts/`](contracts/) — machine-readable contracts
6. [`acceptance/`](acceptance/) — Given/When/Then per requirement

## Workflow (spec-driven)

```
constitution → requirements → architecture → contracts → acceptance
       ↓ approve by human ↓
              implementation → tests prove acceptance
```

**Rule:** No new service code until the relevant contract version is merged and
acceptance criteria exist.

## Contract versions

| Artifact | Version | Path |
|----------|---------|------|
| Kafka event | `v1` | `contracts/events/chapeco-traffic-event.v1.schema.json` |
| Warehouse landing table | `v1` | `contracts/warehouse/traffic_signals_aggregated_stream.yml` |
| Monitor API | `v1` | `contracts/api/monitor.v1.openapi.yaml` |
| Intersection seed | `v1` | `contracts/seeds/chapeco_intersection_locations.v1.schema.json` |

## Traceability matrix (summary)

| Requirement | Contract | Acceptance |
|-------------|----------|------------|
| FR-001 | event v1 | AT-001 |
| FR-002 | warehouse v1 | AT-002 |
| FR-003 | monitor API v1 | AT-004 |
| FR-004 | dbt core model (planned) | AT-003 |
| FR-005 | seed v1 | AT-005 |
