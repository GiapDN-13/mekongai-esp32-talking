#!/bin/bash
# =============================================================================
# VPS Setup Script — Cài đặt giống hệt máy local
# Docker: MySQL (3307), Redis (6381), Qdrant (6333), Voiceprint (8100)
# Native: Manager API (8002), Manager Web (8001), Xiaozhi Server (8000)
# =============================================================================
set -e

echo "========================================="
echo " VPS Setup — Xiaozhi ESP32 Server"
echo "========================================="

# ----- 1. Cài Java 21 (Manager API cần Java 21) -----
echo ""
echo "[1/4] Cài Java 21..."
if java -version 2>&1 | grep -q "21"; then
    echo "  Java 21 đã có sẵn."
else
    apt update
    apt install -y openjdk-21-jdk-headless
    echo "  Java 21 đã cài xong."
fi
java -version

# ----- 2. Cài Maven (build Manager API) -----
echo ""
echo "[2/4] Cài Maven..."
if command -v mvn &> /dev/null; then
    echo "  Maven đã có sẵn."
else
    apt install -y maven
    echo "  Maven đã cài xong."
fi
mvn -version

# ----- 3. Cài Node.js 18 (Manager Web cần Node.js) -----
echo ""
echo "[3/4] Cài Node.js 18..."
if command -v node &> /dev/null; then
    echo "  Node.js đã có sẵn: $(node -v)"
else
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
    apt install -y nodejs
    echo "  Node.js đã cài xong."
fi
node -v
npm -v

# ----- 4. Python + conda env -----
echo ""
echo "[4/4] Tạo conda env cho xiaozhi-server..."
if conda info --envs 2>/dev/null | grep -q "xiaozhi"; then
    echo "  Conda env 'xiaozhi' đã tồn tại."
else
    conda create -n xiaozhi python=3.10 -y
    echo "  Conda env 'xiaozhi' đã tạo xong."
fi

echo ""
echo "========================================="
echo " Cài đặt hoàn tất!"
echo " Tiếp theo: chạy deploy-vps.sh"
echo "========================================="
