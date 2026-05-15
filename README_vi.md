[![Banners](docs/images/banner1.png)](https://github.com/xinnan-tech/xiaozhi-esp32-server)

<h1 align="center">Xiaozhi ESP32 Server — MekongAI Fork</h1>

<p align="center">
Backend cho trợ lý giọng nói thông minh <a href="https://github.com/78/xiaozhi-esp32">xiaozhi-esp32</a><br/>
Fork bởi <strong>MekongAI</strong> — bổ sung <strong>Voiceprint Recognition</strong>, <strong>RAG + Qdrant</strong>, và CLI Dashboard<br/>
Python + Java + Vue &nbsp;|&nbsp; MQTT/UDP + WebSocket &nbsp;|&nbsp; MCP endpoints
</p>

<p align="center">
  <a href="https://github.com/xinnan-tech/xiaozhi-esp32-server"><img alt="Upstream" src="https://img.shields.io/badge/upstream-xinnan--tech-blue"></a>
  <a href="https://github.com/xinnan-tech/xiaozhi-esp32-server/blob/main/LICENSE"><img alt="License" src="https://img.shields.io/badge/license-MIT-white?labelColor=black"></a>
</p>

---

## Mục lục

- [Yêu cầu hệ thống](#yêu-cầu-hệ-thống)
- [Cài đặt trên máy mới (từ đầu)](#cài-đặt-trên-máy-mới-từ-đầu)
- [Khởi chạy nhanh](#khởi-chạy-nhanh)
- [Cấu trúc project](#cấu-trúc-project)
- [Chi tiết từng service](#chi-tiết-từng-service)
- [Cấu hình](#cấu-hình)
- [Tính năng MekongAI bổ sung](#tính-năng-mekongai-bổ-sung)
- [Khắc phục sự cố](#khắc-phục-sự-cố)
- [Upstream](#upstream)

---

## Yêu cầu hệ thống

| Thành phần | Phiên bản tối thiểu | Ghi chú |
|---|---|---|
| **OS** | Windows 10/11, Ubuntu 20.04+, macOS 12+ | Windows khuyến nghị dùng Git Bash |
| **Docker Desktop** | 4.x+ | Bắt buộc — chạy MySQL, Redis, Qdrant |
| **Python** | 3.10 – 3.12 | Khuyến nghị dùng Conda |
| **Java JDK** | 17+ | Cho Manager API (Spring Boot) |
| **Maven** | 3.8+ | Build Manager API |
| **Node.js** | 18+ | Cho Manager Web (Vue 2) |
| **Git** | 2.x+ | Windows: cài Git for Windows (đi kèm Git Bash) |
| **RAM** | 8 GB+ | 4 GB nếu dùng toàn API (không chạy FunASR local) |

---

## Cài đặt trên máy mới (từ đầu)

### Bước 1: Clone repo

```bash
git clone https://github.com/MekongAI/xiaozhi-esp32-server.git
cd xiaozhi-esp32-server
```

### Bước 2: Cài đặt Docker Desktop

- **Windows/macOS**: Tải từ [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/)
- **Ubuntu**: Chạy `bash docker-setup.sh` (script có sẵn trong repo)

Sau khi cài, đảm bảo Docker đang chạy:

```bash
docker --version
docker compose version
```

### Bước 3: Tạo Conda environment

```bash
conda create -n xiaozhi-esp32-server python=3.10 -y
conda activate xiaozhi-esp32-server
```

### Bước 4: Cài Python dependencies

```bash
# Xiaozhi Server (core)
cd main/xiaozhi-server
pip install -r requirements.txt

# Voiceprint Service
cd ../voiceprint-service
pip install -r requirements.txt

cd ../..
```

### Bước 5: Cài Java + Maven (cho Manager API)

- **Windows**: Tải [JDK 21](https://adoptium.net/) và [Maven](https://maven.apache.org/download.cgi), thêm vào PATH
- **Ubuntu**: `sudo apt install openjdk-21-jdk maven`
- **macOS**: `brew install openjdk@21 maven`

Kiểm tra:

```bash
java -version
mvn --version
```

### Bước 6: Cài Node.js (cho Manager Web)

- **Windows/macOS**: Tải từ [nodejs.org](https://nodejs.org/) (LTS)
- **Ubuntu**: `sudo apt install nodejs npm` hoặc dùng [nvm](https://github.com/nvm-sh/nvm)

Cài dependencies cho frontend:

```bash
cd main/manager-web
npm install --legacy-peer-deps
cd ../..
```

### Bước 7: Cấu hình

Tạo file config override (không chỉnh file gốc `config.yaml`):

```bash
mkdir -p main/xiaozhi-server/data
cp main/xiaozhi-server/config.yaml main/xiaozhi-server/data/.config.yaml
```

Mở `main/xiaozhi-server/data/.config.yaml` và cấu hình các API key cần thiết:

```yaml
# Ví dụ tối thiểu — chỉ cần thay đổi phần bạn dùng
ASR:
  type: FunASR              # hoặc dùng API: DoubaoASR, XunfeiStreamASR, ...
  # Nếu dùng API, thêm api_key ở đây

LLM:
  type: OpenAICompatible
  api_key: "YOUR_API_KEY"
  model: "gpt-4o-mini"      # hoặc qwen-turbo, glm-4-flash, ...
  base_url: "https://api.openai.com/v1"

TTS:
  type: EdgeTTS              # Miễn phí, không cần key
  voice: vi-VN-HoaiMyNeural  # Giọng tiếng Việt

# Voiceprint (nhận dạng giọng nói)
voiceprint:
  url: http://localhost:8100?key=voiceprint-secret-key
  speakers:
    - "speaker1,Tên Người 1,Mô tả ngắn"
  similarity_threshold: 0.75
```

### Bước 8: Khởi chạy tất cả

```bash
# Linux / Git Bash (Windows)
bash start-all.sh

# Hoặc Windows CMD
start-all.bat
```

Xong! Truy cập:
- **Bảng điều khiển**: http://localhost:8001
- **Qdrant Dashboard**: http://localhost:6333/dashboard

---

## Khởi chạy nhanh

### Cách 1: CLI Dashboard (khuyến nghị)

```bash
bash start-all.sh
```

Hiển thị log realtime, mỗi service có màu riêng biệt:

| Prefix | Service | Port | Màu |
|---|---|---|---|
| `[DOCKER ]` | MySQL, Redis, Qdrant | 3307, 6379, 6333 | Cyan |
| `[VOICE  ]` | Voiceprint Service | 8100 | Magenta |
| `[API    ]` | Manager API | 8002 | Yellow |
| `[WEB    ]` | Manager Web | 8001 | Green |
| `[SERVER ]` | Xiaozhi AI Server | 8000 | Blue |

Nhấn `Ctrl+C` để dừng tất cả.

### Tùy chọn start-all.sh

```bash
bash start-all.sh --no-web       # Bỏ qua Manager Web
bash start-all.sh --only voiceprint  # Chỉ chạy Voiceprint Service
bash start-all.sh --quiet        # Log vào file, không hiện terminal
bash start-all.sh -h             # Xem trợ giúp
```

### Cách 2: Windows CMD

```cmd
start-all.bat
```

Mỗi service mở một cửa sổ CMD riêng có màu sắc khác nhau.

### Cách 3: Chạy từng service thủ công

```bash
# 1. Docker infrastructure
cd main/xiaozhi-server
docker compose up -d mysql redis qdrant

# 2. Voiceprint Service
conda activate xiaozhi-esp32-server
cd main/voiceprint-service
python app.py

# 3. Manager API
cd main/manager-api
mvn spring-boot:run -Dspring-boot.run.arguments="--spring.datasource.druid.url=jdbc:mysql://127.0.0.1:3307/xiaozhi_esp32_server?useUnicode=true&characterEncoding=UTF-8&serverTimezone=Asia/Ho_Chi_Minh&nullCatalogMeansCurrent=true --spring.datasource.druid.username=root --spring.datasource.druid.password=123456 --spring.data.redis.host=127.0.0.1 --spring.data.redis.port=6379 --spring.data.redis.password=xiaozhi_redis_2024"

# 4. Manager Web
cd main/manager-web
npm run serve

# 5. Xiaozhi Server
cd main/xiaozhi-server
python app.py
```

---

## Cấu trúc project

```
xiaozhi-esp32-server/
├── start-all.sh / .bat        # Khởi chạy tất cả service
├── stop-all.bat                # Dừng tất cả (Windows)
├── docker-setup.sh             # Cài Docker cho Ubuntu
│
├── main/
│   ├── xiaozhi-server/         # Python — AI Core Server
│   │   ├── app.py              #   Entry point (port 8000)
│   │   ├── config.yaml         #   Config mặc định (KHÔNG sửa trực tiếp)
│   │   ├── data/.config.yaml   #   Config override (tạo bằng tay)
│   │   ├── docker-compose.yml  #   MySQL + Redis + Qdrant + Voiceprint
│   │   ├── core/               #   Logic chính (ASR, LLM, TTS, VAD, ...)
│   │   ├── plugins/            #   Plugin mở rộng
│   │   └── models/             #   ML models (SileroVAD, SenseVoice)
│   │
│   ├── manager-api/            # Java Spring Boot — Admin Backend
│   │   └── src/                #   (port 8002)
│   │
│   ├── manager-web/            # Vue 2 — Admin Frontend
│   │   ├── src/                #   (port 8001)
│   │   └── package.json
│   │
│   └── voiceprint-service/     # Python FastAPI — Speaker Recognition
│       ├── app.py              #   Entry point (port 8100)
│       ├── register_speaker.py #   CLI utility
│       └── requirements.txt
│
├── docs/                       # Tài liệu gốc từ upstream
├── logs/                       # Runtime logs (gitignored)
└── README_vi.md                # File này
```

---

## Chi tiết từng service

### 1. Docker Infrastructure

| Container | Image | Port | Mô tả |
|---|---|---|---|
| `xiaozhi-esp32-server-mysql` | mysql:8.0 | 3307 → 3306 | Database cho Manager API |
| `xiaozhi-esp32-server-redis` | redis:7.2-alpine | 6379 | Session cache, rate limiting |
| `qdrant` | qdrant/qdrant:v1.13.2 | 6333, 6334 | Vector DB cho RAG |

### 2. Voiceprint Service (port 8100)

Microservice nhận diện người nói sử dụng **Resemblyzer** (GE2E model).

| API | Method | Mô tả |
|---|---|---|
| `/voiceprint/health?key=KEY` | GET | Health check |
| `/voiceprint/register` | POST | Đăng ký giọng nói |
| `/voiceprint/identify` | POST | Nhận diện ai đang nói |
| `/voiceprint/{id}` | DELETE | Xóa voiceprint |
| `/voiceprint/list` | GET | Liệt kê speakers |

Đăng ký nhanh qua CLI:

```bash
cd main/voiceprint-service
python register_speaker.py register --id speaker1 --audio /path/to/voice.wav
python register_speaker.py list
```

Hoặc đăng ký qua **Bảng điều khiển** (http://localhost:8001) → Voiceprint → Thu âm / Tải file.

### 3. Manager API (port 8002)

Java Spring Boot backend. Quản lý users, agents, devices, models, voiceprints.

### 4. Manager Web (port 8001)

Vue 2 frontend. Bảng điều khiển quản trị với các chức năng:

- Quản lý agent (cấu hình ASR/LLM/TTS/Memory)
- Quản lý thiết bị ESP32
- Cấu hình Voiceprint (thu âm, upload, lịch sử chat)
- Quản lý Knowledge Base (RAG)
- Xem lịch sử chat

### 5. Xiaozhi Server (port 8000)

Python AI core. Xử lý:

- WebSocket connection với ESP32
- ASR (Speech-to-Text)
- LLM (AI responses)
- TTS (Text-to-Speech)
- VAD (Voice Activity Detection)
- Voiceprint identification (gọi Voiceprint Service)
- RAG (Retrieval-Augmented Generation via Qdrant)

---

## Cấu hình

### File config

| File | Mục đích | Sửa? |
|---|---|---|
| `main/xiaozhi-server/config.yaml` | Config mặc định, tham khảo | KHÔNG sửa |
| `main/xiaozhi-server/data/.config.yaml` | Config override cá nhân | Sửa ở đây |
| `main/manager-api/src/main/resources/application-dev.yml` | DB/Redis connections | Sửa nếu đổi password |

### Cấu hình qua Bảng điều khiển

Sau khi chạy Manager API + Web, vào http://localhost:8001 → **Quản lý hệ thống** → **Tham số hệ thống** để cấu hình:

- API keys cho ASR, LLM, TTS
- Voiceprint API URL
- RAG settings

### Ports mặc định

| Port | Service | Giao thức |
|---|---|---|
| 3307 | MySQL | TCP |
| 6379 | Redis | TCP |
| 6333 | Qdrant REST + Dashboard | HTTP |
| 6334 | Qdrant gRPC | gRPC |
| 8000 | Xiaozhi Server (WebSocket) | WS |
| 8001 | Manager Web | HTTP |
| 8002 | Manager API | HTTP |
| 8003 | Xiaozhi HTTP (OTA, Vision) | HTTP |
| 8100 | Voiceprint Service | HTTP |

---

## Tính năng MekongAI bổ sung

Các tính năng được MekongAI thêm vào so với upstream:

### Voiceprint Recognition (Nhận dạng giọng nói)

Nhận diện **ai đang nói** theo thời gian thực:

1. **Đăng ký** giọng nói qua UI (thu âm mic, upload file, hoặc chọn từ lịch sử chat)
2. **Nhận diện** tự động song song với ASR — không ảnh hưởng tốc độ
3. **Cá nhân hóa** — LLM biết ai đang nói để trả lời phù hợp

Xem log nhận dạng realtime trong CLI Dashboard:

```
08:45:12 [VOICE  ] [IDENTIFY] Speaker identified: Minh (score: 0.87)
08:45:12 [SERVER ] [VOICEPRINT] SPEAKER IDENTIFIED >>> Minh <<< | Score: 0.870
```

### RAG + Qdrant

Tích hợp Retrieval-Augmented Generation với Qdrant vector database:

- Upload tài liệu qua bảng điều khiển → tự động chunking + embedding
- LLM tham khảo knowledge base trước khi trả lời
- Hỗ trợ nhiều collections cho nhiều agents

### CLI Dashboard

Script `start-all.sh` chạy tất cả services với log realtime có màu, thay vì phải mở nhiều terminal.

---

## Khắc phục sự cố

### start-all.sh bị dừng / không chạy

```bash
# Đảm bảo Docker Desktop đang mở
docker ps

# Kiểm tra port bị chiếm
netstat -ano | grep ":8100.*LISTENING"

# Xem log chi tiết
cat logs/voiceprint.log
cat logs/xiaozhi-server.log
```

### Không connect được MySQL

```bash
# Kiểm tra container
docker ps | grep mysql

# Restart containers
cd main/xiaozhi-server
docker compose down
docker compose up -d mysql redis qdrant
```

### Voiceprint Service không nhận audio

- Đảm bảo audio là WAV 16kHz mono (UI tự convert)
- Kiểm tra ffmpeg đã cài: `ffmpeg -version`
- Cài ffmpeg nếu thiếu:
  - Windows: `conda install ffmpeg` hoặc tải từ [ffmpeg.org](https://ffmpeg.org/download.html)
  - Ubuntu: `sudo apt install ffmpeg`

### Manager Web lỗi npm

```bash
cd main/manager-web
rm -rf node_modules
npm install --legacy-peer-deps
```

### Conda environment không activate trong start-all.sh

Đảm bảo conda đã được init cho bash:

```bash
conda init bash
# Restart terminal, sau đó:
bash start-all.sh
```

---

## Upstream

Dự án này fork từ [xinnan-tech/xiaozhi-esp32-server](https://github.com/xinnan-tech/xiaozhi-esp32-server).

Xem thêm:
- [Tài liệu triển khai gốc](./docs/Deployment.md)
- [Tài liệu triển khai toàn bộ module](./docs/Deployment_all.md)
- [FAQ](./docs/FAQ.md)
- [Danh sách tính năng đầy đủ](https://github.com/xinnan-tech/xiaozhi-esp32-server)

---

<p align="center">
  <strong>MekongAI</strong> — Spearheaded by Professor Siyuan Liu's Team (South China University of Technology)
</p>
