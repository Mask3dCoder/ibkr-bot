#!/usr/bin/env pwsh
# Installation and Setup Script for IBKR Trading Platform
# Run this script to set up the complete development environment

param(
    [switch]$SkipVenv,
    [switch]$SkipDocker,
    [switch]$Production
)

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "IBKR Institutional Trading Platform - Setup Script" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

# Check Python version
Write-Host "Checking Python version..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($pythonVersion -match "Python 3\.1[2-9]") {
    Write-Host "✓ Python version OK: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "✗ Python 3.12+ required, found: $pythonVersion" -ForegroundColor Red
    exit 1
}

# Create virtual environment
if (-not $SkipVenv) {
    Write-Host "`nCreating virtual environment..." -ForegroundColor Yellow
    if (Test-Path "venv") {
        Write-Host "Virtual environment already exists, skipping..." -ForegroundColor Gray
    } else {
        python -m venv venv
        Write-Host "✓ Virtual environment created" -ForegroundColor Green
    }
    
    # Activate virtual environment
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & .\venv\Scripts\Activate.ps1
    Write-Host "✓ Virtual environment activated" -ForegroundColor Green
}

# Upgrade pip
Write-Host "`nUpgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip wheel setuptools
Write-Host "✓ pip upgraded" -ForegroundColor Green

# Install dependencies
Write-Host "`nInstalling dependencies..." -ForegroundColor Yellow
pip install -e .
Write-Host "✓ Dependencies installed" -ForegroundColor Green

# Install development dependencies
if (-not $Production) {
    Write-Host "`nInstalling development dependencies..." -ForegroundColor Yellow
    pip install -e ".[dev]"
    Write-Host "✓ Development dependencies installed" -ForegroundColor Green
}

# Create necessary directories
Write-Host "`nCreating directory structure..." -ForegroundColor Yellow
$dirs = @(
    "logs",
    "data",
    "config/strategies",
    "monitoring/grafana/dashboards",
    "monitoring/grafana/datasources",
    "docs/architecture",
    "docs/operations"
)

foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "  Created: $dir" -ForegroundColor Gray
    }
}
Write-Host "✓ Directories created" -ForegroundColor Green

# Copy environment template
Write-Host "`nSetting up environment configuration..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Copy-Item ".env.template" ".env"
    Write-Host "✓ Created .env from template" -ForegroundColor Green
    Write-Host "⚠  IMPORTANT: Edit .env with your configuration!" -ForegroundColor Yellow
} else {
    Write-Host ".env already exists, skipping..." -ForegroundColor Gray
}

# Start Docker services
if (-not $SkipDocker) {
    Write-Host "`nStarting Docker services..." -ForegroundColor Yellow
    try {
        docker-compose up -d
        Write-Host "✓ Docker services started" -ForegroundColor Green
        
        # Wait for services to be healthy
        Write-Host "`nWaiting for services to be healthy..." -ForegroundColor Yellow
        Start-Sleep -Seconds 10
        
        $services = docker-compose ps --services
        Write-Host "✓ Services running:" -ForegroundColor Green
        docker-compose ps | Write-Host
    } catch {
        Write-Host "✗ Failed to start Docker services: $_" -ForegroundColor Red
        Write-Host "Make sure Docker Desktop is running" -ForegroundColor Yellow
    }
}

# Run tests
if (-not $Production) {
    Write-Host "`nRunning tests..." -ForegroundColor Yellow
    try {
        pytest tests/unit -v --tb=short
        Write-Host "✓ Tests passed" -ForegroundColor Green
    } catch {
        Write-Host "⚠  Some tests failed - please review" -ForegroundColor Yellow
    }
}

# Summary
Write-Host "`n" + ("=" * 80) -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host ("=" * 80) -ForegroundColor Cyan
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "1. Edit .env with your IBKR credentials and configuration" -ForegroundColor White
Write-Host "2. Review config/main_config.yaml and adjust settings" -ForegroundColor White
Write-Host "3. Start IBKR TWS or Gateway (paper trading port 7497)" -ForegroundColor White
Write-Host "4. Run paper trading: python scripts/run_paper.py" -ForegroundColor White
Write-Host "`n⚠️  CRITICAL WARNINGS:" -ForegroundColor Red
Write-Host "- NEVER run production mode without 30+ days paper trading" -ForegroundColor Red
Write-Host "- Read docs/safety/CRITICAL_WARNINGS.md before deploying" -ForegroundColor Red
Write-Host "- Start with MINIMUM position sizes" -ForegroundColor Red
Write-Host "- Monitor continuously during initial deployment" -ForegroundColor Red
Write-Host "`nDocumentation:" -ForegroundColor Yellow
Write-Host "- README.md - System overview and quick start" -ForegroundColor White
Write-Host "- Implementation plan - Complete architecture" -ForegroundColor White
Write-Host "- Walkthrough - Module implementations" -ForegroundColor White
Write-Host "- docs/safety/CRITICAL_WARNINGS.md - Safety requirements" -ForegroundColor White
Write-Host "`nMonitoring URLs (once running):" -ForegroundColor Yellow
Write-Host "- Prometheus: http://localhost:9090" -ForegroundColor White
Write-Host "- Grafana: http://localhost:3000 (admin/admin)" -ForegroundColor White
Write-Host "- Platform Metrics: http://localhost:9090/metrics" -ForegroundColor White
Write-Host "`n" + ("=" * 80) -ForegroundColor Cyan
