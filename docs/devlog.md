# Development Log

A running record of work sessions on CSMP: decisions made, what was built, the reasoning
behind it, and next steps. Maintained at the end of each session so the project's history
(and the learning journey) is preserved in the repo itself.

> Format: newest session at the top. Each entry captures **Context → Decisions →
> Actions → Learnings → Next steps**.

---

## Session 6 — 2026-06-07 — Phase 5 (monitor API)

### Context
Core warehouse rows from Phase 4 need a read-only HTTP surface for monitoring tools
and AT-004.

### Decisions
| Decision | Choice | Rationale |
|----------|--------|-----------|
| Data source | DuckDB `core_traffic_signals` | Matches local dev pipeline |
| Latest grain | `ROW_NUMBER()` per intersection | FR-003 list + detail |
| Freshness | `max(window_end)` lag vs 120s | NFR-001 / OpenAPI contract |

### Actions
- Added `services/monitor-api/` (FastAPI, repository, CLI `csmp-monitor-api`).
- AT-004: 4 tests passed (health, list, bottleneck filter, 404).
- `Makefile.ps1`: `install-monitor`, `test-monitor`, `monitor-api`.

### Next steps
- [ ] Phase 6 — Map UI (optional v0.2) or polish end-to-end demo script.

---

## Session 5 — 2026-06-07 — Phase 4 (warehouse core)

### Context
Landing rows from Phase 3 need staging/core transforms, bottleneck flags, and spatial
enrichment before the monitor API can query them.

### Decisions
| Decision | Choice | Rationale |
|----------|--------|-----------|
| Local warehouse | DuckDB + SQLite attach | OQ-2; no BigQuery creds for dev |
| dbt targets | `dev` = DuckDB, `cloud` = BigQuery | Same SQL models; adapter switch |
| AT tests | Python `local/engine.py` mirrors dbt SQL | Runnable without dbt CLI in CI |

### Actions
- Added dbt models: `stg_traffic_signals`, `core_traffic_signals`, `rpt_orphan_intersections`.
- Macro `is_severe_bottleneck` (strict `> 75s` AND `< 5 km/h`).
- DuckDB pipeline in `services/dbt/local/engine.py`.
- AT-003 (5 tests) + AT-005 (2 tests) — 7 passed.
- `Makefile.ps1`: `test-warehouse`.

### Next steps
- [ ] Phase 5 — Monitor API (AT-004).

---

## Session 4 — 2026-06-07 — Phase 3 (stream aggregation)

### Context
Phase 2 put valid events on Kafka. Phase 3 aggregates them into 1-minute windows and
lands rows matching the warehouse contract (FR-002).

### Decisions
| Decision | Choice | Rationale |
|----------|--------|-----------|
| Window semantics | Last event by timestamp (`MAX_BY`) | AT-002; not `MAX(string)` |
| Local landing | SQLite `data/landing.db` | OQ-2 dev fallback before BigQuery |
| PyFlink | Optional extra on Python \<3.13 | User env is 3.13; core logic in `window_state.py` |
| Stream path | `stream_runner.py` Kafka → aggregate → SQLite | Runnable local pipeline |

### Actions
- Added `services/flink-job/` (window_state, landing, pipeline, stream_runner, CLI).
- AT-002 tests: 3 window unit tests + 1 landing acceptance test (4 passed).
- `Makefile.ps1`: `test-flink`, `aggregate`, `freshness` mode.
- PyFlink batch SQL kept as optional cross-check when Java + pyflink available.

### Next steps
- [ ] Phase 4 — dbt staging + core models (AT-003, AT-005).

---

## Session 3 — 2026-06-07 — Phase 2 (local ingest)

### Context
Phase 1 proved contracts in CI. Phase 2 connects a real broker and a simulator producer
so AT-001 can run end-to-end.

### Decisions
| Decision | Choice | Rationale |
|----------|--------|-----------|
| Broker port | Host **19092** → internal **9092** | Matches architecture spec |
| Producer layout | `services/producer/` (FinOps pattern) | Independent pyproject + CLI |
| Validation | Pydantic model mirrors JSON Schema | Fail fast before publish |
| Invalid events | Publisher routes to DLQ topic | NFR-004; `invalid_count` for tests |
| Integration tests | `@pytest.mark.integration`, skip if broker down | CI/local flexible |

