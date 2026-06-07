{{ config(
    materialized='incremental',
    incremental_strategy='merge',
    unique_key=['intersection_id', 'window_slice_date'],
    partition_by={
      "field": "window_slice_date",
      "data_type": "date",
      "granularity": "day"
    },
    cluster_by=['current_signal_state', 'intersection_id'],
    schema='core'
) }}

with staging_metrics as (
    select * from {{ ref('stg_traffic_signals') }}
    {% if is_incremental() %}
    where window_end_at >= timestamp_sub(_dbt_max_partition, interval 2 day)
    {% endif %}
),

-- Static Asset Location Seed Join for Spatial Mapping
static_osm_coordinates as (
    select * from {{ ref('seed_chapeco_intersection_locations') }}
),

joined_and_enriched as (
    select
        m.intersection_id,
        c.intersection_name,
        m.current_signal_state,
        m.avg_stop_duration_seconds,
        m.avg_vehicle_speed_kmh,
        m.window_end_at,
        extract(date from m.window_end_at) as window_slice_date,
        
        -- BigQuery Native GIS primitive instantiation
        st_geogpoint(c.longitude, c.latitude) as spatial_geography_point,

        -- Advanced Bottleneck Scoring Flag
        case 
            when m.avg_stop_duration_seconds > 75.0 and m.avg_vehicle_speed_kmh < 5.0 then true
            else false
        end as is_severe_bottleneck

    from staging_metrics m
    inner join static_osm_coordinates c on m.intersection_id = c.intersection_id
)

select * from joined_and_enriched