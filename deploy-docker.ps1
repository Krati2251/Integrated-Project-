# FINANCE TRIAGE AGENT - DOCKER DEPLOYMENT SCRIPT

param(
    [string]$Action = "start",
    [switch]$Rebuild = $false,
    [switch]$CleanUp = $false,
    [switch]$Logs = $false
)

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host ""
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  FINANCE SUPPORT TRIAGE AGENT - DOCKER DEPLOYMENT" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

# Function: Check Docker
function Test-Docker {
    $docker = docker --version 2>$null
    if (-not $?) {
        Write-Host "[X] Docker is not installed or not in PATH" -ForegroundColor Red
        Write-Host "[!] Install Docker Desktop: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
        exit 1
    }
    Write-Host "[OK] Docker found: $docker" -ForegroundColor Green
}

# Function: Clean up
function Clean-Containers {
    Write-Host ""
    Write-Host "[*] Cleaning up existing containers..." -ForegroundColor Yellow
    docker-compose down --remove-orphans 2>$null
    Write-Host "[OK] Cleanup complete" -ForegroundColor Green
}

# Function: Build images
function Build-Images {
    Write-Host ""
    Write-Host "[*] Building Docker images..." -ForegroundColor Yellow
    Set-Location $ProjectRoot
    
    $images = @("backend", "frontend", "quiz")
    foreach ($img in $images) {
        Write-Host "  -> Building $img..." -ForegroundColor Cyan
        docker-compose build $img
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[X] Failed to build $img" -ForegroundColor Red
            exit 1
        }
    }
    Write-Host "[OK] All images built successfully" -ForegroundColor Green
}

# Function: Start services
function Start-Services {
    Write-Host ""
    Write-Host "[*] Starting services..." -ForegroundColor Yellow
    Set-Location $ProjectRoot
    
    docker-compose up -d
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Services started" -ForegroundColor Green
        Start-Sleep -Seconds 5
        Show-ServiceStatus
    } else {
        Write-Host "[X] Failed to start services" -ForegroundColor Red
        exit 1
    }
}

# Function: Stop services
function Stop-Services {
    Write-Host ""
    Write-Host "[*] Stopping services..." -ForegroundColor Yellow
    Set-Location $ProjectRoot
    
    docker-compose down
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Services stopped" -ForegroundColor Green
    } else {
        Write-Host "[X] Failed to stop services" -ForegroundColor Red
        exit 1
    }
}

# Function: Show status
function Show-ServiceStatus {
    Write-Host ""
    Write-Host "[INFO] Service Status:" -ForegroundColor Cyan
    Write-Host "--------" -ForegroundColor DarkGray
    
    $status = docker-compose ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    Write-Host $status
    
    Write-Host ""
    Write-Host "[URLS] Access URLs:" -ForegroundColor Green
    Write-Host "  * Frontend (Dashboard):  http://localhost:8501" -ForegroundColor Cyan
    Write-Host "  * Backend (API):         http://localhost:8000" -ForegroundColor Cyan
    Write-Host "  * Quiz Service:          http://localhost:8502" -ForegroundColor Cyan
    Write-Host "  * API Docs:              http://localhost:8000/docs" -ForegroundColor Cyan
    
    Write-Host ""
    Write-Host "[TIP] Run '.\deploy-docker.ps1 -Action logs' to see live logs" -ForegroundColor Yellow
}

# Function: Show logs
function Show-Logs {
    param([string]$Service = "")
    
    Write-Host ""
    Write-Host "[LOGS] Container Logs (Press Ctrl+C to exit):" -ForegroundColor Cyan
    Set-Location $ProjectRoot
    
    if ($Service) {
        docker-compose logs -f $Service
    } else {
        docker-compose logs -f
    }
}

# Function: Health check
function Test-Health {
    Write-Host ""
    Write-Host "[HEALTH] Running health checks..." -ForegroundColor Yellow
    
    $services = @(
        @{Name="Backend"; URL="http://localhost:8000"; Port=8000}
        @{Name="Frontend"; URL="http://localhost:8501"; Port=8501}
        @{Name="Quiz"; URL="http://localhost:8502"; Port=8502}
    )
    
    foreach ($svc in $services) {
        try {
            $response = Invoke-WebRequest -Uri $svc.URL -UseBasicParsing -TimeoutSec 3
            if ($response.StatusCode -eq 200) {
                Write-Host "  [OK] $($svc.Name) is running (Port $($svc.Port))" -ForegroundColor Green
            }
        } catch {
            Write-Host "  [!] $($svc.Name) is not responding (Port $($svc.Port))" -ForegroundColor Yellow
        }
    }
}


# Main logic
Test-Docker

switch ($Action.ToLower()) {
    "start" {
        if ($Rebuild) {
            Clean-Containers
            Build-Images
        }
        Start-Services
        Test-Health
    }
    "stop" {
        Stop-Services
    }
    "restart" {
        Stop-Services
        Start-Sleep -Seconds 2
        Start-Services
        Test-Health
    }
    "build" {
        Build-Images
    }
    "logs" {
        Show-Logs
    }
    "status" {
        Show-ServiceStatus
        Test-Health
    }
    "clean" {
        Clean-Containers
        Write-Host "[OK] All containers removed" -ForegroundColor Green
    }
    default {
        Write-Host ""
        Write-Host "[USAGE] Commands:" -ForegroundColor Cyan
        Write-Host "  .\deploy-docker.ps1 -Action start              # Start all services"
        Write-Host "  .\deploy-docker.ps1 -Action start -Rebuild    # Rebuild images and start"
        Write-Host "  .\deploy-docker.ps1 -Action stop               # Stop all services"
        Write-Host "  .\deploy-docker.ps1 -Action restart            # Restart all services"
        Write-Host "  .\deploy-docker.ps1 -Action build              # Build images only"
        Write-Host "  .\deploy-docker.ps1 -Action logs               # Show live logs"
        Write-Host "  .\deploy-docker.ps1 -Action status             # Show service status"
        Write-Host "  .\deploy-docker.ps1 -Action clean              # Clean up containers"
        Write-Host ""
    }
}

Write-Host ""
