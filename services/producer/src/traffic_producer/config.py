"""Configuration for the traffic producer."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from traffic_producer.topics import TRAFFIC_EVENTS_DLQ_TOPIC, TRAFFIC_EVENTS_TOPIC


class BrokerSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BROKER_", extra="ignore")

    bootstrap_servers: str = "localhost:19092"
    topic: str = TRAFFIC_EVENTS_TOPIC
    dlq_topic: str = TRAFFIC_EVENTS_DLQ_TOPIC
    client_id: str = "traffic-producer"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PRODUCER_", extra="ignore")

    sink: str = "stdout"
    interval_seconds: float = Field(default=5.0, ge=0)
    seed: int | None = 42
    seed_csv_path: str = Field(
        default=str(
            Path(__file__).resolve().parents[3]
            / "dbt"
            / "seeds"
            / "chapeco_intersection_locations.csv"
        )
    )
    broker: BrokerSettings = Field(default_factory=BrokerSettings)
