# Chapecó Smart Mobility Platform (CSMP)

An open-source, event-driven **traffic semaphore monitor** for Chapecó, SC — built
incrementally and **spec-first**. This is a learning/portfolio monorepo.

## Vision

```
                +------------------------+
   (simulator)  |       producer         |   <-- Phase 2
   telemetry -->|  traffic events v1    |
                +-----------+------------+
                            |
                            v
                +------------------------+
                |      Redpanda          |   <-- Phase 2 (Kafka protocol)
                | chapeco-traffic-events |
                +-----------+------------+
                            |
                            v
                +------------------------+
                |   PyFlink (1-min win)  |   <-- Phase 3
                +-----------+------------+
                            |
                            v
                +------------------------+
                | BigQuery landing       |   <-- Phase 3
                +-----------+------------+
                            |
                            v
                +------------------------+
                |   dbt staging + core   |   <-- Phase 4
                +-----------+------------+
                            |
                            v
                +------------------------+
                |   monitor-api          |   <-- Phase 5 (FastAPI)
                +------------------------+
```

## Repository layout

```
Semaphores Project/
├── specs/                   # Requirements, contracts, acceptance (source of truth)
├── services/
│   ├── producer/            # Phase 2: simulator
│   ├── flink-job/           # Phase 3: stream aggregation
│   ├── monitor-api/         # Phase 5: read API
│   └── dbt/                 # Seeds + warehouse models
├── tests/
│   ├── contract/            # Phase 1 ✅ — 22 tests
│   └── acceptance/          # AT-001 (Phase 2, needs Redpanda)
├── docs/                    # Manual, roadmap, ADRs, devlog
├── infra/                   # docker-compose (Phase 2)
├── pyproject.toml
└── Makefile.ps1
```

## Design principles

1. **Spec-first.** Contracts in `specs/contracts/` before producer, Flink, or API code.
   Every PR traces to `FR-*` / `NFR-*` IDs.
2. **Contract-tested.** Phase 1 CI validates JSON Schema, OpenAPI, warehouse YAML, and
   seeds — no broker required.
3. **Correct realtime semantics.** Signal state = last event in window by timestamp;
   freshness SLAs define "realtime" (≤120s to API).
4. **Independently deployable services.** Each folder in `services/` is self-contained.
5. **Local-first.** Redpanda + optional local sink; BigQuery is the cloud target.

## Quick start (Phase 1 — contract tests)

```powershell
pip install -e ".[dev]"
pytest tests/contract -v
# or
.\Makefile.ps1 test-contract
```

Expected: **22 passed**. No Docker or cloud credentials needed.

## Quick start (Phase 2 — producer + Redpanda)

```powershell
.\Makefile.ps1 install-dev
.\Makefile.ps1 install-producer
.\Makefile.ps1 broker-up
.\Makefile.ps1 producer          # one batch to topic
.\Makefile.ps1 test-acceptance   # AT-001
```

Redpanda console: http://localhost:8080 — bootstrap `localhost:19092`.

## Documentation

- [`docs/MANUAL.md`](docs/MANUAL.md) — the full study guide (every phase, deep-dived).
- [`docs/roadmap.md`](docs/roadmap.md) — the live roadmap.
- [`docs/architecture.md`](docs/architecture.md) — living architecture doc.
- [`specs/README.md`](specs/README.md) — requirements + contract index.

## Project history

Every work session is logged in [`docs/devlog.md`](docs/devlog.md) — decisions,
what was built, and why. It's the canonical record of how this project evolved.

## Roadmap

See [`docs/roadmap.md`](docs/roadmap.md). Short version:

- [x] **Phase 0** — Spec approval + GitHub Spec Kit
- [x] **Phase 1** — Contract tests (JSON Schema, OpenAPI, warehouse, seeds)
- [x] **Phase 2** — Redpanda + producer simulator + AT-001
- [x] **Phase 3** — Stream aggregation → SQLite landing (AT-002)
- [ ] **Phase 4** — dbt core + bottleneck + GIS enrichment
- [ ] **Phase 5** — Monitor API (FastAPI)
- [ ] **Phase 6** — Map UI (optional v0.2)

## Spec Kit (Cursor)

Skills in `.cursor/skills/`: `/speckit-tasks`, `/speckit-implement`, `/speckit-analyze`.
Human specs in `specs/` remain canonical.
