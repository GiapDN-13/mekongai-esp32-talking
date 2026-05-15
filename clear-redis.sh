#!/bin/bash
# ============================================================================
#  Clear Redis cache — use when Redis causes connection/data errors
#  Flushes all Redis data and optionally removes persistence files.
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REDIS_DATA_DIR="$SCRIPT_DIR/main/xiaozhi-server/data/redis"
COMPOSE_DIR="$SCRIPT_DIR/main/xiaozhi-server"

echo ""
echo "=== Redis Cache Cleaner ==="
echo ""

# Try to flush via redis-cli inside Docker container first
CONTAINER=$(docker compose -f "$COMPOSE_DIR/docker-compose.yml" ps -q redis 2>/dev/null || true)

if [ -n "$CONTAINER" ]; then
    echo "[1/3] Redis container is running. Flushing via FLUSHALL..."
    docker exec "$CONTAINER" redis-cli -a xiaozhi_redis_2024 FLUSHALL 2>/dev/null && \
        echo "  -> FLUSHALL OK" || \
        echo "  -> FLUSHALL failed (may need different password)"
else
    echo "[1/3] Redis container not running. Skipping FLUSHALL."
fi

# Remove persistence files on disk
echo "[2/3] Removing Redis persistence files..."
if [ -d "$REDIS_DATA_DIR" ]; then
    rm -rf "$REDIS_DATA_DIR"/*
    echo "  -> Cleared: $REDIS_DATA_DIR"
else
    echo "  -> Directory not found: $REDIS_DATA_DIR (nothing to clear)"
fi

# Restart Redis container if running
if [ -n "$CONTAINER" ]; then
    echo "[3/3] Restarting Redis container..."
    docker compose -f "$COMPOSE_DIR/docker-compose.yml" restart redis
    echo "  -> Redis restarted."
else
    echo "[3/3] Redis not running. Start it with: docker compose up -d redis"
fi

echo ""
echo "=== Done. Redis cache cleared. ==="
echo ""
