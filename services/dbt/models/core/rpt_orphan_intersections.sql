{{ config(materialized='view') }}

select
    staged.intersection_id,
    count(*) as orphan_row_count,
    min(staged.window_end) as first_seen_window,
    max(staged.window_end) as last_seen_window
from {{ ref('stg_traffic_signals') }} as staged
left join {{ ref('chapeco_intersection_locations') }} as seed
    on staged.intersection_id = seed.intersection_id
where seed.intersection_id is null
group by staged.intersection_id
