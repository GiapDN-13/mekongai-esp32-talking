#!/bin/bash
# =============================================================================
# Start All Services — VPS (giống start-all.bat trên local)
# Chạy: bash start-all-vps.sh
# =============================================================================
set -e

PROJECT_DIR="/root/esp32-server"
XIAOZHI_DIR="$PROJECT_DIR/main/xiaozhi-server"
API_DIR="$PROJECT_DIR/main/manager-api"
WEB_DIR="$PROJECT_DIR/main/manager-web"
PORTAL_DIR="$PROJECT_DIR/main/teacher-portal"
VPS_IP="144.91.113.233"

echo "========================================="
echo " Starting All Services..."
echo "========================================="

# ----- Kill old processes if running -----
pkill -f "xiaozhi-esp32-api" 2>/dev/null || true
pkill -f "vue-cli-service" 2>/dev/null || true
pkill -f "python app.py" 2>/dev/null || true
pkill -f "next dev" 2>/dev/null || true
sleep 2

# ----- 1. Docker: MySQL, Redis, Qdrant, Voiceprint -----
echo ""
echo " [1/5] Docker services (MySQL, Redis, Qdrant, Voiceprint)..."
cd "$XIAOZHI_DIR"
docker compose -f docker-compose.vps.yml up -d

echo "        Waiting for MySQL healthy..."
for i in $(seq 1 12); do
    if docker exec xiaozhi-esp32-server-mysql mysqladmin ping -h localhost -u root -p123456 --silent 2>/dev/null; then
        echo "        MySQL ready."
        break
    fi
    sleep 5
done

# ----- 2. Manager API (Java, port 8002) -----
echo ""
echo " [2/5] Manager API (port 8002)..."
cd "$API_DIR"
mkdir -p "$API_DIR/logs"
nohup java -jar target/xiaozhi-esp32-api.jar --spring.profiles.active=dev,vps > /tmp/manager-api.log 2>&1 &
echo "        PID: $! — waiting for Tomcat..."

for i in $(seq 1 12); do
    if curl -s -o /dev/null -w "" http://127.0.0.1:8002/xiaozhi/doc.html 2>/dev/null; then
        STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8002/xiaozhi/doc.html)
        if [ "$STATUS" = "200" ]; then
            echo "        [OK] Manager API ready."
            break
        fi
    fi
    sleep 5
done

# ----- 3. Manager Web (Node.js, port 8001) -----
echo ""
echo " [3/5] Manager Web (port 8001)..."
cd "$WEB_DIR"
nohup npx vue-cli-service serve --port 8001 --host 0.0.0.0 > /tmp/manager-web.log 2>&1 &
echo "        PID: $! — compiling..."
sleep 25

if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8001 2>/dev/null | grep -q "200"; then
    echo "        [OK] Manager Web ready."
else
    echo "        [WAIT] Still compiling, check: tail -f /tmp/manager-web.log"
fi

# ----- 4. Xiaozhi Server (Python, port 8000) -----
echo ""
echo " [4/5] Xiaozhi Server (port 8000)..."
cd "$XIAOZHI_DIR"
eval "$(conda shell.bash hook)"
conda activate xiaozhi
export XIAOZHI_CONFIG_PROFILE=storyteller
nohup python app.py > /tmp/xiaozhi-server.log 2>&1 &
echo "        PID: $! — loading models..."
sleep 15

if grep -q "started" /tmp/xiaozhi-server.log 2>/dev/null; then
    echo "        [OK] Xiaozhi Server ready."
else
    echo "        [WAIT] Still loading, check: tail -f /tmp/xiaozhi-server.log"
fi

# ----- 5. Teacher Portal (Next.js, port 3000) -----
echo ""
echo " [5/5] Teacher Portal (port 3000)..."
cd "$PORTAL_DIR"
if [ ! -d "node_modules" ]; then
    echo "        Installing npm dependencies..."
    npm install > /dev/null 2>&1
fi
nohup npm run dev -- -p 3000 > /tmp/teacher-portal.log 2>&1 &
echo "        PID: $! — compiling..."
sleep 10

if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3000 2>/dev/null | grep -q "200\|307"; then
    echo "        [OK] Teacher Portal ready."
else
    echo "        [WAIT] Still compiling, check: tail -f /tmp/teacher-portal.log"
fi

echo ""
echo "========================================="
echo " All services launched!"
echo "========================================="
echo ""
echo "  Service               Port   Log"
echo "  ---------------------------------------------------------"
echo "  [DOCKER] MySQL        3307   docker compose -f docker-compose.vps.yml logs mysql"
echo "  [DOCKER] Redis        6381   docker compose -f docker-compose.vps.yml logs redis"
echo "  [DOCKER] Qdrant       6333   docker compose -f docker-compose.vps.yml logs qdrant"
echo "  [DOCKER] Voiceprint   8100   docker compose -f docker-compose.vps.yml logs voiceprint-service"
echo "  [NATIVE] Manager API  8002   tail -f /tmp/manager-api.log"
echo "  [NATIVE] Manager Web  8001   tail -f /tmp/manager-web.log"
echo "  [NATIVE] Xiaozhi AI   8000   tail -f /tmp/xiaozhi-server.log"
echo "  [NATIVE] Teacher UI   3000   tail -f /tmp/teacher-portal.log"
echo ""
echo "  Admin Console:    http://$VPS_IP:8001"
echo "  Teacher Portal:   http://$VPS_IP:3000"
echo "  API Docs:         http://$VPS_IP:8002/xiaozhi/doc.html"
echo "  Qdrant UI:        http://$VPS_IP:6333/dashboard"
echo ""
echo "  To stop all:  bash stop-vps.sh"
