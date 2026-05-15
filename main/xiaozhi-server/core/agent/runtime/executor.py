"""Execute actions on the connection.

The executor is the ONLY module that writes to the connection.
All side effects flow through here so they can be traced and audited.
"""

import asyncio
from typing import TYPE_CHECKING

from .actions import Action, ActionType
from config.logger import setup_logging

if TYPE_CHECKING:
    from core.connection import ConnectionHandler

TAG = __name__
logger = setup_logging()


class ActionExecutor:
    """Translate abstract Actions into connection side effects."""

    async def execute(self, action: Action, conn: "ConnectionHandler"):
        if action.type == ActionType.NO_OP or action.type == ActionType.WAIT:
            return

        if action.type == ActionType.MARK_UTTERANCE_COMPLETE:
            await self._mark_utterance_complete(conn, action)

        elif action.type == ActionType.STOP_TTS:
            await self._stop_tts(conn)

        elif action.type == ActionType.STOP_TTS_AND_LISTEN:
            await self._stop_tts_and_listen(conn, action)

        elif action.type == ActionType.DISCARD_AUDIO:
            pass  # No-op: just don't forward audio to ASR

        elif action.type == ActionType.CLOSE_CONNECTION:
            await conn.close()

    async def _mark_utterance_complete(self, conn: "ConnectionHandler", action: Action):
        """Signal ASR that user finished speaking.

        Sets conn.client_voice_stop = True which triggers
        handle_voice_stop in the ASR provider (base.py line ~100).
        """
        conn.client_voice_stop = True
        logger.bind(tag=TAG).debug(
            f"[EXECUTOR] MARK_UTTERANCE_COMPLETE: {action.reason}"
        )

    async def _stop_tts(self, conn: "ConnectionHandler"):
        """Stop TTS playback (abort)."""
        from core.handle.abortHandle import handleAbortMessage
        await handleAbortMessage(conn)
        logger.bind(tag=TAG).info("[EXECUTOR] STOP_TTS")

    async def _stop_tts_and_listen(self, conn: "ConnectionHandler", action: Action):
        """Stop TTS and seed ASR with pre-roll to recover speech onset."""
        from core.handle.abortHandle import handleAbortMessage
        await handleAbortMessage(conn)

        conn.asr_audio.clear()
        if action.pre_roll_audio:
            conn.asr_audio.extend(action.pre_roll_audio)

        pre_roll_count = len(action.pre_roll_audio) if action.pre_roll_audio else 0
        logger.bind(tag=TAG).info(
            f"[EXECUTOR] STOP_TTS_AND_LISTEN: {action.reason} "
            f"(pre-roll: {pre_roll_count} frames, ~{pre_roll_count * 60}ms)"
        )
