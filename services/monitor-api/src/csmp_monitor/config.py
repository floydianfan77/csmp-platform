from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CSMP_MONITOR_")

    duckdb_path: str = "data/csmp.duckdb"
    freshness_threshold_seconds: float = 120.0


settings = Settings()
