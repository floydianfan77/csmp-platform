# AT-005 — Spatial enrichment (FR-005)

**Contract:** `contracts/seeds/chapeco_intersection_locations.v1.schema.json`

## Scenario: Known intersection gets geography

**Given** seed row for `intersection_id = osm-123456789` with lat/lon in Chapecó  
**And** landing aggregate for the same `intersection_id`  
**When** dbt core model runs  
**Then** `spatial_geography_point` is not null  
**And** ST_X/ST_Y or equivalent matches seed within 1e-6 degrees

## Scenario: Orphan intersection is reported

**Given** landing aggregate for `intersection_id = unknown-999` with no seed row  
**When** dbt runs  
**Then** `unknown-999` appears in data quality model `rpt_orphan_intersections`  
**And** it is not silently dropped from monitoring without trace
