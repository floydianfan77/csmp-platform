# 2. Redpanda as the event backbone

- **Status:** Accepted (Phase 2+)
- **Date:** 2026-06-07

## Context

CSMP ingests high-volume per-intersection telemetry. Producers and stream processors
must be decoupled, replayable, and runnable locally without cloud dependencies.
Candidates include Apache Kafka and Redpanda — both expose the **Kafka protocol**.

## Decision

Use **Redpanda** as the default broker for local development and the initial cloud
target:

- Topic: `chapeco-traffic-events` (plus DLQ topic in Phase 2).
- Host port **19092** maps to internal `redpanda:9092` (documented in architecture spec).
- Producers and Flink use the Kafka API (`confluent-kafka` or Flink Kafka connector).

Apache Kafka remains a compatible alternative — swapping is a bootstrap-server config
change, not an application rewrite.

## Consequences

- Same broker skills from the FinOps portfolio project transfer directly.
- Advertised listeners must be configured for host vs Docker network (producer on host,
  Flink in compose).
- Schema Registry is deferred; JSON Schema in `specs/contracts/` is the v0.1 source
  of truth (see ADR 0003).
