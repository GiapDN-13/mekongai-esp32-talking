"""Emit observation events from percepts.

The interpreter reports WHAT happened (transitions, raw durations).
It NEVER applies thresholds or makes decisions.
Skills are responsible for all judgments.
"""

from .events import Event, EventType, AudioFeatures
from .state import ConversationState
from .perception import AudioPercept


class AudioInterpreter:
    """Emit transitions and raw durations. No thresholds. No decisions."""

    def interpret(self, percept: AudioPercept, state: ConversationState) -> Event:
        now = percept.timestamp_ms

        # During TTS: classify mic signal spectrally (only if VAD detects voice)
        if state.bot_is_speaking and percept.vad_result:
            return self._interpret_during_tts(percept, state)

        # Transition: silence -> voice
        if percept.vad_result and not state.voice_active:
            return Event(
                type=EventType.VOICE_STARTED,
                timestamp_ms=now,
                audio=AudioFeatures(
                    rms_energy=percept.rms_energy,
                    spectral_flatness=percept.spectral_flatness,
                    frame_class=percept.frame_class,
                ),
            )

        # Transition: voice -> silence
        if not percept.vad_result and state.voice_active:
            return Event(
                type=EventType.VOICE_STOPPED,
                timestamp_ms=now,
                speech_ms=now - state.voice_start_ms if state.voice_start_ms > 0 else 0,
            )

        # Continuation: still speaking
        if percept.vad_result and state.voice_active:
            return Event(
                type=EventType.VOICE_CONTINUING,
                timestamp_ms=now,
                speech_ms=now - state.voice_start_ms if state.voice_start_ms > 0 else 0,
                audio=AudioFeatures(
                    rms_energy=percept.rms_energy,
                    spectral_flatness=percept.spectral_flatness,
                    frame_class=percept.frame_class,
                ),
            )

        # Continuation: still silent
        silence_ms = 0.0
        if state.last_voice_end_ms > 0:
            silence_ms = now - state.last_voice_end_ms

        return Event(
            type=EventType.SILENCE_CONTINUING,
            timestamp_ms=now,
            silence_ms=silence_ms,
        )

    def _interpret_during_tts(self, percept: AudioPercept, state: ConversationState) -> Event:
        """During TTS playback: emit per-frame spectral classification."""
        now = percept.timestamp_ms

        if percept.frame_class == "echo":
            return Event(
                type=EventType.TTS_ECHO_FRAME,
                timestamp_ms=now,
                consecutive_echo_frames=state.consecutive_echo_frames + 1,
                audio=AudioFeatures(
                    rms_energy=percept.rms_energy,
                    spectral_flatness=percept.spectral_flatness,
                    frame_class="echo",
                ),
            )

        if percept.frame_class == "human":
            return Event(
                type=EventType.TTS_HUMAN_FRAME,
                timestamp_ms=now,
                consecutive_human_frames=state.consecutive_human_frames + 1,
                audio=AudioFeatures(
                    rms_energy=percept.rms_energy,
                    spectral_flatness=percept.spectral_flatness,
                    frame_class="human",
                ),
            )

        return Event(
            type=EventType.TTS_AMBIGUOUS_FRAME,
            timestamp_ms=now,
            audio=AudioFeatures(
                rms_energy=percept.rms_energy,
                spectral_flatness=percept.spectral_flatness,
                frame_class="ambiguous",
            ),
        )
