# CSMP Implementation Plan

**Version:** 0.1 — phased build after spec approval. **No code in this document.**

---

## Phase 0 — Spec approval

- [x] Bootstrap specs + contracts
- [x] Human review: requirements, architecture, acceptance
- [x] Resolve OQ-1..3 in `01-requirements.md`
- [x] Git + GitHub Spec Kit initialized

**Exit criteria:** Approval checklist in requirements all checked. **Complete.**

---

## Phase 1 — Contracts & contract tests

| Task | Delivers | Req | Status |
|------|----------|-----|--------|
| 1.1 | JSON Schema validator tests for sample events | FR-001 | done |
| 1.2 | OpenAPI mock tests (pytest + httpx against stub) | FR-003 | done |
| 1.3 | dbt source YAML synced to warehouse contract | FR-002 | done |
| 1.4 | Seed CSV/JSON for fallback intersections | FR-005 | done |

**Exit criteria:** CI runs contract tests only — no Flink yet. **Complete.**

---

## Phase 2 — Local ingest path

| Task | Delivers | Req | Status |
|------|----------|-----|--------|
| 2.1 | `docker-compose.yml` (Redpanda, ports per architecture) | NFR-002 | done |
| 2.2 | Producer simulator conforming to event v1 | FR-001 | done |
| 2.3 | DLQ topic + invalid event counter | NFR-004 | done |
| 2.4 | Integration test: N events → topic → sample consumed | AT-001 | done |

**Exit criteria:** AT-001 passes locally (with Redpanda running). **Complete.**

---

## Phase 3 — Stream aggregation

| Task | Delivers | Req | Status |
|------|----------|-----|--------|
| 3.1 | Window job: MAX_BY signal_state, correct column mapping | FR-002 | done |
| 3.2 | Sink to SQLite landing (`data/landing.db`) for dev | OQ-2 | done |
| 3.3 | Freshness metric on landing table | NFR-001 | done |

**Exit criteria:** AT-002 passes; no column order bugs. **Complete.**

---

## Phase 4 — Warehouse core (dbt)

| Task | Delivers | Req |
|------|----------|-----|
| 4.1 | `stg_traffic_signals` view | FR-002 | done |
| 4.2 | `core_traffic_signals` incremental + bottleneck | FR-004 | done |
| 4.3 | Seed join + orphan report model | FR-005 | done |
| 4.4 | dbt tests: unique grain, accepted_values signal_state | NFR-004 | done |

**Exit criteria:** AT-003, AT-005 pass. **Complete.**

---

## Phase 5 — Monitor API

| Task | Delivers | Req |
|------|----------|-----|
| 5.1 | FastAPI app from `monitor.v1.openapi.yaml` | FR-003 |
| 5.2 | Read-only query: latest per intersection | FR-003 |
| 5.3 | `/health` with freshness vs NFR-001 | NFR-001 |

**Exit criteria:** AT-004 passes.

---

## Phase 6 — Monitor UI (optional v0.2)

- Map layer (Leaflet/Mapbox) consuming monitor API
- pt-BR labels
- Bottleneck highlights

Blocked on OQ-1 if API-only for v0.1.

---

## Repository layout (target)

```
Semaphores Project/
├── specs/                 ← you are here (source of truth)
├── services/
│   ├── producer/
│   ├── flink-job/
│   ├── monitor-api/
│   └── dbt/
├── infra/
│   └── docker-compose.yml
└── tests/
    ├── contract/
    └── acceptance/
```

---

## Risks

| Risk | Mitigation |
|------|------------|
| BigQuery dev friction | Phase 3.2 local sink fallback |
| Flink complexity | Keep SQL job minimal; checkpoint 15s |
| OSM API rate limits | Cache seed; fallback nodes |
| Scope creep on UI | API-first; UI phase 6 |
