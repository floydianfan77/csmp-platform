with source as (
    select * from {{ source('raw_landing', 'traffic_signals_aggregated_stream') }}
)

select
    intersection_id,
    cast(window_end as {{ dbt.type_timestamp() }}) as window_end,
    upper(signal_state) as signal_state,
    avg_stop_duration_seconds,
    avg_vehicle_speed_kmh,
    event_count,
    cast(ingested_at as {{ dbt.type_timestamp() }}) as ingested_at
from source
