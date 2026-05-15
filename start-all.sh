#!/usr/bin/env bash
# ============================================================================
#  Xiaozhi ESP32 Server — CLI Dashboard with Live Logs
#
#  Usage:
#     bash start-all.sh              # All services, live logs
#     bash start-all.sh --no-web     # Skip manager-web
#     bash start-all.sh --only voiceprint
#     bash start-all.sh --quiet      # Logs to files only (old behavior)
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
CONDA_ENV="xiaozhi-esp32-server"
LOG_DIR="$PROJECT_ROOT/logs"
mkdir -p "$LOG_DIR"

# ─── ANSI Colors ──────────────────────────────────────────────────────────
RST='\033[0m'
BOLD='\033[1m'
DIM='\033[2m'

C_SYS='\033[1;37m'       # white   — system
C_DOCKER='\033[0;36m'     # cyan    — docker
C_VP='\033[1;35m'         # magenta — voiceprint
C_API='\033[1;33m'        # yellow  — manager api
C_WEB='\033[0;32m'        # green   — manager web
C_SERVER='\033[1;34m'     # blue    — xiaozhi server
C_PORTAL='\033[0;96m'     # cyan    — teacher portal

C_OK='\033[1;32m'
C_WARN='\033[1;33m'
C_ERR='\033[1;31m'
C_INFO='\033[0;36m'

# ─── Logging ──────────────────────────────────────────────────────────────
_ts() { date '+%H:%M:%S'; }

sys()  { echo -e "${DIM}$(_ts)${RST} ${C_SYS}[SYSTEM]${RST}  $1"; }
ok()   { echo -e "${DIM}$(_ts)${RST} ${C_OK}  [OK]${RST}    $1"; }
warn() { echo -e "${DIM}$(_ts)${RST} ${C_WARN}[WARN]${RST}   $1"; }
err()  { echo -e "${DIM}$(_ts)${RST} ${C_ERR} [ERR]${RST}    $1"; }
hdr()  {
    echo ""
    echo -e "${C_INFO}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RST}"
    echo -e "${C_INFO}  $1${RST}"
    echo -e "${C_INFO}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RST}"
}

stream_with_prefix() {
    local color="$1" label="$2" logfile="$3"
    while IFS= read -r line; do
        echo -e "${DIM}$(_ts)${RST} ${color}[${label}]${RST} ${line}"
        echo "$(_ts) [${label}] ${line}" >> "$logfile"
    done
}

# ─── PIDs & Cleanup ──────────────────────────────────────────────────────
PIDS=""
add_pid() { PIDS="$PIDS $1"; }

cleanup() {
    echo ""
    hdr "Shutting down..."
    for pid in $PIDS; do
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null
            ok "Stopped PID $pid"
        fi
    done
    jobs -p 2>/dev/null | while read -r p; do kill "$p" 2>/dev/null; done
    ok "All services stopped. Bye!"
    exit 0
}
trap cleanup SIGINT SIGTERM

# ─── Helpers ──────────────────────────────────────────────────────────────
wait_for_port() {
    local port="$1" name="$2" timeout="${3:-60}"
    local elapsed=0
    while true; do
        if netstat -ano 2>/dev/null | grep -q ":${port}.*LISTENING"; then
            ok "$name ready on :${port} (${elapsed}s)"
            return 0
        fi
        sleep 2
        elapsed=$((elapsed + 2))
        if [ "$elapsed" -ge "$timeout" ]; then
            err "$name failed to start on port $port (timeout ${timeout}s)"
            return 1
        fi
    done
}

free_port() {
    local port="$1" name="$2"
    local pid=""
    pid=$(netstat -ano 2>/dev/null | grep ":${port}.*LISTENING" | awk '{print $NF}' | head -1) || true
    if [ -n "$pid" ] && [ "$pid" != "0" ]; then
        warn "Port $port occupied by PID $pid — killing old $name..."
        taskkill //F //PID "$pid" >/dev/null 2>&1 || kill -9 "$pid" 2>/dev/null || true
        sleep 1
        ok "Port $port freed"
    fi
}

