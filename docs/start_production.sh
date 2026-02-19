#!/bin/bash

# Quick start script for production environment

echo "========================================="
echo "  Coding Agent - Production Setup"
echo "========================================="
echo ""

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

echo "✓ Docker and Docker Compose are installed"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "✓ Created .env file"
    echo "⚠️  Please edit .env and add your API keys before continuing"
    echo ""
    read -p "Press Enter after editing .env file..."
fi

echo "Starting services..."
echo ""

# Start Docker Compose
docker-compose up -d

echo ""
echo "Waiting for services to be ready..."
sleep 10

# Check health
echo ""
echo "Checking API health..."
if curl -s http://localhost:8000/api/v1/health > /dev/null; then
    echo "✓ API is healthy"
else
    echo "⚠️  API health check failed. Check logs with: docker-compose logs api"
fi

echo ""
echo "========================================="
echo "  Services Started Successfully!"
echo "========================================="
echo ""
echo "Access the following URLs:"
echo ""
echo "  API:           http://localhost:8000"
echo "  API Docs:      http://localhost:8000/docs"
echo "  Memgraph Lab:  http://localhost:3000"
echo "  Jaeger:        http://localhost:16686"
echo "  Flower:        http://localhost:5555"
echo "  RabbitMQ:      http://localhost:15672 (guest/guest)"
echo ""
echo "To view logs:    docker-compose logs -f"
echo "To stop:         docker-compose down"
echo ""
echo "Read PRODUCTION_ENHANCEMENTS.md for usage examples"
echo ""
