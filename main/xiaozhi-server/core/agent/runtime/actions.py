"""Output commands produced by skills and resolved by policy.

Actions are abstract intents. The executor translates them
into concrete side effects on the connection object.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List


class ActionType(Enum):
    NO_OP = auto()
    WAIT = auto()

    # Utterance lifecycle: set conn.client_voice_stop = True.
    # ASR handler auto-triggers on this flag (base.py line 100).
    MARK_UTTERANCE_COMPLETE = auto()

    DISCARD_AUDIO = auto()
    BUFFER_AUDIO = auto()

    # TTS control
    STOP_TTS = auto()
    STOP_TTS_AND_LISTEN = auto()

    # Connection
    EXTEND_TIMEOUT = auto()
    CLOSE_CONNECTION = auto()


@dataclass
class Action:
    type: ActionType
    confidence: float = 1.0
    skill_name: str = ""
    reason: str = ""
    pre_roll_audio: List[bytes] = field(default_factory=list)
    urgency: float = 0.5
