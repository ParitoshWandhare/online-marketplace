#!/bin/bash
# startup.sh - Optimized for Azure App Service

echo "========================================="
echo "🚀 Starting Unified Gift AI Service"
echo "========================================="

# Navigate to deployed app root
cd /home/site/wwwroot || {
    echo "❌ Failed to navigate to app directory"
    exit 1
}

echo "📂 Working directory: $(pwd)"
echo "🐍 Python version: $(python --version)"

# Environment check
echo ""
echo "🔐 Environment Check:"
echo "  - GOOGLE_API_KEY: ${GOOGLE_API_KEY:+SET}"
echo "  - GEMINI_API_KEY: ${GEMINI_API_KEY:+SET}"
echo "  - MONGODB_URL: ${MONGODB_URL:+SET}"
echo "  - QDRANT_URL: ${QDRANT_URL:+SET}"
echo "  - PORT: ${PORT:-8000}"

# Activate Azure's virtual env (already created by Oryx)
if [ -d "antenv" ]; then
    echo "📦 Activating antenv..."
    source antenv/bin/activate
fi

PORT=${PORT:-8000}

echo ""
echo "⚡ Starting Gunicorn..."

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
