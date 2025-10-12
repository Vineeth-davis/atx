#!/bin/bash

# Fix Docker Issues Script
# This script addresses the ODBC driver and import issues

echo "🔧 Fixing Docker Issues for Atrean RAG Platform"
echo "================================================"

# Stop existing containers
echo "📦 Stopping existing containers..."
docker-compose down

# Remove old images to force rebuild
echo "🗑️ Removing old images..."
docker-compose down --rmi all

# Rebuild containers with updated Dockerfile
echo "🔨 Rebuilding containers with ODBC drivers..."
docker-compose build --no-cache

# Start containers
echo "🚀 Starting containers..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check container status
echo "📊 Container status:"
docker-compose ps

# Check logs for any remaining issues
echo "📋 Recent logs from app container:"
docker-compose logs --tail=20 app

echo "📋 Recent logs from streamlit container:"
docker-compose logs --tail=20 streamlit

echo ""
echo "✅ Docker fixes applied!"
echo "🌐 Streamlit UI should be available at: http://localhost:8501"
echo "🔗 API should be available at: http://localhost:8000"
echo ""
echo "If you still see issues, check the logs with:"
echo "  docker-compose logs -f"
