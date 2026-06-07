# CSMP Requirements

**Product:** Chapecó Smart Mobility Platform (CSMP) — realtime traffic **semaphore monitor**  
**Version:** 0.1 (approved for implementation bootstrap)  
**Grain of monitor:** one row per intersection showing **latest known state** within freshness SLA

---

## 1. Problem statement

Operators and citizens need a trustworthy view of **traffic signal state** and **congestion
signals** across Chapecó intersections. Raw telemetry is high-volume; the monitor must show
**current conditions** derived from validated, windowed aggregates — not raw Kafka noise.

## 2. Goals

- Ingest per-intersection telemetry continuously.
- Aggregate to **1-minute tumbling windows** per intersection.
- Expose a **monitor API** (and later UI) with map-ready coordinates and bottleneck flags.
- Run the ingestion + stream path **locally** for development.

## 3. Out of scope (v0.1)

- City-wide traffic prediction / ML
- Direct control of physical signal hardware
- Mobile native apps (API-first; UI is a follow-on)
- Multi-city support beyond Chapecó bounding box

## 4. Assumptions

- **A1:** v0.1 uses a **simulator producer**; real municipal feeds may replace it in v2.
- **A2:** Intersection inventory comes from **OpenStreetMap** with a **local fallback seed**.
- **A3:** Landing warehouse is **BigQuery** dataset `stg_raw_landing` (cloud target).
- **A4:** Monitor reads from **core** tables (dbt), not directly from Kafka.

---

## 5. Functional requirements

### FR-001 — Event ingestion

The system SHALL publish traffic telemetry events to Kafka topic `chapeco-traffic-events`
conforming to `chapeco-traffic-event.v1.schema.json`.

| Field | Rule |
|-------|------|
| Key | `intersection_id` (recommended) |
| Rate | ≥ 1 event per intersection per 10s (simulator) |

**Traces to:** `contracts/events/`, AT-001

---

### FR-002 — Stream aggregation

A Flink job SHALL consume `chapeco-traffic-events` and write **1-minute tumbling window**
aggregates to `stg_raw_landing.traffic_signals_aggregated_stream`.

| Rule | Detail |
|------|--------|
| Window | Tumbling, 1 minute, event time |
| Grain | `(intersection_id, window_end)` unique |
| `signal_state` | **Last** `telemetry.current_signal_state` by `event_timestamp` in window |
| Metrics | `avg_stop_duration`, `avg_vehicle_speed` = AVG in window |

**Traces to:** `contracts/warehouse/`, AT-002

---

### FR-003 — Realtime monitor API

The system SHALL expose HTTP API `monitor.v1` returning intersection status for the monitor.

| Endpoint (min) | Purpose |
|----------------|---------|
| `GET /health` | Liveness + data freshness summary |
| `GET /intersections` | List intersections with latest state |
| `GET /intersections/{id}` | Detail for one intersection |

**Traces to:** `contracts/api/monitor.v1.openapi.yaml`, AT-004

---

### FR-004 — Bottleneck detection

The core model SHALL set `is_severe_bottleneck = true` when **both**:

- `avg_stop_duration_seconds > 75.0`
- `avg_vehicle_speed_kmh < 5.0`

for the same `(intersection_id, window_end)`.

**Traces to:** AT-003

---

### FR-005 — Spatial enrichment

Each monitored intersection SHALL have a non-null `spatial_geography_point` (WGS84) by
joining aggregates to seed `chapeco_intersection_locations`.

If an `intersection_id` appears in aggregates but not in seed, the pipeline SHALL
surface it in a **data quality report** (not silent drop).

**Traces to:** `contracts/seeds/`, AT-005

---

## 6. Non-functional requirements

### NFR-001 — Freshness (monitor)

| Metric | Target (v0.1) |
|--------|----------------|
| p95 lag: event `environment.timestamp` → monitor API | **≤ 120 seconds** |
| p95 lag: `window_end` → row in core table | **≤ 180 seconds** |

### NFR-002 — Availability (local dev)

`docker compose up` SHALL start Redpanda + Flink job manager + producer (simulator) with
documented ports.

### NFR-003 — Delivery semantics

Flink → BigQuery landing: **at-least-once** (documented). Core dbt layer: **idempotent merge**
on `(intersection_id, window_end)`.

### NFR-004 — Data quality

- Invalid JSON events: **≤ 0.1%** sustained; excess triggers investigation (not auto-retry forever).
- DLQ or `invalid_events` topic required before production.

### NFR-005 — Security (v0.1)

Monitor API: no auth (local dev). **v0.2** adds API key or OAuth — noted, not implemented.

---

## 7. Glossary

| Term | Meaning |
|------|---------|
| **Intersection** | A traffic signal node (OSM `highway=traffic_signals`) |
| **Signal state** | `GREEN`, `RED`, `FLASHING_YELLOW`, … |
| **Window** | 1-minute tumbling bucket on event time |
| **Monitor** | API (+ future UI) showing latest intersection status |
| **Bottleneck** | Severe stop duration + very low speed (FR-004) |

---

## 8. Resolved decisions (v0.1)

| ID | Decision |
|----|----------|
| OQ-1 | **API-only** in v0.1; map UI in Phase 6 |
| OQ-2 | **Local sink fallback** (Parquet/SQLite) for dev; BigQuery for cloud target |
| OQ-3 | **pt-BR** for user-facing monitor UI (Phase 6); API errors in English for v0.1 |

---

## 9. Approval checklist

- [x] Product owner reviewed problem statement & scope
- [x] FR/NFR IDs accepted
- [x] Contracts v1 reviewed against FR-001..005
- [x] Acceptance scenarios reviewed
- [x] Open questions OQ-1..3 resolved

**Spec approved — implementation may proceed per `03-implementation-plan.md`.**
