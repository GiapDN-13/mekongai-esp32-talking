"""Stateless signal extraction from a single audio frame.

When device-side AEC is active, audio arriving at the server is already
clean — VAD result alone is sufficient to classify frames.
Spectral analysis is skipped entirely to reduce CPU and avoid false rejections.
"""

import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.providers.vad.base import VADProviderBase


@dataclass
class AudioPercept:
    """Raw signal from 1 frame. No history, no decisions."""

    timestamp_ms: float
    vad_result: bool
    rms_energy: float = 0.0
    spectral_flatness: float = 0.0
    frame_class: str = "silence"


class AudioPerception:
    """Wraps existing VAD. With device AEC, VAD alone is authoritative."""

    def __init__(self, vad_provider: "VADProviderBase"):
        self.vad = vad_provider

    def analyze(self, conn, opus_packet: bytes) -> AudioPercept:
        have_voice = getattr(conn, "client_have_voice", False)

        if have_voice:
            frame_class = "human"
        else:
            frame_class = "silence"

        return AudioPercept(
            timestamp_ms=time.time() * 1000,
            vad_result=have_voice,
            frame_class=frame_class,
        )

    def cleanup_conn(self, conn):
        """No resources to release."""
        pass
