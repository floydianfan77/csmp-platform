"""FR-002: Warehouse landing contract synced to dbt sources."""

from __future__ import annotations

from tests.contract.conftest import (
    DBT_SOURCES_PATH,
    LANDING_COLUMN_ORDER,
    WAREHOUSE_CONTRACT_PATH,
    load_yaml,
)


def _table_columns(doc: dict, source_name: str, table_name: str) -> list[str]:
    for source in doc["sources"]:
        if source["name"] != source_name:
            continue
        for table in source["tables"]:
            if table["name"] == table_name:
                return [col["name"] for col in table["columns"]]
    raise KeyError(f"{source_name}.{table_name} not found")


def test_dbt_sources_file_exists():
    assert DBT_SOURCES_PATH.is_file()


def test_dbt_sources_match_warehouse_contract():
    contract = load_yaml(WAREHOUSE_CONTRACT_PATH)
    dbt_sources = load_yaml(DBT_SOURCES_PATH)
    contract_cols = _table_columns(
        contract, "raw_landing", "traffic_signals_aggregated_stream"
    )
    dbt_cols = _table_columns(dbt_sources, "raw_landing", "traffic_signals_aggregated_stream")
    assert contract_cols == dbt_cols


def test_landing_column_order_matches_flink_ddl():
    contract = load_yaml(WAREHOUSE_CONTRACT_PATH)
    contract_cols = _table_columns(
        contract, "raw_landing", "traffic_signals_aggregated_stream"
    )
    assert contract_cols == LANDING_COLUMN_ORDER


def test_unique_grain_test_defined():
    dbt_sources = load_yaml(DBT_SOURCES_PATH)
    for source in dbt_sources["sources"]:
        if source["name"] != "raw_landing":
            continue
        for table in source["tables"]:
            if table["name"] == "traffic_signals_aggregated_stream":
                tests = table.get("tests", [])
                assert any(
                    "unique_combination_of_columns" in str(t) for t in tests
                ), "Grain test missing on landing table"
                return
    raise AssertionError("traffic_signals_aggregated_stream not found")
