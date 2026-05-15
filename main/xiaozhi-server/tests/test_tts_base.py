"""Tests for core.providers.tts.base — sentence boundary, text splitting.

Mocks opuslib_next since the native Opus library may not be available in CI.
"""

import sys
from unittest.mock import MagicMock

# Mock native deps before importing tts.base
sys.modules.setdefault("opuslib_next", MagicMock())

from core.providers.tts.base import TTSProviderBase


class TestIsSentenceBoundary:
    def test_non_dot_always_true(self):
        assert TTSProviderBase._is_sentence_boundary("hello!", 5) is True

    def test_dot_after_letter(self):
        assert TTSProviderBase._is_sentence_boundary("end.", 3) is True

    def test_dot_between_digits_not_boundary(self):
        assert TTSProviderBase._is_sentence_boundary("3.5", 1) is False

    def test_dot_digit_then_letter_not_boundary(self):
        assert TTSProviderBase._is_sentence_boundary("3.5kg", 1) is False

    def test_dot_at_end_after_digit_not_boundary(self):
        assert TTSProviderBase._is_sentence_boundary("price is 3.", 10) is False

    def test_dot_after_digit_then_space(self):
        assert TTSProviderBase._is_sentence_boundary("3. Next", 1) is True

    def test_dot_no_digit_before(self):
        assert TTSProviderBase._is_sentence_boundary("ok.", 2) is True

    def test_dot_at_position_zero(self):
        assert TTSProviderBase._is_sentence_boundary(".hello", 0) is True


class TestSplitLongText:
    def test_short_text_single_segment(self):
        result = TTSProviderBase._split_long_text("Hello world", max_len=150)
        assert result == ["Hello world"]

    def test_long_text_splits_at_comma(self):
        text = "A" * 80 + "," + "B" * 80
        result = TTSProviderBase._split_long_text(text, max_len=100)
        assert len(result) >= 2
        assert result[0].endswith(",")

    def test_no_punctuation_splits_at_max(self):
        text = "A" * 300
        result = TTSProviderBase._split_long_text(text, max_len=150)
        assert len(result) >= 2
        # The split func uses best=max_len when no punct found, so first chunk is max_len+1 chars
        assert all(len(s) <= 151 for s in result)

    def test_chinese_punctuation_split(self):
        text = "你好世界" * 20 + "，" + "再见" * 20
        result = TTSProviderBase._split_long_text(text, max_len=50)
        assert len(result) >= 2

    def test_preserves_all_text(self):
        text = "Hello, world. This is a test! Really? Yes; indeed."
        result = TTSProviderBase._split_long_text(text, max_len=20)
        joined = "".join(result)
        assert joined == text

    def test_exact_max_len(self):
        text = "A" * 150
        result = TTSProviderBase._split_long_text(text, max_len=150)
        assert result == [text]

    def test_decimal_not_split(self):
        text = "The price is 3.5 million dong, very expensive indeed and more text here to fill"
        result = TTSProviderBase._split_long_text(text, max_len=60)
        joined = "".join(result)
        assert "3.5" in joined
