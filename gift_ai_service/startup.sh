#!/bin/bash
# startup.sh - Minimal version for Azure Oryx deployment
# Oryx automatically sets working directory to the extracted location

echo "========================================="
echo "🚀 Gift AI Service - Starting"
echo "========================================="
echo "📂 Working directory: $(pwd)"
echo "📋 Files:"
ls -la | head -10

# Verify main.py exists
if [ ! -f "main.py" ]; then
    echo "❌ ERROR: main.py not found in $(pwd)"
    echo "📂 Directory contents:"
    ls -la
    exit 1
fi

echo "✅ Found main.py"

# Set environment
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
PORT=${PORT:-8001}

echo "🔐 Environment:"
[ -n "$GOOGLE_API_KEY" ] && echo "  ✅ GOOGLE_API_KEY: SET" || echo "  ⚠️  GOOGLE_API_KEY: NOT SET"
[ -n "$MONGODB_URL" ] && echo "  ✅ MONGODB_URL: SET" || echo "  ⚠️  MONGODB_URL: NOT SET"
[ -n "$QDRANT_URL" ] && echo "  ✅ QDRANT_URL: SET" || echo "  ⚠️  QDRANT_URL: NOT SET"
echo "  📡 PORT: $PORT"

echo ""
echo "⚡ Starting Gunicorn..."

# Start Gunicorn
exec gunicorn \
    -w 1 \
    -k uvicorn.workers.UvicornWorker \
    main:app \
    --bind=0.0.0.0:$PORT \
    --timeout=300 \
    --graceful-timeout=120 \
    --access-logfile=- \
    --error-logfile=- \
    --log-level=info