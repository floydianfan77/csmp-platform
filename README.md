# Chapecó Smart Mobility Platform (CSMP)

Real-time **traffic signal monitor** for intersections in Chapecó, SC — built **spec-first**.

## Status

| Phase | Status |
|-------|--------|
| Spec (requirements + contracts) | **Approved** — see [`specs/`](specs/) |
| Git + Spec Kit | **Initialized** |
| Implementation | **Phase 1** — contract tests (see plan) |

## Quick links

- Start here: [`specs/README.md`](specs/README.md)
- Requirements: [`specs/01-requirements.md`](specs/01-requirements.md)
- Architecture: [`specs/02-architecture.md`](specs/02-architecture.md)
- Implementation plan: [`specs/03-implementation-plan.md`](specs/03-implementation-plan.md)
- Event contract: [`specs/contracts/events/chapeco-traffic-event.v1.schema.json`](specs/contracts/events/chapeco-traffic-event.v1.schema.json)
- Monitor API: [`specs/contracts/api/monitor.v1.openapi.yaml`](specs/contracts/api/monitor.v1.openapi.yaml)

## Spec Kit (Cursor)

This project uses [GitHub Spec Kit](https://github.com/github/spec-kit). Skills live in `.cursor/skills/`.

| Skill | When to use |
|-------|-------------|
| `/speckit-tasks` | Break Phase 1 into actionable tasks from existing spec |
| `/speckit-implement` | Execute a task batch with traceability to FR/NFR |
| `/speckit-analyze` | Cross-check specs vs contracts before coding |
| `/speckit-checklist` | Quality gate on requirements completeness |

**Note:** Human-authored specs in `specs/` are canonical. Spec Kit skills extend the workflow — they do not replace contracts in `specs/contracts/`.
