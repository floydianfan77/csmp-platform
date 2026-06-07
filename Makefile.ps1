# CSMP dev commands (Windows-friendly)
# Usage: .\Makefile.ps1 help

param(
    [Parameter(Position = 0)]
    [string]$Target = "help"
)

$Root = $PSScriptRoot
$ComposeFile = Join-Path $Root "infra\docker-compose.yml"

function Show-Help {
    Write-Host "  install-dev      Install root dev dependencies"
    Write-Host "  install-producer Install producer service (editable + broker)"
    Write-Host "  broker-up        Start Redpanda + console (docker compose)"
    Write-Host "  broker-down      Stop Redpanda stack"
    Write-Host "  test-contract    Phase 1 contract tests"
    Write-Host "  test-producer    Producer unit tests"
    Write-Host "  test-acceptance  AT-001 (needs broker-up)"
    Write-Host "  test-flink        PyFlink AT-002 batch tests (needs Java)"
    Write-Host "  test-warehouse    AT-003 + AT-005 (DuckDB local dbt pipeline)"
    Write-Host "  install-monitor   Install monitor API service"
    Write-Host "  test-monitor      AT-004 monitor API tests"
    Write-Host "  monitor-api       Run monitor API on :8000"
    Write-Host "  aggregate         Kafka -> SQLite landing (drain topic, ~3s)"
    Write-Host "  demo              broker-up + producer + aggregate + warehouse"
    Write-Host "  test-all          Contract + producer + flink + warehouse + acceptance"
    Write-Host "  producer         Run simulator to broker (1 batch)"
}

switch ($Target) {
    "help" { Show-Help }
    "install-dev" {
        Set-Location $Root
        pip install -e ".[dev]"
    }
    "install-producer" {
        Set-Location (Join-Path $Root "services\producer")
        pip install -e ".[broker,dev]"
    }
    "broker-up" {
        docker compose -f $ComposeFile up -d
    }
    "broker-down" {
        docker compose -f $ComposeFile down
    }
    "test-contract" {
        Set-Location $Root
        pytest tests/contract -v
    }
    "test-producer" {
        Set-Location $Root
        pytest services/producer/tests -v
    }
    "test-flink" {
        Set-Location $Root
        pytest services/flink-job/tests/test_at002_window.py -v
    }
    "aggregate" {
        Set-Location $Root
        csmp-flink-job --mode stream --from-earliest --idle-seconds 2 --landing-db "$Root\data\landing.db"
    }
    "test-warehouse" {
        Set-Location $Root
        pytest tests/acceptance/test_at003_bottleneck.py tests/acceptance/test_at005_spatial.py -v
    }
    "install-monitor" {
        Set-Location (Join-Path $Root "services\monitor-api")
        pip install -e ".[dev]"
    }
    "test-monitor" {
        Set-Location $Root
        pytest tests/acceptance/test_at004_monitor_api.py -v
    }
    "monitor-api" {
        Set-Location $Root
        csmp-monitor-api
    }
    "test-acceptance" {
        Set-Location $Root
        pytest tests/acceptance -v -m integration
    }
    "test-all" {
        Set-Location $Root
        pytest tests/contract services/producer/tests -v
        pytest services/flink-job/tests/test_at002_window.py -v
        pytest tests/acceptance/test_at003_bottleneck.py tests/acceptance/test_at005_spatial.py -v
        pytest tests/acceptance/test_at004_monitor_api.py -v
        pytest tests/acceptance -v -m integration
    }
    "producer" {
        Set-Location $Root
        traffic-producer --sink broker --bootstrap-servers localhost:19092 --max-batches 1
    }
    "demo" {
        Set-Location $Root
        docker compose -f $ComposeFile up -d
        traffic-producer --sink broker --bootstrap-servers localhost:19092 --max-batches 1
        csmp-flink-job --mode stream --from-earliest --idle-seconds 2 --landing-db "$Root\data\landing.db"
        python -c "from pathlib import Path; from local.engine import run_pipeline; run_pipeline(landing_db=Path(r'$Root\data\landing.db'), seed_csv=Path(r'$Root\services\dbt\seeds\chapeco_intersection_locations.csv'), duckdb_path=Path(r'$Root\data\csmp.duckdb'))"
        Write-Host "[demo] landing.db + csmp.duckdb ready. Run: .\Makefile.ps1 monitor-api"
    }
    default {
        Write-Error "Unknown target: $Target"
        exit 1
    }
}