activate_conda() {
    if command -v conda &>/dev/null; then
        eval "$(conda shell.bash hook 2>/dev/null)" || true
        conda activate "$CONDA_ENV" 2>/dev/null || true
        ok "Conda: $CONDA_ENV ($(python --version 2>&1))"
    else
        warn "conda not found — using system Python"
    fi
}

# ─── Parse args ───────────────────────────────────────────────────────────
SKIP_WEB=false
SKIP_PORTAL=false
ONLY=""
QUIET=false
while [ $# -gt 0 ]; do
    case "$1" in
        --no-web)      SKIP_WEB=true; shift ;;
        --no-portal)   SKIP_PORTAL=true; shift ;;
        --only)        ONLY="$2"; shift 2 ;;
        --quiet)       QUIET=true; shift ;;
        -h|--help)
            cat <<'HELP'
Xiaozhi ESP32 Server — CLI Dashboard

Usage: bash start-all.sh [OPTIONS]

Options:
  --no-web          Skip manager-web (Vue dev server)
  --no-portal       Skip teacher-portal (Next.js dev server)
  --only SERVICE    Start only: docker | voiceprint | api | web | portal | server
  --quiet           Redirect logs to files (no live output)
  -h, --help        Show this help
HELP
            exit 0 ;;
        *) err "Unknown option: $1"; exit 1 ;;
    esac
done

should_run() {
    [ -z "$ONLY" ] || [ "$ONLY" = "$1" ]
}

# ═══════════════════════════════════════════════════════════════════════════
#                              BANNER
# ═══════════════════════════════════════════════════════════════════════════
clear
echo -e "${C_INFO}${BOLD}"
cat << 'BANNER'
    ╔═══════════════════════════════════════════════════════╗
    ║         XIAOZHI ESP32 — Service Dashboard            ║
    ╚═══════════════════════════════════════════════════════╝
BANNER
echo -e "${RST}"
echo -e "  ${DIM}Log directory: $LOG_DIR${RST}"
echo -e "  ${DIM}Press ${BOLD}Ctrl+C${RST}${DIM} to stop all services${RST}"
echo ""

# ─── Pre-checks ──────────────────────────────────────────────────────────
sys "Running pre-flight checks..."

if ! command -v docker &>/dev/null; then
    err "docker not found — install Docker Desktop first"
    exit 1
fi
ok "Docker: $(docker --version 2>&1 | head -c 50)"

if should_run "api"; then
    command -v mvn &>/dev/null || warn "mvn not found — Manager API will be skipped"
fi
if should_run "web" && [ "$SKIP_WEB" = "false" ]; then
    command -v npm &>/dev/null || warn "npm not found — Manager Web will be skipped"
fi

# ═══════════════════════════════════════════════════════════════════════════
#  1. Docker infrastructure
# ═══════════════════════════════════════════════════════════════════════════
if should_run "docker"; then
    hdr "1/6  Docker Infrastructure"

    cd "$PROJECT_ROOT/main/xiaozhi-server"
    sys "Starting MySQL, Redis, Qdrant containers..."
    docker compose up -d mysql redis qdrant 2>&1 | stream_with_prefix "$C_DOCKER" "DOCKER " "$LOG_DIR/docker.log"

    sys "Waiting for MySQL..."
    mysql_ok=false
    for i in $(seq 1 30); do
        if docker exec xiaozhi-esp32-server-mysql mysqladmin ping -h localhost -u root -p123456 &>/dev/null 2>&1; then
            ok "MySQL ready (port 3307)"
            mysql_ok=true
            break
        fi
        sleep 2
    done
    if [ "$mysql_ok" = "false" ]; then
        warn "MySQL may not be fully ready"
    fi
    ok "Redis ready (port 6379)"
    ok "Qdrant ready (port 6333)"
fi

