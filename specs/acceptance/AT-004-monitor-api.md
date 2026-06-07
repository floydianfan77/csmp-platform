# AT-004 — Monitor API (FR-003, NFR-001)

**Contract:** `contracts/api/monitor.v1.openapi.yaml`

## Scenario: Health reports freshness

**Given** core data with latest `window_end` within 60 seconds of now  
**When** `GET /health` is called  
**Then** response status is 200  
**And** `freshness_status` is `FRESH`  
**And** `max_lag_seconds` <= 120

## Scenario: List intersections

**Given** at least 3 intersections in core with valid coordinates  
**When** `GET /intersections` is called  
**Then** response contains `count` >= 3  
**And** each item includes `intersection_id`, `signal_state`, `window_end`, `is_severe_bottleneck`  
**And** each item includes `location.latitude` and `location.longitude`

## Scenario: Filter bottlenecks only

**Given** one intersection with `is_severe_bottleneck = true` and two without  
**When** `GET /intersections?bottleneck_only=true`  
**Then** `count` = 1  
**And** the returned item has `is_severe_bottleneck = true`

## Scenario: Unknown intersection returns 404

**When** `GET /intersections/nonexistent-id`  
**Then** response status is 404  
**And** body matches `Error` schema
