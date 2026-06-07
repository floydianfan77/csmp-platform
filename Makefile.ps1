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
    Write-Host "  aggregate         Kafka -> SQLite landing (needs broker + messages)"
    Write-Host "  test-all          Contract + producer + flink batch + acceptance"
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
        csmp-flink-job --mode stream --max-messages 20 --landing-db "$Root\data\landing.db"
    }
    "test-acceptance" {
        Set-Location $Root
        pytest tests/acceptance -v -m integration
    }
    "test-all" {
        Set-Location $Root
        pytest tests/contract services/producer/tests -v
        pytest services/flink-job/tests/test_at002_window.py -v
        pytest tests/acceptance -v -m integration
    }
    "producer" {
        Set-Location $Root
        traffic-producer --sink broker --bootstrap-servers localhost:19092 --max-batches 1
    }
    default {
        Write-Error "Unknown target: $Target"
        exit 1
    }
}
