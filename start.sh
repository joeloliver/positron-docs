#!/bin/bash

# Document RAG Interface Startup Script

echo "🚀 Starting Document RAG Interface..."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Please run setup first:"
    echo "   python3 -m venv .venv"
    echo "   source .venv/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "✅ Please edit .env file with your settings before running again."
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Start the backend server
echo "🔧 Starting FastAPI backend server..."
uvicorn app:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo "✅ Backend server started (PID: $BACKEND_PID)"
echo "📡 API available at: http://localhost:8000"
echo "📚 API docs available at: http://localhost:8000/docs"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping servers..."
    kill $BACKEND_PID 2>/dev/null
    echo "✅ Servers stopped"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

echo ""
echo "🌐 To start the frontend, run in another terminal:"
echo "   cd frontend"
echo "   npm install"
echo "   npm run dev"
echo ""
echo "📖 Frontend will be available at: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop the backend server"

# Wait for the backend process
wait $BACKEND_PID