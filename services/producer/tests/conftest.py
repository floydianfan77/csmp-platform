from pathlib import Path

import pytest

SEED_CSV = (
    Path(__file__).resolve().parents[2]
    / "dbt"
    / "seeds"
    / "chapeco_intersection_locations.csv"
)


@pytest.fixture
def seed_csv_path() -> Path:
    return SEED_CSV
