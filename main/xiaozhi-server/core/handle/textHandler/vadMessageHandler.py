import asyncio
from typing import Dict, Any, TYPE_CHECKING

from config.logger import setup_logging
from core.handle.textMessageHandler import TextMessageHandler
from core.handle.textMessageType import TextMessageType

if TYPE_CHECKING:
    from core.connection import ConnectionHandler

TAG = __name__
logger = setup_logging()


class VadTextMessageHandler(TextMessageHandler):
    """Receives VAD notifications from ESP32 during Speaking state.

    With device-side AEC enabled, the firmware AFE VAD is authoritative:
    echo has already been cancelled, so VAD detected = real human speech.
    We directly trigger barge-in via abort.
    """

    @property
    def message_type(self) -> TextMessageType:
        return TextMessageType.VAD

    async def handle(self, conn: "ConnectionHandler", msg_json: Dict[str, Any]) -> None:
        if not conn.config.get("enable_voice_barge_in", True):
            return

        state = msg_json.get("state", "")
        if state != "detected":
            return

        if not conn.client_is_speaking:
            return

        # Debounce: don't trigger multiple times in quick succession
        import time
        last_vad = getattr(conn, "_last_firmware_vad_time", 0.0)
        now = time.time()
        if now - last_vad < 1.0:
            return
        conn._last_firmware_vad_time = now

        # Firmware AEC + AFE VAD = real speech. Stop TTS immediately.
        conn.client_have_voice = True

        from core.handle.abortHandle import handleAbortMessage
        await handleAbortMessage(conn)

        logger.bind(tag=TAG).info(
            "[VAD] Firmware VAD barge-in: stopped TTS, listening"
        )
