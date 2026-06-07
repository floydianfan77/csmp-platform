FROM python:3.12-slim

WORKDIR /app

COPY services/producer/pyproject.toml services/producer/README.md ./
COPY services/producer/src ./src
COPY services/dbt/seeds/chapeco_intersection_locations.csv ./seeds/

RUN pip install --no-cache-dir -e ".[broker]"

ENV PRODUCER_SEED_CSV_PATH=/app/seeds/chapeco_intersection_locations.csv

CMD ["traffic-producer", "--sink", "broker", "--interval", "5"]