# ═══════════════════════════════════════════════════════════════════════════
#  2. Voiceprint Service
# ═══════════════════════════════════════════════════════════════════════════
if should_run "voiceprint"; then
    hdr "2/6  Voiceprint Service (Resemblyzer)"

    activate_conda
    free_port 8100 "Voiceprint Service"

    cd "$PROJECT_ROOT/main/voiceprint-service"
    : > "$LOG_DIR/voiceprint.log"

    if [ "$QUIET" = "true" ]; then
        python app.py >> "$LOG_DIR/voiceprint.log" 2>&1 &
    else
        python app.py 2>&1 | stream_with_prefix "$C_VP" "VOICE  " "$LOG_DIR/voiceprint.log" &
    fi
    add_pid $!
    wait_for_port 8100 "Voiceprint Service" 60
fi

# ═══════════════════════════════════════════════════════════════════════════
#  3. Manager API
# ═══════════════════════════════════════════════════════════════════════════
if should_run "api" && command -v mvn &>/dev/null; then
    hdr "3/6  Manager API (Spring Boot)"

    if netstat -ano 2>/dev/null | grep -q ":8002.*LISTENING"; then
        ok "Manager API already running on :8002"
    else
        cd "$PROJECT_ROOT/main/manager-api"
        : > "$LOG_DIR/manager-api.log"

        MVN_ARGS="--spring.datasource.druid.url=jdbc:mysql://127.0.0.1:3307/xiaozhi_esp32_server?useUnicode=true&characterEncoding=UTF-8&serverTimezone=Asia/Ho_Chi_Minh&nullCatalogMeansCurrent=true --spring.datasource.druid.username=root --spring.datasource.druid.password=123456 --spring.data.redis.host=127.0.0.1 --spring.data.redis.port=6379 --spring.data.redis.password=xiaozhi_redis_2024"

        if [ "$QUIET" = "true" ]; then
            mvn spring-boot:run -Dspring-boot.run.arguments="$MVN_ARGS" >> "$LOG_DIR/manager-api.log" 2>&1 &
        else
            mvn spring-boot:run -Dspring-boot.run.arguments="$MVN_ARGS" 2>&1 | stream_with_prefix "$C_API" "API    " "$LOG_DIR/manager-api.log" &
        fi
        add_pid $!
        wait_for_port 8002 "Manager API" 90
    fi
fi

# ═══════════════════════════════════════════════════════════════════════════
#  4. Manager Web
# ═══════════════════════════════════════════════════════════════════════════
if should_run "web" && [ "$SKIP_WEB" = "false" ] && command -v npm &>/dev/null; then
    hdr "4/6  Manager Web (Vue)"

    if netstat -ano 2>/dev/null | grep -q ":8001.*LISTENING"; then
        ok "Manager Web already running on :8001"
    else
        cd "$PROJECT_ROOT/main/manager-web"
        if [ ! -d "node_modules" ]; then
            sys "Installing npm dependencies..."
            npm install --legacy-peer-deps 2>&1 | tail -3
        fi
        : > "$LOG_DIR/manager-web.log"

        if [ "$QUIET" = "true" ]; then
            npm run serve >> "$LOG_DIR/manager-web.log" 2>&1 &
        else
            npm run serve 2>&1 | stream_with_prefix "$C_WEB" "WEB    " "$LOG_DIR/manager-web.log" &
        fi
        add_pid $!
        wait_for_port 8001 "Manager Web" 60
    fi
fi

# ═══════════════════════════════════════════════════════════════════════════
#  5. Xiaozhi Server
# ═══════════════════════════════════════════════════════════════════════════
if should_run "server"; then
    hdr "5/6  Xiaozhi Server (AI Core)"

    activate_conda
    free_port 8000 "Xiaozhi Server"

    cd "$PROJECT_ROOT/main/xiaozhi-server"
    : > "$LOG_DIR/xiaozhi-server.log"

    if [ "$QUIET" = "true" ]; then
        python app.py >> "$LOG_DIR/xiaozhi-server.log" 2>&1 &
    else
        python app.py 2>&1 | stream_with_prefix "$C_SERVER" "SERVER " "$LOG_DIR/xiaozhi-server.log" &
    fi
    add_pid $!
    wait_for_port 8000 "Xiaozhi Server" 60
