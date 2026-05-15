"""Episodic memory: tracks conversation turn patterns.

Records speaking durations and pause durations to build
a model of the current user's speech patterns. Skills query
this for adaptive thresholds (e.g., typical pause length
for THIS user in THIS session).
"""

from collections import deque
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TurnRecord:
    """One completed user turn."""

    speech_ms: float
    pause_before_ms: float
    turn_index: int


class EpisodicMemory:
    """Session-level pattern tracking for adaptive thresholds."""

    MAX_TURNS = 50
    DEFAULT_SILENCE_THRESHOLD_MS = 1000.0
    MIN_SILENCE_THRESHOLD_MS = 500.0
    MAX_SILENCE_THRESHOLD_MS = 2000.0

    def __init__(self):
        self._turns: deque = deque(maxlen=self.MAX_TURNS)
        self._turn_counter: int = 0
        self._mid_pause_samples: deque = deque(maxlen=30)

    def record_turn(self, speech_ms: float, pause_before_ms: float):
        """Record a completed user turn."""
        self._turn_counter += 1
        self._turns.append(
            TurnRecord(
                speech_ms=speech_ms,
                pause_before_ms=pause_before_ms,
                turn_index=self._turn_counter,
            )
        )

    def record_mid_pause(self, pause_ms: float):
        """Record a mid-utterance pause (user paused but resumed speaking)."""
        self._mid_pause_samples.append(pause_ms)

    def get_adaptive_silence_threshold(self) -> float:
        """Return silence threshold adapted to user patterns.

        Uses p75 of mid-utterance pauses + buffer.
        Falls back to default if insufficient data.
        """
        if len(self._mid_pause_samples) < 3:
            return self.DEFAULT_SILENCE_THRESHOLD_MS

        sorted_pauses = sorted(self._mid_pause_samples)
        p75_index = int(len(sorted_pauses) * 0.75)
        p75 = sorted_pauses[min(p75_index, len(sorted_pauses) - 1)]

        # Threshold = p75 + 200ms buffer (user's longest mid-pause + safety)
        threshold = p75 + 200.0
        return max(
            self.MIN_SILENCE_THRESHOLD_MS,
            min(threshold, self.MAX_SILENCE_THRESHOLD_MS),
        )

    def get_avg_speech_duration(self) -> Optional[float]:
        """Average user speech duration. None if insufficient data."""
        if len(self._turns) < 2:
            return None
        return sum(t.speech_ms for t in self._turns) / len(self._turns)

    @property
    def turn_count(self) -> int:
        return self._turn_counter

    @property
    def has_sufficient_data(self) -> bool:
        return len(self._mid_pause_samples) >= 3
