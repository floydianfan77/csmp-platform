from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_DEFAULT_SEED = (
    Path(__file__).resolve().parents[3]
    / "dbt"
    / "seeds"
    / "chapeco_intersection_locations.csv"
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CSMP_MONITOR_")

    duckdb_path: str = "data/csmp.duckdb"
    seed_csv_path: str = str(_DEFAULT_SEED)
    freshness_threshold_seconds: float = 120.0


settings = Settings()
