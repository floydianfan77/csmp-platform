{{ config(
    materialized='view',
    schema='staging'
) }}

with source_data as (
    select * from {{ source('flink_infrastructure', 'traffic_signals_aggregated_stream') }}
),

transformed as (
    select
        cast(intersection_id as string) as intersection_id,
        cast(upper(signal_state) as string) as current_signal_state,
        cast(avg_stop_duration as numeric) as avg_stop_duration_seconds,
        cast(avg_vehicle_speed as numeric) as avg_vehicle_speed_kmh,
        cast(window_start as timestamp) as window_start_at,
        cast(window_end as timestamp) as window_end_at,
        current_timestamp() as dbt_processed_at
    from source_data
)

select * from transformed