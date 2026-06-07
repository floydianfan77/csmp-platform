"""Flink job settings."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="FLINK_", extra="ignore")

    bootstrap_servers: str = "localhost:19092"
    source_topic: str = "chapeco-traffic-events"
    consumer_group: str = "csmp-flink-job"
    watermark_seconds: int = Field(default=10, ge=0)
    landing_db_path: str = "./data/landing.db"
    checkpoint_ms: int = Field(default=15000, ge=1000)