### Actions
- Added `infra/docker-compose.yml` — Redpanda + console (+ optional producer profile).
- Built `traffic-producer`: simulator (seed CSV), scheduler, broker/stdout sinks.
- DLQ topic `chapeco-traffic-events-dlq` on validation failure.
- AT-001 tests in `tests/acceptance/test_at001_ingestion.py`.
- Extended `Makefile.ps1` with `broker-up`, `test-acceptance`, `producer`.

### Learnings (concepts to study)
- **Advertised listeners** — host `localhost:19092` vs in-network `redpanda:9092`.
- **Message keys** — key = `intersection_id` for partition affinity.
- **DLQ pattern** — quarantine bad payloads without stopping the producer.

### Next steps
- [ ] Phase 3 — PyFlink 1-min windows → landing table (AT-002).

---

### Context
The approved spec defined Kafka events, a warehouse landing table, a monitor API, and
intersection seeds — but nothing enforced those shapes in CI. Phase 1 proves the
contracts are testable before Flink, Redpanda, or a real API exist.

### Decisions
| Decision | Choice | Rationale |
|----------|--------|-----------|
| Test layout | `tests/contract/` at repo root | One place for cross-cutting contract tests |
| Event validation | `jsonschema` + `FormatChecker` | Catches invalid UUIDs, not just missing fields |
| API testing | FastAPI stub + OpenAPI component schemas | Validates responses without Phase 5 implementation |
| Warehouse sync | Copy contract → `services/dbt/models/staging/_sources.yml` | dbt-ready; test asserts parity with spec |
| Seed format | CSV in `services/dbt/seeds/` | dbt-native; 4 Chapecó fallback intersections |
| CI | GitHub Actions `contract-tests.yml` | Exit criteria: contract tests only |

### Actions
- Added root `pyproject.toml` with `[dev]` extras (pytest, jsonschema, fastapi, openapi-spec-validator).
- Wrote 22 contract tests across four modules:
  - `test_event_schema.py` — FR-001
  - `test_monitor_openapi.py` + `stub_monitor_api.py` — FR-003
  - `test_warehouse_contract.py` — FR-002
  - `test_seed_schema.py` — FR-005
- Scaffolded `services/dbt/` (project, profiles, seeds, synced `_sources.yml`).
- Added `Makefile.ps1` (`test-contract`, `install-dev`) and `.github/workflows/contract-tests.yml`.
- Updated `specs/03-implementation-plan.md` — Phase 1 marked complete.
- Added FinOps-style docs: `docs/MANUAL.md`, `roadmap.md`, `architecture.md`, `devlog.md`, ADRs.

### Learnings (concepts to study)
- **Contract testing** — validate the spec, not just the implementation.
- **OpenAPI as contract** — document + machine-checkable response shapes.
- **Column order as contract** — Flink INSERT order must match landing DDL exactly.
- **JSON Schema `format`** — UUID/date-time checks need an explicit format checker.

### Next steps
- [ ] Phase 2 — Redpanda compose + producer simulator (AT-001).
- [ ] (later) promote shared Python models to `libs/common` like FinOps.

---

## Session 1 — 2026-06-07 — Phase 0 (spec bootstrap + Spec Kit)

### Context
Starting a portfolio project for realtime traffic **semaphore monitoring** in Chapecó, SC.
Goal: spec-driven development with traceable requirements before any pipeline code.

### Decisions
| Decision | Choice | Rationale |
|----------|--------|-----------|
| Workflow | Spec-first + GitHub Spec Kit | Same discipline as professional SDD; Cursor skills for tasks |
| Monitor v0.1 | API-only | Map UI deferred to Phase 6 |
| Dev warehouse | Local sink fallback allowed | BigQuery is cloud target, not dev blocker |
| Signal aggregation | Last event by timestamp in window | Correct realtime semantics |
| Broker | Redpanda (Kafka protocol) | Portfolio consistency; local-friendly |

### Actions
- Bootstrapped `specs/`: constitution, requirements (FR/NFR), architecture, plan, acceptance AT-001..005.
- Authored contracts: event JSON Schema, warehouse YAML, OpenAPI monitor API, seed schema.
- Initialized git; ran `specify init` with `cursor-agent` integration.
- Synced CSMP constitution into `.specify/memory/constitution.md`.
- Second commit: Spec Kit extensions + approved spec status.

### Learnings (concepts to study)
- **FR/NFR traceability** — requirements → contracts → acceptance tests.
- **Spec Kit vs specs/** — skills for implementation loops; human contracts stay canonical.
- **Freshness SLAs** — define "realtime" as measurable lag, not marketing.

### Next steps
- [x] Phase 1 contract tests (Session 2).
- [ ] Phase 2 ingest path.
