# AT-002 — Stream aggregation (FR-002)

**Contract:** `contracts/warehouse/traffic_signals_aggregated_stream.yml`

## Scenario: One-minute window produces correct grain

**Given** events for `intersection_id = osm-test-1` spanning two distinct 1-minute windows  
**When** the Flink job processes them with event-time tumbling windows  
**Then** landing table contains exactly **2** rows for `osm-test-1`  
**And** each row has unique `(intersection_id, window_end)`  
**And** `event_count` >= 1 per row

## Scenario: Signal state uses last event in window

**Given** in the same 1-minute window for one intersection:
  - t=0s: `RED`
  - t=30s: `GREEN`
  - t=50s: `RED`  
**When** the window closes  
**Then** `signal_state` = `RED` (last by `environment.timestamp`)  
**And** `signal_state` is NOT derived from `MAX(signal_state)` lexicographic order

## Scenario: Column mapping matches contract

**Given** a known input event with fixed metrics  
**When** written to landing  
**Then** Flink INSERT column order matches DDL in warehouse contract  
**And** `avg_stop_duration_seconds` and `avg_vehicle_speed_kmh` are not swapped
