#!/bin/bash

# License Plate Detection Service - Deployment Script

set -e

echo "🚀 Deploying License Plate Detection Service..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p uploads outputs logs

# Check if model file exists
if [ ! -f "license_plate_best.pt" ]; then
    echo "⚠️  Warning: license_plate_best.pt not found. Make sure it exists before running."
fi

# Build and start services
echo "🔨 Building Docker image..."
docker-compose build

echo "🚀 Starting services..."
docker-compose up -d

echo "⏳ Waiting for service to be ready..."
sleep 10

# Check health
echo "🏥 Checking service health..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Service is healthy and running!"
    echo ""
    echo "📋 Service Information:"
    echo "   - API URL: http://localhost:8000"
    echo "   - API Docs: http://localhost:8000/docs"
    echo "   - Health Check: http://localhost:8000/health"
    echo ""
    echo "📊 View logs: docker-compose logs -f"
    echo "🛑 Stop service: docker-compose down"
else
    echo "⚠️  Service may still be starting. Check logs with: docker-compose logs"
fi

