#!/bin/bash

# Australian Customs Declaration Backend Startup Script

echo "🚀 Starting Australian Customs Declaration Backend..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/upgrade dependencies
echo "📚 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file from template..."
    cp env.example .env
    echo "⚠️  Please edit .env file with your configuration before continuing"
    echo "Press Enter when ready..."
    read
fi

# Create uploads directory
echo "📁 Creating uploads directory..."
mkdir -p uploads

echo "✅ Setup complete!"
echo ""
echo "To start the backend:"
echo "1. Start PostgreSQL and Redis"
echo "2. Run: uvicorn main:app --reload --host 0.0.0.0 --port 8000"
echo "3. In another terminal, run: celery -A tasks.background_tasks worker --loglevel=info"
echo ""
echo "Or use Docker Compose:"
echo "docker-compose up --build"
