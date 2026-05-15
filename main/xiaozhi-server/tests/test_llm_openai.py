"""Tests for core.providers.llm.openai — normalize_dialogue, param parsing."""

from unittest.mock import MagicMock, patch


class TestNormalizeDialogue:
    def _get_cls(self):
        with patch("core.providers.llm.openai.openai.setup_logging", return_value=MagicMock()):
            with patch("core.providers.llm.openai.openai.check_model_key", return_value=None):
                with patch("openai.OpenAI"):
                    from core.providers.llm.openai.openai import LLMProvider
        return LLMProvider

    def test_adds_missing_content(self):
        LLMProvider = self._get_cls()
        dialogue = [
            {"role": "assistant", "tool_calls": [{"id": "1"}]},
            {"role": "user", "content": "hi"},
        ]
        result = LLMProvider.normalize_dialogue(dialogue)
        assert result[0]["content"] == ""
        assert result[1]["content"] == "hi"

    def test_preserves_existing_content(self):
        LLMProvider = self._get_cls()
        dialogue = [{"role": "user", "content": "hello"}]
        result = LLMProvider.normalize_dialogue(dialogue)
        assert result[0]["content"] == "hello"

    def test_empty_dialogue(self):
        LLMProvider = self._get_cls()
        assert LLMProvider.normalize_dialogue([]) == []

    def test_all_messages_have_content(self):
        LLMProvider = self._get_cls()
        dialogue = [
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "hello"},
        ]
        result = LLMProvider.normalize_dialogue(dialogue)
        for msg in result:
            assert "content" in msg
