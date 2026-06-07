# AT-006 — Monitor UI (Phase 6)

**Requirements:** OQ-1 (map UI), OQ-3 (pt-BR user-facing copy)

## Scenario: Map shows intersections from API

**Given** monitor API is running with at least one intersection in core  
**When** the user opens `/app/`  
**Then** a Leaflet map is displayed centered on Chapecó  
**And** markers appear for intersections with coordinates  
**And** copy is in Portuguese (pt-BR)

## Scenario: Bottleneck is visually highlighted

**Given** at least one intersection with `is_severe_bottleneck = true`  
**When** the map loads  
**Then** that intersection has a distinct bottleneck marker style  
**And** the sidebar shows a "Gargalo" tag

## Scenario: Filter bottlenecks only

**Given** mixed bottleneck and normal intersections  
**When** the user enables "Somente gargalos severos"  
**Then** only bottleneck intersections are listed and shown on the map
