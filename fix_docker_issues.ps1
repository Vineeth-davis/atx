# Fix Docker Issues Script for Windows
# This script addresses the ODBC driver and import issues

Write-Host "🔧 Fixing Docker Issues for Atrean RAG Platform" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green

# Stop existing containers
Write-Host "📦 Stopping existing containers..." -ForegroundColor Yellow
docker-compose down

# Remove old images to force rebuild
Write-Host "🗑️ Removing old images..." -ForegroundColor Yellow
docker-compose down --rmi all

# Rebuild containers with updated Dockerfile
Write-Host "🔨 Rebuilding containers with ODBC drivers..." -ForegroundColor Yellow
docker-compose build --no-cache

# Start containers
Write-Host "🚀 Starting containers..." -ForegroundColor Yellow
docker-compose up -d

# Wait for services to be ready
Write-Host "⏳ Waiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Check container status
Write-Host "📊 Container status:" -ForegroundColor Cyan
docker-compose ps

# Check logs for any remaining issues
Write-Host "📋 Recent logs from app container:" -ForegroundColor Cyan
docker-compose logs --tail=20 app

Write-Host "📋 Recent logs from streamlit container:" -ForegroundColor Cyan
docker-compose logs --tail=20 streamlit

Write-Host ""
Write-Host "✅ Docker fixes applied!" -ForegroundColor Green
Write-Host "🌐 Streamlit UI should be available at: http://localhost:8501" -ForegroundColor Blue
Write-Host "🔗 API should be available at: http://localhost:8000" -ForegroundColor Blue
Write-Host ""
Write-Host "If you still see issues, check the logs with:" -ForegroundColor Yellow
Write-Host "  docker-compose logs -f" -ForegroundColor Gray