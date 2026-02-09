#!/bin/bash
# startup.sh - Optimized for Azure App Service with Lazy Initialization

echo "========================================="
echo "🚀 Starting Unified Gift AI Service"
echo "========================================="

# Navigate to service directory
cd /home/site/wwwroot/gift_ai_service || {
    echo "❌ Failed to navigate to gift_ai_service directory"
    exit 1
}

echo "📂 Working directory: $(pwd)"
echo "🐍 Python version: $(python --version)"
echo "📦 Pip version: $(pip --version)"

# Check environment variables
echo ""
echo "🔐 Environment Check:"
echo "  - GOOGLE_API_KEY: ${GOOGLE_API_KEY:+SET}"
echo "  - GEMINI_API_KEY: ${GEMINI_API_KEY:+SET}"
echo "  - MONGODB_URL: ${MONGODB_URL:+SET}"
echo "  - QDRANT_URL: ${QDRANT_URL:+SET}"
echo "  - PORT: ${PORT:-8001}"

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo ""
    echo "📦 Creating virtual environment..."
    python -m venv venv
fi

echo ""
echo "📦 Activating virtual environment..."
source venv/bin/activate

echo ""
echo "📦 Installing/Upgrading dependencies..."
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir

# List installed packages for debugging
echo ""
echo "📋 Installed packages:"
pip list | grep -E "(fastapi|uvicorn|gunicorn|google|qdrant|motor|pymongo)"

# Get port from environment or default to 8001
PORT=${PORT:-8001}

echo ""
echo "========================================="
echo "⚡ Starting Gunicorn (OPTIMIZED)"
echo "========================================="
echo "Configuration:"
echo "  - Workers: 2 (reduced from 4)"
echo "  - Worker class: uvicorn.workers.UvicornWorker"
echo "  - Timeout: 300s (worker timeout)"
echo "  - Preload: enabled (faster startup)"
echo "  - Port: $PORT"
echo "  - Startup mode: LAZY (connections on first request)"
echo ""
echo "Expected startup: <5 seconds ⚡"
echo "========================================="

# Start Gunicorn with optimized settings
exec gunicorn \
    -w 2 \
    -k uvicorn.workers.UvicornWorker \
    main:app \
    --bind 0.0.0.0:$PORT \
    --timeout 300 \
    --preload \
    --access-logfile - \
    --error-logfile - \
    --log-level info