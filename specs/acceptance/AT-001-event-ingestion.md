# AT-001 — Event ingestion (FR-001)

**Contract:** `contracts/events/chapeco-traffic-event.v1.schema.json`  
**Topic:** `chapeco-traffic-events`

## Scenario: Valid simulator event is accepted

**Given** Redpanda is running with topic `chapeco-traffic-events`  
**And** the producer simulator is configured with bootstrap `localhost:19092`  
**When** the simulator runs for 60 seconds  
**Then** at least one message per configured intersection is present on the topic  
**And** each message validates against `chapeco-traffic-event.v1.schema.json`  
**And** `environment.source` is `simulator`  
**And** message key equals `intersection_id`

## Scenario: Invalid event is rejected

**Given** a malformed JSON payload (missing `telemetry`)  
**When** it is published to the topic  
**Then** it is routed to `chapeco-traffic-events-dlq` or counted as invalid  
**And** it does not crash the Flink job
