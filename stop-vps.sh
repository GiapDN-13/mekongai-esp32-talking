#!/bin/bash
# =============================================================================
# Stop All Services — VPS
# =============================================================================
echo "========================================="
echo " Stopping All Services..."
echo "========================================="

# Stop native processes
pkill -f "xiaozhi-esp32-api" 2>/dev/null && echo "  [OK] Stopped Manager API" || echo "  Manager API not running"
pkill -f "vue-cli-service" 2>/dev/null && echo "  [OK] Stopped Manager Web" || echo "  Manager Web not running"
pkill -f "python app.py" 2>/dev/null && echo "  [OK] Stopped Xiaozhi Server" || echo "  Xiaozhi Server not running"

# Stop Docker services
cd /root/esp32-server/main/xiaozhi-server
docker compose -f docker-compose.vps.yml down
echo "  [OK] Stopped Docker services (MySQL, Redis, Qdrant, Voiceprint)"

echo ""
echo "========================================="
echo " All services stopped."
echo "========================================="
