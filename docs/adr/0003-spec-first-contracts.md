# 3. Spec-first development with machine-readable contracts

- **Status:** Accepted
- **Date:** 2026-06-07

## Context

The monitor spans Kafka events, stream aggregation, a warehouse landing table, dbt
transforms, and a read API. Without explicit contracts, implementations drift — wrong
column order in Flink sinks, ambiguous "realtime" semantics, and untestable requirements.

## Decision

**Spec before code.** The `specs/` folder is the source of truth:

| Artifact | Format | Requirement trace |
|----------|--------|-------------------|
| Kafka events | JSON Schema v1 | FR-001 |
| Landing table | dbt sources YAML | FR-002 |
| Monitor API | OpenAPI 3.1 | FR-003 |
| Intersection seed | JSON Schema v1 | FR-005 |

Implementation is blocked until contracts and acceptance scenarios (`specs/acceptance/`)
exist. Phase 1 adds **contract tests** that validate samples against these artifacts
before any Flink or producer code ships.

[GitHub Spec Kit](https://github.com/github/spec-kit) provides Cursor skills for task
breakdown (`/speckit-tasks`, `/speckit-implement`); it extends the workflow but does
**not** replace `specs/contracts/`.

## Consequences

- Every service PR references `FR-*` / `NFR-*` IDs.
- Breaking changes require contract version bumps (`v2`) and migration notes.
- dbt `_sources.yml` must stay synced with `specs/contracts/warehouse/` (enforced by
  `tests/contract/test_warehouse_contract.py`).
