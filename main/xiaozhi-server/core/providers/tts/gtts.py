import os
import uuid
from io import BytesIO
from datetime import datetime
from gtts import gTTS
from core.providers.tts.base import TTSProviderBase


class TTSProvider(TTSProviderBase):
    def __init__(self, config, delete_audio_file):
        super().__init__(config, delete_audio_file)
        self.language = config.get("language", "vi")
        self.tld = config.get("tld", "com.vn")
        self.slow = config.get("slow", False)
        self.audio_file_type = "mp3"

    def generate_filename(self, extension=".mp3"):
        return os.path.join(
            self.output_file,
            f"tts-{datetime.now().date()}@{uuid.uuid4().hex}{extension}",
        )

    async def text_to_speak(self, text, output_file):
        try:
            tts = gTTS(text=text, lang=self.language, tld=self.tld, slow=self.slow)
            if output_file:
                os.makedirs(os.path.dirname(output_file), exist_ok=True)
                tts.save(output_file)
            else:
                buf = BytesIO()
                tts.write_to_fp(buf)
                return buf.getvalue()
        except Exception as e:
            error_msg = f"gTTS request failed: {e}"
            raise Exception(error_msg)
