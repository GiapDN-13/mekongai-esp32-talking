"""Tests for core.handle.receiveAudioHandle — RMS, spectral flatness, reset state.

Mocks opuslib_next since the native Opus library may not be available in CI.
"""

import sys
from unittest.mock import MagicMock

# Mock native deps before importing
sys.modules.setdefault("opuslib_next", MagicMock())

import numpy as np
from core.handle.receiveAudioHandle import (
    _compute_rms,
    _compute_spectral_flatness,
    _reset_barge_in_state,
)


class TestComputeRms:
    def test_silence(self):
        pcm = np.zeros(960, dtype=np.int16)
        assert _compute_rms(pcm) == 0.0

    def test_loud_signal(self):
        pcm = np.full(960, 10000, dtype=np.int16)
        assert _compute_rms(pcm) > 5000

    def test_empty_array(self):
        pcm = np.array([], dtype=np.int16)
        assert _compute_rms(pcm) == 0.0

    def test_known_value(self):
        pcm = np.array([100, -100, 100, -100], dtype=np.int16)
        assert abs(_compute_rms(pcm) - 100.0) < 1.0

    def test_single_sample(self):
        pcm = np.array([500], dtype=np.int16)
        assert abs(_compute_rms(pcm) - 500.0) < 1.0


class TestComputeSpectralFlatness:
    def test_short_signal_returns_zero(self):
        pcm = np.array([1, 2, 3], dtype=np.int16)
        assert _compute_spectral_flatness(pcm) == 0.0

    def test_empty_returns_zero(self):
        pcm = np.array([], dtype=np.int16)
        assert _compute_spectral_flatness(pcm) == 0.0

    def test_silence_returns_zero(self):
        pcm = np.zeros(256, dtype=np.int16)
        assert _compute_spectral_flatness(pcm) == 0.0

    def test_pure_tone_low_flatness(self):
        t = np.arange(960)
        pcm = (10000 * np.sin(2 * np.pi * 440 * t / 16000)).astype(np.int16)
        flatness = _compute_spectral_flatness(pcm)
        assert flatness < 0.3  # tonal signals have lower flatness than white noise

    def test_white_noise_high_flatness(self):
        rng = np.random.RandomState(42)
        pcm = (rng.randn(960) * 5000).astype(np.int16)
        flatness = _compute_spectral_flatness(pcm)
        assert flatness > 0.1

    def test_returns_float(self):
        pcm = np.ones(256, dtype=np.int16) * 1000
        assert isinstance(_compute_spectral_flatness(pcm), float)


class TestResetBargeInState:
    def test_all_fields_reset(self):
        conn = MagicMock()
        conn._barge_in_counter = 5
        conn._echo_check_buffer = [b"data"]
        conn._sustained_voice_frames = 10
        conn._echo_cooldown_until = 999.0
        conn._barge_in_no_voice_streak = 3
        conn._spectral_human_votes = 7
        conn._spectral_echo_votes = 2

        _reset_barge_in_state(conn)

        assert conn._barge_in_counter == 0
        assert conn._echo_check_buffer == []
        assert conn._sustained_voice_frames == 0
        assert conn._echo_cooldown_until == 0.0
        assert conn._barge_in_no_voice_streak == 0
        assert conn._spectral_human_votes == 0
        assert conn._spectral_echo_votes == 0
