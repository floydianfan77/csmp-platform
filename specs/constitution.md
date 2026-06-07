# CSMP Constitution

Non-negotiable principles for the Chapecó Smart Mobility Platform.
All specs, plans, and implementations must comply.

## 1. Contract-first

- Kafka events, warehouse tables, and the monitor API are defined in `specs/contracts/`
  **before** producer, Flink, dbt, or API code is written.
- Breaking contract changes require a **new version** (`v2`) and a migration note.

## 2. Spec before code

- Every implementation PR references at least one `FR-*` or `NFR-*` ID.
- Spike code and throwaway prototypes are **not** a specification.

## 3. Testable acceptance

- Every functional requirement has at least one acceptance scenario in `specs/acceptance/`.
- "Done" means acceptance tests pass — not "it compiles".

## 4. Realtime semantics are explicit

- "Realtime" is defined as **freshness SLAs** (see NFR-001), not marketing language.
- Signal state in a window uses **last event by timestamp**, never `MAX(string)`.

## 5. Local-first development

- Full pipeline must run locally: Redpanda + Flink + (optional) BigQuery emulator or
  local sink substitute documented in the plan.
- Cloud (BigQuery) is a **deployment target**, not a dev blocker.

## 6. At-least-once + idempotent sinks

- Stream sinks declare delivery guarantee explicitly.
- Warehouse **core** layer uses merge/upsert on natural keys — safe to reprocess.

## 7. Failure isolation

- Invalid events are quarantined (dead-letter topic or file) — they do not block the stream.
- Missing OSM seed data must not silently drop intersections (see FR-005).

## 8. Documentation language

- Specs: English (contracts and IDs).
- User-facing monitor copy: Portuguese (pt-BR) when UI is built.
