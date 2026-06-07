{{ config(materialized='table') }}

with staged as (
    select * from {{ ref('stg_traffic_signals') }}
),

seed as (
    select * from {{ ref('chapeco_intersection_locations') }}
),

enriched as (
    select
        staged.intersection_id,
        seed.display_name,
        staged.window_end,
        staged.signal_state,
        staged.avg_stop_duration_seconds,
        staged.avg_vehicle_speed_kmh,
        staged.event_count,
        staged.ingested_at,
        seed.latitude,
        seed.longitude,
        {{ is_severe_bottleneck(
            'staged.avg_stop_duration_seconds',
            'staged.avg_vehicle_speed_kmh'
        ) }} as is_severe_bottleneck
    from staged
    left join seed
        on staged.intersection_id = seed.intersection_id
)

select
    intersection_id,
    display_name,
    window_end,
    signal_state,
    avg_stop_duration_seconds,
    avg_vehicle_speed_kmh,
    event_count,
    ingested_at,
    is_severe_bottleneck,
    latitude,
    longitude,
    {% if target.type == 'duckdb' %}
        case
            when latitude is not null and longitude is not null
            then st_point(longitude, latitude)
        end as spatial_geography_point
    {% else %}
        st_geogpoint(longitude, latitude) as spatial_geography_point
    {% endif %}
from enriched
