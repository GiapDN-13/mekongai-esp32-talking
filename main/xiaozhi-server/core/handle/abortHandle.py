import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler
TAG = __name__


async def handleAbortMessage(conn: "ConnectionHandler"):
    # Debounce: ignore rapid successive aborts (< 500ms apart)
    last_abort = getattr(conn, "_last_abort_time", 0.0)
    import time
    now = time.monotonic()
    if now - last_abort < 0.5:
        conn.logger.bind(tag=TAG).debug("Abort debounced (too rapid)")
        return
    conn._last_abort_time = now

    conn.logger.bind(tag=TAG).info("Abort message received")
    conn.client_abort = True
    conn.clear_queues()

    # Rollback story position so next "continue" replays the interrupted chunk
    backup = getattr(conn, "_rag_story_state_backup", None)
    if backup and backup.get("story_id"):
        conn._rag_story_state = dict(backup)
        conn.logger.bind(tag=TAG).info(
            f"Story position rolled back to part={backup.get('last_part_index')} "
            f"sub_offset={backup.get('sub_offset')}"
        )
    conn._rag_story_state_backup = None
    try:
        await conn.websocket.send(
            json.dumps({"type": "tts", "state": "stop", "session_id": conn.session_id})
        )
    except Exception as e:
        conn.logger.bind(tag=TAG).warning(f"Failed to send abort to client: {e}")
    conn.clearSpeakStatus()
    # Signal that this stop was from barge-in, not natural TTS end.
    # receive_audio uses this to skip post-TTS cooldown and listen immediately.
    conn._barge_in_active = True
    conn.logger.bind(tag=TAG).info("Abort message received-end")
