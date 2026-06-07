# 1. Boot Environment
docker compose up -d --build

# 2. Trigger stream ingestion execution inside container task slots
docker exec -d csmp_flink_coordinator flink run -py /app/stream_processing_job.py

# 3. Test and run dbt batch assets
dbt deps && dbt test
dbt build --target prod --profiles-dir ./config