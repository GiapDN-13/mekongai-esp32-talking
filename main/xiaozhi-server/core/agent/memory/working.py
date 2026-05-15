"""Pre-roll ring buffer for audio frames.

Maintains a fixed-size circular buffer of recent audio frames
so that when VAD triggers, we can include audio slightly before
the detection point (compensating for VAD latency).
"""

from collections import deque
from dataclasses import dataclass
from typing import List


@dataclass
class WorkingMemory:
    """Audio working memory: pre-roll buffer + current utterance frames."""

    PRE_ROLL_FRAMES: int = 15  # ~900ms at 60ms/frame

    def __init__(self, pre_roll_size: int = 15):
        self.PRE_ROLL_FRAMES = pre_roll_size
        self._pre_roll: deque = deque(maxlen=pre_roll_size)
        self._utterance_frames: List[bytes] = []
        self._collecting: bool = False

    def push_frame(self, opus_packet: bytes):
        """Always push to pre-roll. If collecting, also store in utterance."""
        self._pre_roll.append(opus_packet)
        if self._collecting:
            self._utterance_frames.append(opus_packet)

    def start_collecting(self):
        """Begin collecting utterance frames (include pre-roll)."""
        self._collecting = True
        self._utterance_frames = list(self._pre_roll)

    def stop_collecting(self) -> List[bytes]:
        """Stop collecting and return the utterance audio."""
        self._collecting = False
        frames = self._utterance_frames
        self._utterance_frames = []
        return frames

    def get_pre_roll(self) -> List[bytes]:
        """Return pre-roll buffer content."""
        return list(self._pre_roll)

    def discard(self):
        """Discard current collection without returning."""
        self._collecting = False
        self._utterance_frames = []

    @property
    def is_collecting(self) -> bool:
        return self._collecting
