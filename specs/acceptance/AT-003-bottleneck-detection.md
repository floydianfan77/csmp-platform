# AT-003 — Bottleneck detection (FR-004)

**Requirement:** `is_severe_bottleneck = true` iff stop > 75s AND speed < 5 km/h

## Scenario: Severe bottleneck flagged

**Given** a core row with:
  - `avg_stop_duration_seconds = 80.0`
  - `avg_vehicle_speed_kmh = 3.0`  
**When** dbt core model runs  
**Then** `is_severe_bottleneck` is `true`

## Scenario: High stop alone is not severe

**Given** `avg_stop_duration_seconds = 90.0` and `avg_vehicle_speed_kmh = 15.0`  
**Then** `is_severe_bottleneck` is `false`

## Scenario: Low speed alone is not severe

**Given** `avg_stop_duration_seconds = 30.0` and `avg_vehicle_speed_kmh = 2.0`  
**Then** `is_severe_bottleneck` is `false`

## Scenario: Boundary values

**Given** `avg_stop_duration_seconds = 75.0` and `avg_vehicle_speed_kmh = 5.0`  
**Then** `is_severe_bottleneck` is `false` (strict inequalities in FR-004)
