"""Tests for core.utils.prompt_manager — language inference/resolution helpers."""

from core.utils.prompt_manager import _infer_reply_language_from_voice, resolve_reply_language


class TestInferReplyLanguageFromVoice:
    def test_vietnamese(self):
        assert _infer_reply_language_from_voice("vi-VN-HoaiMyNeural") == "Tiếng Việt"

    def test_chinese_zh(self):
        assert _infer_reply_language_from_voice("zh-CN-XiaoxiaoNeural") == "中文"

    def test_chinese_cmn(self):
        assert _infer_reply_language_from_voice("cmn-CN-XiaoxiaoNeural") == "中文"

    def test_english(self):
        assert _infer_reply_language_from_voice("en-US-JennyNeural") == "English"

    def test_japanese(self):
        assert _infer_reply_language_from_voice("ja-JP-NanamiNeural") == "日本語"

    def test_korean(self):
        assert _infer_reply_language_from_voice("ko-KR-SunHiNeural") == "한국어"

    def test_unknown_voice(self):
        assert _infer_reply_language_from_voice("fr-FR-SomeVoice") is None

    def test_empty_string(self):
        assert _infer_reply_language_from_voice("") is None

    def test_none_input(self):
        assert _infer_reply_language_from_voice(None) is None

    def test_whitespace(self):
        assert _infer_reply_language_from_voice("  vi-VN-Voice  ") == "Tiếng Việt"


class TestResolveReplyLanguage:
    def test_explicit_language(self):
        config = {
            "selected_module": {"TTS": "edge"},
            "TTS": {"edge": {"language": "Tiếng Việt", "voice": "en-US-JennyNeural"}},
        }
        assert resolve_reply_language(config) == "Tiếng Việt"

    def test_inferred_from_voice(self):
        config = {
            "selected_module": {"TTS": "edge"},
            "TTS": {"edge": {"voice": "vi-VN-HoaiMyNeural"}},
        }
        assert resolve_reply_language(config) == "Tiếng Việt"

    def test_default_chinese(self):
        config = {
            "selected_module": {"TTS": "edge"},
            "TTS": {"edge": {}},
        }
        assert resolve_reply_language(config) == "中文"

    def test_empty_config(self):
        assert resolve_reply_language({}) == "中文"

    def test_none_values_in_config(self):
        config = {"selected_module": None, "TTS": None}
        assert resolve_reply_language(config) == "中文"

    def test_explicit_empty_string_falls_through(self):
        config = {
            "selected_module": {"TTS": "edge"},
            "TTS": {"edge": {"language": "  ", "voice": "ja-JP-NanamiNeural"}},
        }
        # Empty-ish explicit language → infer from voice
        assert resolve_reply_language(config) == "日本語"
