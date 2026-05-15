# Voiceprint Recognition Service

Microservice nhận diện người nói (Speaker Identification) sử dụng **Resemblyzer** (GE2E model).
Tích hợp sẵn với hệ thống xiaozhi-esp32-server.

## Kiến trúc

```
ESP32 (mic) → WebSocket → ASR + Voiceprint (song song)
                                    ↓
                          POST /voiceprint/identify
                                    ↓
                          Resemblyzer embedding → Cosine similarity
                                    ↓
                          {"speaker_id": "test1", "score": 0.89}
                                    ↓
                          LLM nhận: {"speaker": "Minh", "content": "xin chào"}
```

## Quick Start

### 1. Cài đặt dependencies

```bash
cd main/voiceprint-service
pip install -r requirements.txt
```

### 2. Khởi chạy service

```bash
python app.py
# Service chạy tại http://localhost:8100
```

### 3. Đăng ký giọng nói

Cần file WAV (16kHz, mono, ít nhất 5-10 giây nói chuyện):

```bash
# Đăng ký từ file WAV
python register_speaker.py register --id test1 --audio /path/to/minh_voice.wav

# Hoặc thu âm trực tiếp từ microphone (cần sounddevice)
pip install sounddevice
python register_speaker.py record --id test1 --duration 10
```

### 4. Test nhận diện

```bash
python register_speaker.py identify --audio /path/to/test.wav --candidates test1,test2,test3
```

### 5. Quản lý

```bash
# Kiểm tra service
python register_speaker.py health

# Liệt kê speakers đã đăng ký
python register_speaker.py list

# Xóa speaker
python register_speaker.py delete --id test1
```

## Docker

```bash
docker compose up voiceprint-service -d
```

## API Endpoints

| Method | Path | Mô tả |
|--------|------|--------|
| GET | `/voiceprint/health?key=API_KEY` | Health check |
| POST | `/voiceprint/register` | Đăng ký giọng nói (speaker_id + WAV file) |
| POST | `/voiceprint/identify` | Nhận diện ai đang nói (speaker_ids + WAV file) |
| DELETE | `/voiceprint/{speaker_id}` | Xóa voiceprint |
| GET | `/voiceprint/list` | Liệt kê tất cả speakers |

## Environment Variables

| Variable | Default | Mô tả |
|----------|---------|--------|
| `VOICEPRINT_API_KEY` | `voiceprint-secret-key` | API key xác thực |
| `VOICEPRINT_PORT` | `8100` | Port service |
| `VOICEPRINT_DATA_DIR` | `./data/voiceprints` | Thư mục lưu embeddings |

## Cấu hình xiaozhi-server

Trong `config.yaml`:

```yaml
voiceprint:
  url: http://localhost:8100?key=voiceprint-secret-key
  speakers:
    - "test1,Minh,Minh là lập trình viên"
    - "test2,Lan,Lan là quản lý sản phẩm"
  similarity_threshold: 0.75
```

**Lưu ý:** `speaker_id` trong config phải khớp với ID đã đăng ký qua `/voiceprint/register`.

## Quy trình hoạt động

1. **Đăng ký**: Upload WAV → Resemblyzer trích xuất 256-dim embedding → Lưu vào disk
2. **Nhận diện**: Mỗi lần người dùng nói → WAV gửi đến service → So sánh cosine similarity với tất cả candidates → Trả về best match
3. **Tích hợp LLM**: Speaker name được inject vào message → LLM cá nhân hóa phản hồi

## Tips

- **Chất lượng audio đăng ký**: Nên 5-30 giây, giọng rõ ràng, ít tạp âm
- **Threshold**: Resemblyzer cosine similarity thường 0.7-0.95 cho cùng người. Đặt threshold 0.75 là hợp lý
- **Nhiều mẫu**: Có thể đăng ký lại (overwrite) với audio tốt hơn
