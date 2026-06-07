# Deprecated Gemini spike

These files were generated in a single Gemini session **without** a proper spec.
They are preserved for reference only. **Do not implement from this folder.**

## Known defects (why this was archived)

| File | Issue |
|------|-------|
| Producer | `async run_intersection_simulation` missing `def` (syntax error) |
| Producer | Overpass URL broken (markdown inside string) |
| Producer | Port `19092` vs Flink `redpanda:9092` undocumented |
| Flink job | INSERT column order ≠ sink DDL |
| Flink job | `MAX(signal_state)` wrong semantics (should be last-in-window) |
| dbt | References missing seed `seed_chapeco_intersection_locations` |
| YAML | Only a fragment — not a full warehouse contract |
| Architecture doc | Truncated; marked "Approved" without requirements |

## Replacement

Use [`../../specs/`](../../specs/) as the source of truth:

- Requirements: `01-requirements.md`
- Contracts: `contracts/events/`, `contracts/warehouse/`, `contracts/api/`
- Acceptance: `acceptance/AT-001` … `AT-005`

## Files in this archive

- `gemini-code-1780865928770.md` — truncated architecture
- `gemini-code-1780865978150.py` — Kafka producer/simulator
- `gemini-code-1780865994697.py` — PyFlink job
- `gemini-code-1780866005893.yaml` — partial dbt sources
- `gemini-code-1780866014944.sql` — staging view
- `gemini-code-1780866019885.sql` — core incremental model
- `gemini-code-1780866029682.sh` — docker compose + run script
