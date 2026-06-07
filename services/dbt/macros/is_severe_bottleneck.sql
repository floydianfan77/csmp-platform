{% macro is_severe_bottleneck(stop_duration_col, vehicle_speed_col) %}
    ({{ stop_duration_col }} > 75.0 and {{ vehicle_speed_col }} < 5.0)
{% endmacro %}
