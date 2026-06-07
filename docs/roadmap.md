# Roadmap

Incremental build-out of the Chapecó Smart Mobility Platform (CSMP). Each phase is
shippable on its own. Full task lists live in
[`../specs/03-implementation-plan.md`](../specs/03-implementation-plan.md).

## Phase 0 — Spec approval ✅

- [x] Bootstrap requirements, architecture, acceptance criteria
- [x] Machine-readable contracts (event, warehouse, API, seed)
- [x] Human review + resolve open questions (API-only v0.1, local sink fallback)
- [x] Git + GitHub Spec Kit (Cursor skills)

## Phase 1 — Contracts & contract tests ✅ (current)

Prove the spec is testable before streaming code exists.

- [x] JSON Schema tests for `chapeco-traffic-event` v1 (FR-001)
- [x] OpenAPI validation + stub monitor API tests (FR-003)
- [x] dbt `_sources.yml` synced to warehouse contract (FR-002)
- [x] Fallback intersection seed CSV + schema tests (FR-005)
- [x] GitHub Actions workflow: `contract-tests.yml`
- [ ] (nice-to-have) shared `libs/common` Python models mirroring JSON Schema

## Phase 2 — Local ingest path

- [x] `infra/docker-compose.yml` — Redpanda on port **19092** (NFR-002)
- [x] Producer simulator conforming to event v1 (FR-001)
- [x] DLQ topic `chapeco-traffic-events-dlq` + invalid event counter (NFR-004)
- [x] Integration test: N events → topic → consumed (AT-001)

## Phase 3 — Stream aggregation

- [x] `services/flink-job/` — 1-min windows, MAX_BY semantics (FR-002)
- [x] SQLite landing `data/landing.db` (OQ-2 local substitute)
- [x] Freshness helper `csmp-flink-job --mode freshness`
- [x] AT-002 tests (window + landing acceptance)

## Phase 4 — Warehouse core (dbt)

- [ ] `stg_traffic_signals` view
- [ ] `core_traffic_signals` incremental + `is_severe_bottleneck` (FR-004)
- [ ] Seed join + orphan report model (FR-005)
- [ ] dbt tests: grain, accepted_values
- [ ] AT-003, AT-005 pass

## Phase 5 — Monitor API

- [ ] Production FastAPI app from `monitor.v1.openapi.yaml` (FR-003)
- [ ] Latest row per intersection from core
- [ ] `/health` freshness vs NFR-001 (≤120s)
- [ ] AT-004 passes

## Phase 6 — Monitor UI (optional v0.2)

- [ ] Map layer (Leaflet/Mapbox) consuming monitor API
- [ ] pt-BR labels and bottleneck highlights
- [ ] Screenshot in `docs/assets/`
