"""Pure observation events emitted by the interpreter.

Events carry FACTS (transitions + raw durations).
They never carry JUDGMENTS (thresholds, confirmations).
Skills are responsible for interpreting meaning.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional


class EventType(Enum):
    # Transitions (one-shot, emitted at moment of change)
    VOICE_STARTED = auto()
    VOICE_STOPPED = auto()

    # Continuations (emitted every frame while state persists)
    VOICE_CONTINUING = auto()
    SILENCE_CONTINUING = auto()

    # During TTS: per-frame spectral classification (raw, no accumulation)
    TTS_ECHO_FRAME = auto()
    TTS_HUMAN_FRAME = auto()
    TTS_AMBIGUOUS_FRAME = auto()

    # System events (from protocol/connection, not audio analysis)
    TTS_PLAYBACK_STARTED = auto()
    TTS_PLAYBACK_STOPPED = auto()
    WAKE_WORD_DETECTED = auto()
    CONNECTION_TIMEOUT = auto()


@dataclass
class AudioFeatures:
    """Raw signal measurements for a single frame."""

    rms_energy: float = 0.0
    spectral_flatness: float = 0.0
    vad_probability: float = 0.0
    frame_class: str = "silence"


@dataclass
class Event:
    """Carries raw measurements. Skills interpret meaning."""

    type: EventType
    timestamp_ms: float

    # Raw durations (no thresholds applied)
    silence_ms: float = 0.0
    speech_ms: float = 0.0

    # Raw frame counts (no thresholds applied)
    consecutive_human_frames: int = 0
    consecutive_echo_frames: int = 0

    audio: Optional[AudioFeatures] = None
    source: str = "perception"
