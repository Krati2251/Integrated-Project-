# ═══════════════════════════════════════════════════════════════════
# PUSH DOCKER IMAGES TO HUB - SCRIPT
# ═══════════════════════════════════════════════════════════════════

param(
    [string]$DockerHub_Username = "krati2251",
    [string]$Tag = "v1",
    [switch]$SkipLogin = $false
)

Write-Host ""
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  PUSHING DOCKER IMAGES TO DOCKER HUB" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

# Verify Docker
$docker = docker --version 2>$null
if (-not $?) {
    Write-Host "[X] Docker not found" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Docker: $docker" -ForegroundColor Green

# Docker Hub Login
if (-not $SkipLogin) {
    Write-Host ""
    Write-Host "[*] Logging into Docker Hub..." -ForegroundColor Yellow
    docker login
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[X] Login failed" -ForegroundColor Red
        exit 1
    }
    Write-Host "[OK] Logged in successfully" -ForegroundColor Green
}

# Define images to push
$images = @(
    @{
        LocalName   = "finance-backend:latest"
        RemoteName  = "$DockerHub_Username/finance-backend:$Tag"
        Description = "Backend API (FastAPI)"
    },
    @{
        LocalName   = "finance-frontend:latest"
        RemoteName  = "$DockerHub_Username/finance-frontend:$Tag"
        Description = "Frontend Dashboard (Streamlit)"
    },
    @{
        LocalName   = "finance-quiz:latest"
        RemoteName  = "$DockerHub_Username/finance-quiz:$Tag"
        Description = "Quiz Service (Streamlit)"
    }
)

# Tag and push images
Write-Host ""
Write-Host "[*] Tagging and pushing images..." -ForegroundColor Yellow
Write-Host ""

foreach ($img in $images) {
    Write-Host "  [$($img.Description)]" -ForegroundColor Cyan
    
    # Tag
    Write-Host "    Tagging: $($img.LocalName) -> $($img.RemoteName)" -ForegroundColor Gray
    docker tag $img.LocalName $img.RemoteName
    if ($LASTEXITCODE -ne 0) {
        Write-Host "    [X] Failed to tag" -ForegroundColor Red
        continue
    }
    
    # Push
    Write-Host "    Pushing: $($img.RemoteName)..." -ForegroundColor Gray
    docker push $img.RemoteName
    if ($LASTEXITCODE -eq 0) {
        Write-Host "    [OK] Pushed successfully" -ForegroundColor Green
        Write-Host "         URL: https://hub.docker.com/r/$($img.RemoteName)" -ForegroundColor Green
    } else {
        Write-Host "    [X] Push failed" -ForegroundColor Red
    }
    Write-Host ""
}

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "[SUMMARY] Images pushed to Docker Hub" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Your images are now available at:" -ForegroundColor Cyan
foreach ($img in $images) {
    $url = "https://hub.docker.com/r/$($img.RemoteName)"
    Write-Host "  * $($img.Description)" -ForegroundColor Cyan
    Write-Host "    $url" -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "To pull and run from Docker Hub:" -ForegroundColor Green
Write-Host ""
Write-Host "docker network create finance-net" -ForegroundColor Gray
Write-Host ""
Write-Host "# Backend" -ForegroundColor Gray
Write-Host "docker run -d --name backend --network finance-net --env-file .env -p 8000:8000 $($images[0].RemoteName)" -ForegroundColor Cyan
Write-Host ""
Write-Host "# Frontend" -ForegroundColor Gray
Write-Host "docker run -d --name frontend --network finance-net -e API_BASE_URL=http://backend:8000 -p 8501:8501 $($images[1].RemoteName)" -ForegroundColor Cyan
Write-Host ""
Write-Host "# Quiz" -ForegroundColor Gray
Write-Host "docker run -d --name quiz --network finance-net -e BACKEND_API_URL=http://backend:8000 -p 8502:8501 $($images[2].RemoteName)" -ForegroundColor Cyan
Write-Host ""