fi

# ═══════════════════════════════════════════════════════════════════════════
#  6. Teacher Portal
# ═══════════════════════════════════════════════════════════════════════════
if should_run "portal" && [ "$SKIP_PORTAL" = "false" ] && command -v npm &>/dev/null; then
    hdr "6/6  Teacher Portal (Next.js)"

    if netstat -ano 2>/dev/null | grep -q ":3000.*LISTENING"; then
        ok "Teacher Portal already running on :3000"
    else
        cd "$PROJECT_ROOT/main/teacher-portal"
        if [ ! -d "node_modules" ]; then
            sys "Installing npm dependencies..."
            npm install 2>&1 | tail -3
        fi
        : > "$LOG_DIR/teacher-portal.log"

        if [ "$QUIET" = "true" ]; then
            npm run dev >> "$LOG_DIR/teacher-portal.log" 2>&1 &
        else
            npm run dev 2>&1 | stream_with_prefix "$C_PORTAL" "PORTAL " "$LOG_DIR/teacher-portal.log" &
        fi
        add_pid $!
        wait_for_port 3000 "Teacher Portal" 30
    fi
fi

# ═══════════════════════════════════════════════════════════════════════════
#  Dashboard Summary
# ═══════════════════════════════════════════════════════════════════════════
echo ""
echo -e "${C_INFO}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RST}"
echo -e "${C_INFO}${BOLD}  All services running!${RST}"
echo -e "${C_INFO}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RST}"
echo ""
echo -e "  ${BOLD}Service               Port   Color    Log File${RST}"
echo -e "  ${DIM}──────────────────────────────────────────────────────────${RST}"
echo -e "  ${C_DOCKER}[DOCKER ]${RST} MySQL       3307   ${C_DOCKER}cyan${RST}     $LOG_DIR/docker.log"
echo -e "  ${C_DOCKER}[DOCKER ]${RST} Redis       6379   ${C_DOCKER}cyan${RST}     (docker logs)"
echo -e "  ${C_DOCKER}[DOCKER ]${RST} Qdrant      6333   ${C_DOCKER}cyan${RST}     (docker logs)"
echo -e "  ${C_VP}[VOICE  ]${RST} Voiceprint  8100   ${C_VP}magenta${RST}  $LOG_DIR/voiceprint.log"
echo -e "  ${C_API}[API    ]${RST} Manager API 8002   ${C_API}yellow${RST}   $LOG_DIR/manager-api.log"
echo -e "  ${C_WEB}[WEB    ]${RST} Manager Web 8001   ${C_WEB}green${RST}    $LOG_DIR/manager-web.log"
echo -e "  ${C_SERVER}[SERVER ]${RST} Xiaozhi AI  8000   ${C_SERVER}blue${RST}     $LOG_DIR/xiaozhi-server.log"
echo -e "  ${C_PORTAL}[PORTAL ]${RST} Teacher UI  3000   ${C_PORTAL}cyan${RST}     $LOG_DIR/teacher-portal.log"
echo ""
echo -e "  ${C_INFO}Admin Console:${RST}   ${BOLD}http://localhost:8001${RST}"
echo -e "  ${C_INFO}Teacher Portal:${RST}  ${BOLD}http://localhost:3000${RST}"
echo -e "  ${C_INFO}Qdrant:${RST}          ${BOLD}http://localhost:6333/dashboard${RST}"
echo ""
echo -e "  ${DIM}Logs stream below in real-time. Press ${BOLD}Ctrl+C${RST}${DIM} to stop all.${RST}"
echo -e "  ${DIM}Tip: Look for ${C_VP}[VOICE  ]${RST}${DIM} lines to see voiceprint results.${RST}"
echo ""
echo -e "${C_INFO}━━━━━━━━━━━━━━━━━━━━━ LIVE LOG ━━━━━━━━━━━━━━━━━━━━━━━━━━━${RST}"
echo ""

# Keep script alive — wait for all background processes
wait
