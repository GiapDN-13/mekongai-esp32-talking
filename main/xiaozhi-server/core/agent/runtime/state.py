"""Unified conversation state and state manager.

StateManager owns the single source of truth for the agent runtime.
Migration strategy:
  - Before swap: conn -> state (sync_from_conn reads)
  - After swap: state -> conn (sync_to_conn writes for ASR compatibility)
"""

from dataclasses import dataclass, field
from .events import Event, EventType


@dataclass
class ConversationState:
    """Single source of truth for the conversation runtime."""

    # Voice tracking
    voice_active: bool = False
    voice_start_ms: float = 0.0
    last_voice_end_ms: float = 0.0
    current_speech_ms: float = 0.0

    # Silence tracking
    silence_ms: float = 0.0

    # TTS state
    bot_is_speaking: bool = False
    tts_start_ms: float = 0.0

    # Barge-in accumulation (raw counts, skills decide thresholds)
    consecutive_human_frames: int = 0
    consecutive_echo_frames: int = 0
    pre_roll_buffer: list = field(default_factory=list)

    # Phase
    phase: str = "idle"

    # Operational goal (set by future cognitive layer)
    current_goal: str = "listen_accurately"


class StateManager:
    """Updates state from events. Pure state machine, no decisions."""

    def __init__(self):
        self.current = ConversationState()

    def update(self, event: Event):
        s = self.current

        if event.type == EventType.VOICE_STARTED:
            s.voice_active = True
            s.voice_start_ms = event.timestamp_ms
            s.silence_ms = 0.0
            s.consecutive_human_frames = 0
            s.consecutive_echo_frames = 0

        elif event.type == EventType.VOICE_STOPPED:
            s.voice_active = False
            s.last_voice_end_ms = event.timestamp_ms
            s.current_speech_ms = event.speech_ms

        elif event.type == EventType.VOICE_CONTINUING:
            s.current_speech_ms = event.speech_ms

        elif event.type == EventType.SILENCE_CONTINUING:
            s.silence_ms = event.silence_ms

        elif event.type == EventType.TTS_HUMAN_FRAME:
            s.consecutive_human_frames = event.consecutive_human_frames
            s.consecutive_echo_frames = 0

        elif event.type == EventType.TTS_ECHO_FRAME:
            s.consecutive_echo_frames = event.consecutive_echo_frames
            s.consecutive_human_frames = 0

        elif event.type == EventType.TTS_AMBIGUOUS_FRAME:
            # With device AEC active, ambiguous should not occur.
            # If it does, treat as human (AEC already removed echo).
            s.consecutive_human_frames += 1
            s.consecutive_echo_frames = 0

        elif event.type == EventType.TTS_PLAYBACK_STARTED:
            s.bot_is_speaking = True
            s.tts_start_ms = event.timestamp_ms

        elif event.type == EventType.TTS_PLAYBACK_STOPPED:
            s.bot_is_speaking = False

    def sync_from_conn(self, conn):
        """Read state from conn (conn = source of truth). Used before swap."""
        self.current.bot_is_speaking = getattr(conn, "client_is_speaking", False)
        self.current.voice_active = getattr(conn, "client_have_voice", False)

    def sync_to_conn(self, conn):
        """Sync agent state to conn for compatibility.

        IMPORTANT: Do NOT overwrite conn.client_have_voice or conn.client_voice_stop.
        These are managed by the VAD provider and ASR depends on them.
        Only write fields that the agent runtime exclusively owns.
        """
        pass
