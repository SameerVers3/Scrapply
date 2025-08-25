#!/bin/bash

# Nexus Platform Backend Startup Script

echo "🚀 Starting Nexus Platform Backend..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "⚠️  Virtual environment not found. Creating one..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cp .env.example .env
    echo "📝 Please edit .env file and add your OpenAI API key"
    echo "   OPENAI_API_KEY=your_api_key_here"
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Run database migrations
echo "🗄️  Setting up database..."
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head

# Start the application
echo "🌟 Starting FastAPI server..."
echo "📍 API will be available at: http://localhost:8000"
echo "📚 API docs will be available at: http://localhost:8000/docs"
uvicorn main:app --reload --host 0.0.0.0 --port 8000
