from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table import StreamTableEnvironment

def init_mobility_streaming_pipeline():
    env = StreamExecutionEnvironment.get_execution_environment()
    env.get_checkpoint_config().set_checkpoint_interval(15000) # Checkpoint state every 15s
    t_env = StreamTableEnvironment.create(env)
    
    t_env.get_config().get_configuration().set_string(
        "pipeline.jars",
        "file:///opt/flink/plugins/flink-sql-connector-kafka-3.1.0.jar;"
        "file:///opt/flink/plugins/flink-bigquery-connector-1.3.0.jar"
    )

    # Source: Redpanda Stream
    t_env.execute_sql("""
        CREATE TABLE source_traffic_stream (
            intersection_id STRING,
            telemetry ROW<current_signal_state STRING, measured_stop_duration_seconds DOUBLE, observed_vehicle_speed_kmh DOUBLE, sensor_gap_triggered_override BOOLEAN>,
            environment ROW<is_peak_hour_cycle BOOLEAN, macro_cycle_setting_seconds INT, timestamp STRING>,
            event_timestamp AS TO_TIMESTAMP(REPLACE(environment.timestamp, 'T', ' '), 'yyyy-MM-dd HH:mm:ss.SSS'),
            WATERMARK FOR event_timestamp AS event_timestamp - INTERVAL '10' SECOND
        ) WITH (
            'connector' = 'kafka',
            'topic' = 'chapeco-traffic-events',
            'properties.bootstrap.servers' = 'redpanda:9092',
            'properties.group.id' = 'chapeco_flink_analytics_v1',
            'format' = 'json'
        )
    """)

    # Sink: Google BigQuery Landing Zone
    t_env.execute_sql("""
        CREATE TABLE sink_bigquery_mobility (
            intersection_id STRING,
            signal_state STRING,
            avg_stop_duration DOUBLE,
            avg_vehicle_speed DOUBLE,
            window_start TIMESTAMP(3),
            window_end TIMESTAMP(3)
        ) WITH (
            'connector' = 'bigquery',
            'project' = 'chapeco-smart-mobility',
            'dataset' = 'stg_raw_landing',
            'table' = 'traffic_signals_aggregated_stream',
            'credentials-file' = '/etc/gcp/service_account_key.json',
            'delivery-guarantee' = 'at-least-once'
        )
    """)

    # Windowed Processing & Aggregation Logic (1-Minute Tumbling Windows)
    t_env.execute_sql("""
        INSERT INTO sink_bigquery_mobility
        SELECT 
            intersection_id,
            TUMBLE_START(event_timestamp, INTERVAL '1' MINUTE) as window_start,
            TUMBLE_END(event_timestamp, INTERVAL '1' MINUTE) as window_end,
            MAX(telemetry.current_signal_state) as signal_state,
            AVG(telemetry.measured_stop_duration_seconds) as avg_stop_duration,
            AVG(telemetry.observed_vehicle_speed_kmh) as avg_vehicle_speed
        FROM source_traffic_stream
        GROUP BY 
            intersection_id, 
            TUMBLE(event_timestamp, INTERVAL '1' MINUTE)
    """)

if __name__ == "__main__":
    init_mobility_streaming_pipeline()