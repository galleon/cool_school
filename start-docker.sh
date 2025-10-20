#!/bin/bash

# Customer Support Docker Setup Script

echo "🚀 Starting Customer Support Application with Docker..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found! Please create it with your configuration."
    exit 1
fi

# Build and start services
echo "📦 Building and starting services..."
docker-compose up --build -d

# Wait a moment for services to start
sleep 5

echo "✅ Services started successfully!"
echo ""
echo "🌐 Application URLs:"
echo "   Frontend: http://localhost:5173"
echo "   Backend API: http://localhost:8001"
echo "   Database: localhost:5432"
echo ""
echo "📋 To view logs:"
echo "   docker-compose logs -f"
echo ""
echo "🛑 To stop services:"
echo "   docker-compose down"
echo ""
echo "🔄 To restart services:"
echo "   docker-compose restart"
