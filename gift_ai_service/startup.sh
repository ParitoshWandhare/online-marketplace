#!/bin/bash
# startup.sh - FIXED for Azure App Service deployment

echo "========================================="
echo "🚀 Starting Unified Gift AI Service"
echo "========================================="

# Try multiple possible locations
if [ -d "/home/site/wwwroot/gift_ai_service" ]; then
    cd /home/site/wwwroot/gift_ai_service
    echo "📂 Working directory: /home/site/wwwroot/gift_ai_service"
elif [ -d "/home/site/wwwroot" ]; then
    cd /home/site/wwwroot
    echo "📂 Working directory: /home/site/wwwroot"
else
    echo "❌ Cannot find application directory"
    exit 1
fi

echo "📋 Files present:"
ls -la | head -20

# Check if main.py exists
if [ ! -f "main.py" ]; then
    echo "❌ ERROR: main.py not found in $(pwd)"
    echo "📂 Directory contents:"
    ls -la
    exit 1
fi

echo "✅ Found main.py"

# Add current directory to Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
echo "🐍 PYTHONPATH: $PYTHONPATH"

# Check Python version
echo "🐍 Python version: $(python --version)"

# Environment variable check
echo ""
echo "🔐 Environment Check:"
[ -n "$GOOGLE_API_KEY" ] && echo "  ✅ GOOGLE_API_KEY: SET" || echo "  ❌ GOOGLE_API_KEY: NOT SET"
[ -n "$GEMINI_API_KEY" ] && echo "  ✅ GEMINI_API_KEY: SET" || echo "  ❌ GEMINI_API_KEY: NOT SET"  
[ -n "$MONGODB_URL" ] && echo "  ✅ MONGODB_URL: SET" || echo "  ❌ MONGODB_URL: NOT SET"
[ -n "$QDRANT_URL" ] && echo "  ✅ QDRANT_URL: SET" || echo "  ❌ QDRANT_URL: NOT SET"
echo "  - PORT: ${PORT:-8001}"

# Try to activate virtual environment
echo ""
echo "📦 Checking for virtual environment..."
if [ -d "/tmp/8de68234386b6c1/antenv" ]; then
    echo "  ✅ Found antenv at /tmp/8de68234386b6c1/antenv"
    source /tmp/8de68234386b6c1/antenv/bin/activate
elif [ -d "antenv" ]; then
    echo "  ✅ Found antenv in current directory"
    source antenv/bin/activate
else
    echo "  ⚠️  No virtual environment found (using system Python)"
fi

# Test if main module can be imported
echo ""
echo "🧪 Testing module import..."
python -c "import main; print('✅ main.py imports successfully')" || {
    echo "❌ Failed to import main.py"
    echo "🔍 Debugging info:"
    python -c "import sys; print('Python path:', sys.path)"
    exit 1
}

PORT=${PORT:-8001}

echo ""
echo "⚡ Starting Gunicorn on port $PORT..."
echo "   Workers: 1 (lazy init mode)"
echo "   Worker class: uvicorn.workers.UvicornWorker"
echo "   Timeout: 300s"
echo ""

# Start with single worker and preload for faster startup
exec gunicorn \
    -w 1 \
    -k uvicorn.workers.UvicornWorker \
    main:app \
    --bind 0.0.0.0:$PORT \
    --timeout 300 \
    --graceful-timeout 120 \
    --keep-alive 75 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --preload \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --worker-tmp-dir /dev/shm 2>&1