from ..base import MemoryProviderBase, logger
import time
import json
import os
import yaml
from config.config_loader import get_project_dir
from config.manage_api_client import generate_and_save_chat_summary
import asyncio
from core.utils.util import check_model_key


short_term_memory_prompt = """
# Trợ lý ghi nhớ — Chatbot kể chuyện cho bé

## Nhiệm vụ
Từ đoạn hội thoại giữa Cô Trúc Linh (assistant) và bé (user), tổng hợp thông tin quan trọng về bé để phiên sau có thể cá nhân hóa trải nghiệm kể chuyện.

## Nguyên tắc ghi nhớ

### 1. Đánh giá 3 chiều (mỗi lần cập nhật phải thực hiện)
| Chiều         | Tiêu chí                          | Trọng số |
|---------------|-----------------------------------|----------|
| Tính thời sự  | Thông tin mới nhất ưu tiên hơn   | 40%      |
| Cảm xúc       | Bé thích/sợ/hào hứng mạnh       | 35%      |
| Liên kết      | Kết nối với thông tin khác        | 25%      |

### 2. Cập nhật động
- Khi bé đổi tên gọi (VD: "gọi con là Bống"): cập nhật tên, giữ tên cũ trong danh sách.
- Khi bé nghe xong truyện: chuyển từ "đang nghe" sang "đã nghe xong".
- Khi có mâu thuẫn: lấy thông tin MỚI NHẤT làm chuẩn.

### 3. Tối ưu không gian
- Viết ngắn gọn, dùng ký hiệu khi có thể.
- Khi tổng ký tự >= 800: xóa thông tin trọng số thấp và 3 phiên không nhắc lại.
- Gộp các mục trùng lặp (giữ timestamp mới nhất).

## Cấu trúc output
Output PHẢI là chuỗi JSON hợp lệ, KHÔNG giải thích, KHÔNG comment. Chỉ trích xuất từ hội thoại thực, KHÔNG bịa thêm.
```json
{
  "ho_so_be": {
    "ten": "",
    "ten_cu": [],
    "tuoi_uoc_luong": "",
    "dac_diem": [],
    "so_thich": [],
    "so_hai": []
  },
  "truyen": {
    "da_nghe_xong": [],
    "dang_nghe_do": "",
    "vi_tri_dung": "",
    "truyen_yeu_thich": [],
    "nhan_vat_thich": [],
    "nhan_vat_so": []
  },
  "tuong_tac": {
    "phong_cach": "",
    "hay_hoi_tai_sao": false,
    "thoi_diem_hay_nghe": "",
    "ghi_chu": []
  },
  "ky_uc_noi_bat": [
    "Cau noi/phan ung dang nho cua be (nguyen van)"
  ]
}
```
"""


def extract_json_data(json_code):
    start = json_code.find("```json")
    end = json_code.find("```", start + 1)
    if start == -1 or end == -1:
        try:
            jsonData = json.loads(json_code)
            return json_code
        except Exception as e:
            print("Error:", e)
        return ""
    jsonData = json_code[start + 7 : end]
    return jsonData


TAG = __name__


class MemoryProvider(MemoryProviderBase):
    def __init__(self, config, summary_memory):
        super().__init__(config)
        self.short_memory = ""
        self.save_to_file = True
        self.memory_path = get_project_dir() + "data/.memory.yaml"
        self.load_memory(summary_memory)

    def init_memory(
        self, role_id, llm, summary_memory=None, save_to_file=True, **kwargs
    ):
        super().init_memory(role_id, llm, **kwargs)
        self.save_to_file = save_to_file
        self.load_memory(summary_memory)

    def load_memory(self, summary_memory):
        if summary_memory or not self.save_to_file:
            self.short_memory = summary_memory
            return

        all_memory = {}
        if os.path.exists(self.memory_path):
            with open(self.memory_path, "r", encoding="utf-8") as f:
                all_memory = yaml.safe_load(f) or {}
        if self.role_id in all_memory:
            self.short_memory = all_memory[self.role_id]

    def save_memory_to_file(self):
        all_memory = {}
        if os.path.exists(self.memory_path):
            with open(self.memory_path, "r", encoding="utf-8") as f:
                all_memory = yaml.safe_load(f) or {}
        all_memory[self.role_id] = self.short_memory
        with open(self.memory_path, "w", encoding="utf-8") as f:
            yaml.dump(all_memory, f, allow_unicode=True)

    async def save_memory(self, msgs, session_id=None):
        model_info = getattr(self.llm, "model_name", str(self.llm.__class__.__name__))
        logger.bind(tag=TAG).debug(f"Memory save model: {model_info}")
        api_key = getattr(self.llm, "api_key", None)
        memory_key_msg = check_model_key("Memory LLM", api_key)
        if memory_key_msg:
            logger.bind(tag=TAG).error(memory_key_msg)
        if self.llm is None:
            logger.bind(tag=TAG).error("LLM chưa được thiết lập cho memory provider")
            return None

        if len(msgs) < 2:
            return None

        msgStr = ""
        for msg in msgs:
            content = msg.content

            # Extract content from JSON format if present (for ASR with emotion/language tags)
            try:
                if content and content.strip().startswith("{") and content.strip().endswith("}"):
                    data = json.loads(content)
                    if "content" in data:
                        content = data["content"]
            except (json.JSONDecodeError, KeyError, TypeError):
                # If parsing fails, use original content
                pass

            if msg.role == "user":
                msgStr += f"User: {content}\n"
            elif msg.role == "assistant":
                msgStr += f"Assistant: {content}\n"
        if self.short_memory and len(self.short_memory) > 0:
            msgStr += "Ký ức phiên trước:\n"
            msgStr += self.short_memory

        time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        msgStr += f"Thời gian hiện tại: {time_str}"

        if self.save_to_file:
            try:
                result = self.llm.response_no_stream(
                    short_term_memory_prompt,
                    msgStr,
                    max_tokens=2000,
                    temperature=0.2,
                )
                json_str = extract_json_data(result)
                json.loads(json_str)
                self.short_memory = json_str
                self.save_memory_to_file()
            except Exception as e:
                logger.bind(tag=TAG).error(f"Error in saving memory: {e}")
        else:
            summary_id = session_id if session_id else self.role_id
            await generate_and_save_chat_summary(summary_id)
        logger.bind(tag=TAG).info(
            f"Lưu memory thành công - Device: {self.role_id}, Session: {session_id}"
        )

        return self.short_memory

    async def query_memory(self, query: str) -> str:
        return self.short_memory
