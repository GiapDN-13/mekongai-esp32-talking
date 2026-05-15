#!/bin/bash
# =============================================================================
# VPS Deploy Script — Khởi động tất cả services
# Chạy SAU khi đã: setup-vps.sh + git clone + upload data/models
# =============================================================================
set -e

PROJECT_DIR="/root/esp32-server"
XIAOZHI_DIR="$PROJECT_DIR/main/xiaozhi-server"
API_DIR="$PROJECT_DIR/main/manager-api"
WEB_DIR="$PROJECT_DIR/main/manager-web"

VPS_IP="144.91.113.233"

echo "========================================="
echo " Deploy — Xiaozhi ESP32 Server"
echo "========================================="

# ----- 1. Docker: MySQL, Redis, Qdrant, Voiceprint -----
echo ""
echo "[1/5] Khởi động Docker services (MySQL, Redis, Qdrant, Voiceprint)..."
cd "$XIAOZHI_DIR"
docker compose -f docker-compose.vps.yml up -d
echo "  Đợi MySQL healthy..."
sleep 15

# ----- 2. Import MySQL database (nếu chưa có data) -----
if [ -f "$XIAOZHI_DIR/mysql_backup.sql" ]; then
    echo ""
    echo "[2/5] Import MySQL database..."
    docker exec -i xiaozhi-esp32-server-mysql mysql -u root -p123456 xiaozhi_esp32_server < "$XIAOZHI_DIR/mysql_backup.sql"
    echo "  Import xong."
else
    echo ""
    echo "[2/5] Không tìm thấy mysql_backup.sql — bỏ qua import."
fi

# ----- 3. Build + chạy Manager API (Java) -----
echo ""
echo "[3/5] Build Manager API..."
cd "$API_DIR"
# Dùng profile vps (application-vps.yml) thay vì dev
mvn clean package -DskipTests -q
echo "  Build xong. Khởi động Manager API..."
nohup java -jar target/xiaozhi-esp32-api-0.0.1.jar --spring.profiles.active=vps > /tmp/manager-api.log 2>&1 &
echo "  Manager API PID: $!"
echo "  Đợi Tomcat khởi động..."
sleep 25

# Kiểm tra
if curl -s http://127.0.0.1:8002/xiaozhi/doc.html > /dev/null; then
    echo "  [OK] Manager API sẵn sàng trên port 8002"
else
    echo "  [WARN] Manager API chưa sẵn sàng, kiểm tra log: tail -f /tmp/manager-api.log"
fi

# ----- 4. Build + chạy Manager Web (Node.js) -----
echo ""
echo "[4/5] Build Manager Web..."
cd "$WEB_DIR"
npm install --legacy-peer-deps
echo "  Khởi động Manager Web (dev server port 8001)..."
nohup npx vue-cli-service serve --port 8001 > /tmp/manager-web.log 2>&1 &
echo "  Manager Web PID: $!"
sleep 10

if curl -s http://127.0.0.1:8001 > /dev/null; then
    echo "  [OK] Manager Web sẵn sàng trên port 8001"
else
    echo "  [WARN] Manager Web chưa sẵn sàng, kiểm tra log: tail -f /tmp/manager-web.log"
fi

# ----- 5. Chạy Xiaozhi Server (Python) -----
echo ""
echo "[5/5] Khởi động Xiaozhi Server..."
cd "$XIAOZHI_DIR"

# Kích hoạt conda env
eval "$(conda shell.bash hook)"
conda activate xiaozhi

# Cài dependencies (lần đầu)
pip install -r requirements.txt -q 2>/dev/null || true

# Sửa config: websocket URL cho ESP32 kết nối
# (chỉ cần sửa 1 lần, config.yaml gốc có placeholder)
export XIAOZHI_CONFIG_PROFILE=storyteller

nohup python app.py > /tmp/xiaozhi-server.log 2>&1 &
echo "  Xiaozhi Server PID: $!"
sleep 10

echo ""
echo "========================================="
echo " Tất cả services đã khởi động!"
echo "========================================="
echo ""
echo "  Service               Port   Status"
echo "  ---------------------------------------------------------"
echo "  [DOCKER] MySQL        3307   docker compose -f docker-compose.vps.yml ps"
echo "  [DOCKER] Redis        6381   docker compose -f docker-compose.vps.yml ps"
echo "  [DOCKER] Qdrant       6333   docker compose -f docker-compose.vps.yml ps"
echo "  [DOCKER] Voiceprint   8100   docker compose -f docker-compose.vps.yml ps"
echo "  [NATIVE] Manager API  8002   tail -f /tmp/manager-api.log"
echo "  [NATIVE] Manager Web  8001   tail -f /tmp/manager-web.log"
echo "  [NATIVE] Xiaozhi AI   8000   tail -f /tmp/xiaozhi-server.log"
echo ""
echo "  Web Console:  http://$VPS_IP:8001"
echo "  API Docs:     http://$VPS_IP:8002/xiaozhi/doc.html"
echo "  Qdrant UI:    http://$VPS_IP:6333/dashboard"
echo ""
echo "  Logs:"
echo "    tail -f /tmp/manager-api.log"
echo "    tail -f /tmp/manager-web.log"
echo "    tail -f /tmp/xiaozhi-server.log"
