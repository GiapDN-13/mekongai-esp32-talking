import re
import httpx
from core.utils.util import check_model_key
from core.providers.tts.base import TTSProviderBase
from config.logger import setup_logging

TAG = __name__
logger = setup_logging()

_EMOTION_KEYWORDS = {
    "solemn": re.compile(
        r"chiến tranh|hy sinh|mất mát|bi hùng|đau thương|tử sĩ|kháng chiến"
        r"|giải phóng|cách mạng|liệt sĩ|hy sinh|tổn thất|tang thương"
        r"|thảm sát|nô lệ|gian khổ",
        re.IGNORECASE,
    ),
    "admiration": re.compile(
        r"đẹp|tinh tế|tuyệt tác|nghệ thuật|hoa văn|men ngọc|lộng lẫy"
        r"|tinh xảo|điêu khắc|gốm sứ|tráng lệ|kiệt tác|mỹ thuật"
        r"|công phu|trau chuốt",
        re.IGNORECASE,
    ),
    "curiosity": re.compile(
        r"đoán xem|bạn có biết|thú vị|bất ngờ|bí mật|ít ai biết"
        r"|đặc biệt|kỳ lạ|ngạc nhiên|có bao giờ|tự hỏi",
        re.IGNORECASE,
    ),
}

_EMOTION_HINTS = {
    "solemn": (
        "For this passage, lower your pitch and speak with measured, "
        "respectful gravity. Pause slightly longer between phrases."
    ),
    "admiration": (
        "For this passage, let genuine wonder and admiration come through. "
        "Slow down slightly, soften your voice with awe."
    ),
    "curiosity": (
        "For this passage, speak with playful curiosity. "
        "Rise in pitch slightly, as if sharing an exciting secret."
    ),
}


class TTSProvider(TTSProviderBase):
    TTS_PARAM_CONFIG = [
        ("ttsRate", "speed", 0.25, 4, 1, lambda v: round(float(v), 2)),
    ]

    def __init__(self, config, delete_audio_file):
        super().__init__(config, delete_audio_file)
        self.api_key = config.get("api_key")
        self.api_url = config.get("api_url", "https://api.openai.com/v1/audio/speech")
        self.model = config.get("model", "gpt-4o-mini-tts")
        if config.get("private_voice"):
            self.voice = config.get("private_voice")
        else:
            self.voice = config.get("voice", "alloy")
        self.audio_file_type = config.get("format", "mp3")

        speed = config.get("speed", "1.0")
        self.speed = float(speed) if speed else 1.0

        instructions = config.get("instructions", "")
        self.instructions = instructions if instructions else None

        self._apply_percentage_params(config)

        self.output_file = config.get("output_dir", "tmp/")
        model_key_msg = check_model_key("TTS", self.api_key)
        if model_key_msg:
            logger.bind(tag=TAG).error(model_key_msg)

    @staticmethod
    def _get_emotion_hint(text):
        for emotion, pattern in _EMOTION_KEYWORDS.items():
            if pattern.search(text):
                return _EMOTION_HINTS[emotion]
        return None

    async def text_to_speak(self, text, output_file):
        emotion_hint = self._get_emotion_hint(text)
        effective_instructions = self.instructions
        if emotion_hint and effective_instructions:
            effective_instructions = f"{emotion_hint}\n\n{effective_instructions}"
        elif emotion_hint:
            effective_instructions = emotion_hint

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        data = {
            "model": self.model,
            "input": text,
            "voice": self.voice,
            "response_format": self.audio_file_type,
            "speed": self.speed,
        }
        if effective_instructions:
            data["instructions"] = effective_instructions

        async with httpx.AsyncClient(timeout=60) as client:
            async with client.stream("POST", self.api_url, json=data, headers=headers) as response:
                if response.status_code != 200:
                    error_body = await response.aread()
                    raise Exception(
                        f"OpenAI TTS failed: {response.status_code} - {error_body.decode()}"
                    )
                if output_file:
                    with open(output_file, "wb") as f:
                        async for chunk in response.aiter_bytes(4096):
                            f.write(chunk)
                else:
                    audio_bytes = b""
                    async for chunk in response.aiter_bytes(4096):
                        audio_bytes += chunk
                    return audio_bytes
