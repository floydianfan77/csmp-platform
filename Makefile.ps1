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
    Write-Host "  warehouse         landing.db -> csmp.duckdb (required before monitor-api)"
    Write-Host "  monitor-api       Build warehouse if needed, run API on :8000"
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
    "warehouse" {
        Set-Location $Root
        $env:PYTHONPATH = (Join-Path $Root "services\dbt")
        python (Join-Path $Root "services\dbt\local\build_warehouse.py")
    }
    "monitor-api" {
        Set-Location $Root
        if (-not (Get-Command csmp-monitor-api -ErrorAction SilentlyContinue)) {
            pip install -e (Join-Path $Root "services\monitor-api") -q
        }
        $DuckDb = Join-Path $Root "data\csmp.duckdb"
        $LandingDb = Join-Path $Root "data\landing.db"
        if (-not (Test-Path $DuckDb)) {
            if (-not (Test-Path $LandingDb)) {
                Write-Error "No data yet. Run: .\Makefile.ps1 producer then aggregate (or demo)"
                exit 1
            }
            Write-Host "[monitor-api] building warehouse from landing.db ..."
            & $PSCommandPath warehouse
        }
        $env:CSMP_MONITOR_DUCKDB_PATH = $DuckDb
        Write-Host "[monitor-api] http://127.0.0.1:8000/docs  (Ctrl+C to stop)"
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
        & $PSCommandPath warehouse
        Write-Host "[demo] ready. Run: .\Makefile.ps1 monitor-api"
    }
    default {
        Write-Error "Unknown target: $Target"
        exit 1
    }
}
