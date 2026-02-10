#!/bin/bash
# startup.sh - FIXED for Azure App Service deployment

echo "========================================="
echo "🚀 Starting Unified Gift AI Service"
echo "========================================="

# Try multiple possible locations for main.py
if [ -f "/home/site/wwwroot/main.py" ]; then
    cd /home/site/wwwroot
    echo "📂 Working directory: /home/site/wwwroot"
elif [ -f "/home/site/wwwroot/gift_ai_service/main.py" ]; then
    cd /home/site/wwwroot/gift_ai_service
    echo "📂 Working directory: /home/site/wwwroot/gift_ai_service"
else
    echo "❌ Cannot find main.py. Listing directory structure:"
    find /home/site/wwwroot -name "main.py" 2>/dev/null || echo "No main.py found anywhere"
    echo ""
    echo "📂 /home/site/wwwroot contents:"
    ls -la /home/site/wwwroot/
    exit 1
fi

echo "📋 Files present:"
ls -la | head -20

echo "✅ Found main.py at: $(pwd)/main.py"

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
ANTENV_PATHS=(
    "/tmp/8de68b156672248/antenv"
    "$(pwd)/antenv"
    "/home/site/wwwroot/antenv"
)

ACTIVATED=false
for VENV_PATH in "${ANTENV_PATHS[@]}"; do
    if [ -d "$VENV_PATH" ]; then
        echo "  ✅ Found antenv at $VENV_PATH"
        source "$VENV_PATH/bin/activate"
        ACTIVATED=true
        break
    fi
done

if [ "$ACTIVATED" = false ]; then
    echo "  ⚠️  No virtual environment found (using system Python)"
    echo "  📦 Installing dependencies from requirements.txt..."
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt --quiet
        echo "  ✅ Dependencies installed"
    fi
fi

# Test if main module can be imported
echo ""
echo "🧪 Testing module import..."
python -c "import main; print('✅ main.py imports successfully')" || {
    echo "❌ Failed to import main.py"
    echo "🔍 Debugging info:"
    python -c "import sys; print('Python path:', sys.path)"
    python -c "import fastapi; print('FastAPI version:', fastapi.__version__)" 2>/dev/null || echo "❌ FastAPI not installed"
    exit 1
}

PORT=${PORT:-8001}

echo ""
echo "⚡ Starting Gunicorn on port $PORT..."
echo "   Workers: 1 (lazy init mode)"
echo "   Worker class: uvicorn.workers.UvicornWorker"
echo "   Timeout: 300s"
echo ""

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