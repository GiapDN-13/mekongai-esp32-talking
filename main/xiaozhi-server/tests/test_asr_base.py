"""Tests for core.providers.asr.base — echo detection, PCM->WAV, enhanced text.

Mocks opuslib_next since the native Opus library may not be available in CI.
"""

import io
import sys
import json
import wave
from unittest.mock import MagicMock

# Mock opuslib_next before any import of asr.base
sys.modules.setdefault("opuslib_next", MagicMock())

from core.providers.asr.base import ASRProviderBase


class _ConcreteASR(ASRProviderBase):
    """Minimal concrete subclass for testing base methods."""
    async def speech_to_text(self, opus_data, session_id, audio_format="opus", artifacts=None):
        return "dummy", None


class TestTextOverlapRatio:
    def test_full_overlap(self):
        assert ASRProviderBase._text_overlap_ratio("hello world", "hello world foo") == 1.0

    def test_no_overlap(self):
        assert ASRProviderBase._text_overlap_ratio("abc def", "xyz uvw") == 0.0

    def test_partial_overlap(self):
        ratio = ASRProviderBase._text_overlap_ratio("hello world foo", "hello world bar")
        assert 0.3 < ratio < 0.8

    def test_empty_asr(self):
        assert ASRProviderBase._text_overlap_ratio("", "some text") == 0.0

    def test_empty_tts(self):
        assert ASRProviderBase._text_overlap_ratio("hello", "") == 0.0

    def test_identical(self):
        assert ASRProviderBase._text_overlap_ratio("xin chào", "xin chào") == 1.0

    def test_single_word_match(self):
        assert ASRProviderBase._text_overlap_ratio("hello", "hello world") == 1.0

    def test_single_word_no_match(self):
        assert ASRProviderBase._text_overlap_ratio("hello", "world") == 0.0


class TestBuildEnhancedText:
    def setup_method(self):
        self.asr = _ConcreteASR()

    def test_with_speaker_and_confidence(self):
        result = self.asr._build_enhanced_text("xin chào", "Nguyen", 0.95)
        data = json.loads(result)
        assert data["speaker"] == "Nguyen"
        assert data["content"] == "xin chào"
        assert data["confidence"] == 0.95

    def test_with_speaker_no_confidence(self):
        result = self.asr._build_enhanced_text("hello", "John", 0.0)
        data = json.loads(result)
        assert data["speaker"] == "John"
        assert "confidence" not in data

    def test_without_speaker(self):
        result = self.asr._build_enhanced_text("hello", "", 0.0)
        assert result == "hello"

    def test_none_speaker(self):
        result = self.asr._build_enhanced_text("hello", None, 0.0)
        assert result == "hello"

    def test_whitespace_speaker(self):
        result = self.asr._build_enhanced_text("hello", "   ", 0.0)
        assert result == "hello"


class TestPcmToWav:
    def setup_method(self):
        self.asr = _ConcreteASR()

    def test_valid_pcm_produces_wav(self):
        pcm = b"\x00\x01" * 1600
        wav_data = self.asr._pcm_to_wav(pcm)
        assert len(wav_data) > 44
        buf = io.BytesIO(wav_data)
        with wave.open(buf, "rb") as wf:
            assert wf.getnchannels() == 1
            assert wf.getsampwidth() == 2
            assert wf.getframerate() == 16000

    def test_empty_pcm_returns_empty(self):
        assert self.asr._pcm_to_wav(b"") == b""

    def test_odd_length_pcm_truncated(self):
        pcm = b"\x00\x01\x02"
        wav_data = self.asr._pcm_to_wav(pcm)
        buf = io.BytesIO(wav_data)
        with wave.open(buf, "rb") as wf:
            frames = wf.readframes(wf.getnframes())
            assert len(frames) == 2
