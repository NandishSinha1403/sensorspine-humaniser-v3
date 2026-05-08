#!/bin/bash

# ScholarAI v3 SOTA - Orchestration Script
# This script starts the full async pipeline: Redis -> Celery -> FastAPI

echo "--------------------------------------------------------"
echo "🚀 Starting ScholarAI v3 SOTA Pipeline"
echo "--------------------------------------------------------"

# 1. Start Redis Server (Background)
echo "[1/3] Starting Redis Server..."
redis-server --daemonize yes

# Wait a moment for Redis to initialize
sleep 2
if pgrep -x "redis-server" > /dev/null
then
    echo "✅ Redis is running."
else
    echo "❌ Failed to start Redis."
    exit 1
fi

# 2. Start Celery Worker (Background)
# We use --concurrency=1 to prevent multiple processes from fighting for the GPU.
# Logs will still be visible in the terminal.
echo "[2/3] Starting Celery Worker (Gemma/AMR/Judge)..."
celery -A tasks worker --loglevel=info --concurrency=1 &

# 3. Start FastAPI/Uvicorn (Foreground)
# This will keep the process alive and show the web gateway logs.
echo "[3/3] Starting FastAPI Gateway at http://0.0.0.0:8000"
echo "--------------------------------------------------------"
uvicorn main:app --host 0.0.0.0 --port 8000
