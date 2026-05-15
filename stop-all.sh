#!/bin/bash
# ============================================================================
#  Xiaozhi ESP32 Server — Stop all services
# ============================================================================

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
COMPOSE_DIR="$SCRIPT_DIR/main/xiaozhi-server"

echo ""
echo "  Stopping all Xiaozhi services..."
echo ""

kill_by_pattern() {
    local name="$1"
    local pattern="$2"
    local pids
    pids=$(pgrep -f "$pattern" 2>/dev/null || true)
    if [ -n "$pids" ]; then
        echo "$pids" | xargs kill -9 2>/dev/null
        echo "[OK] $name stopped (PIDs: $pids)"
    else
        echo "[--] $name not running"
    fi
}

kill_by_pattern "Voiceprint Service" "voiceprint-service/app.py"
kill_by_pattern "Manager API"        "spring-boot:run.*xiaozhi"
kill_by_pattern "Manager Web"        "manager-web.*serve"
kill_by_pattern "Xiaozhi Server"     "xiaozhi-server/app.py"

echo ""
read -p "Stop Docker containers too? (y/N): " STOP_DOCKER
if [[ "$STOP_DOCKER" =~ ^[Yy]$ ]]; then
    docker compose -f "$COMPOSE_DIR/docker-compose.yml" stop
    echo "[OK] Docker containers stopped."
fi

echo ""
echo "  All services stopped."
echo ""
