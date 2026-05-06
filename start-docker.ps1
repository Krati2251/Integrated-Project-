# Finance Triage Agent - Docker Startup Script
# Run this script during presentation to start all services

Write-Host "🚀 Starting Finance Triage Agent Docker Containers..." -ForegroundColor Green
Write-Host ""

# Navigate to project directory
Set-Location "D:\Triage Agent Final\finance-support-triage-agent-final-streamlit-1"

# Option 1: Simple docker-compose up
Write-Host "📦 Starting with docker-compose..." -ForegroundColor Cyan
docker-compose up -d

Write-Host ""
Write-Host "⏳ Waiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Check status
Write-Host ""
Write-Host "✅ Container Status:" -ForegroundColor Green
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

Write-Host ""
Write-Host "🌐 Open in Browser:" -ForegroundColor Cyan
Write-Host "   Frontend:  http://127.0.0.1:8501" -ForegroundColor White
Write-Host "   Backend:   http://127.0.0.1:8000" -ForegroundColor White
Write-Host "   Quiz:      http://127.0.0.1:8502" -ForegroundColor White

Write-Host ""
Write-Host "✨ All services are running!" -ForegroundColor Green
