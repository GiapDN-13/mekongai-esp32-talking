"""Tests for core.utils.dialogue — Message and Dialogue classes."""

import uuid
from datetime import datetime
from core.utils.dialogue import Dialogue, Message


class TestMessage:
    def test_defaults(self):
        m = Message(role="user", content="hello")
        assert m.role == "user"
        assert m.content == "hello"
        assert m.tool_calls is None
        assert m.tool_call_id is None
        assert m.is_temporary is False
        assert m.uniq_id  # auto-generated UUID

    def test_explicit_uniq_id(self):
        m = Message(role="assistant", content="hi", uniq_id="custom-id")
        assert m.uniq_id == "custom-id"


class TestDialogue:
    def _make_dialogue(self, *messages: Message) -> Dialogue:
        d = Dialogue()
        for m in messages:
            d.put(m)
        return d

    # ------------------------------------------------------------------
    # put / getMessages
    # ------------------------------------------------------------------

    def test_put_and_get_llm_dialogue(self):
        d = Dialogue()
        d.put(Message(role="system", content="You are helpful."))
        d.put(Message(role="user", content="Hi"))
        d.put(Message(role="assistant", content="Hello!"))
        result = d.get_llm_dialogue()
        assert result[0]["role"] == "system"
        assert result[1]["role"] == "user"
        assert result[2]["role"] == "assistant"
        assert result[2]["content"] == "Hello!"

    def test_tool_message_format(self):
        d = Dialogue()
        d.put(Message(role="system", content="sys"))
        d.put(Message(role="tool", content="result", tool_call_id="tc-1"))
        result = d.get_llm_dialogue()
        tool_msg = [m for m in result if m["role"] == "tool"][0]
        assert tool_msg["tool_call_id"] == "tc-1"
        assert tool_msg["content"] == "result"

    def test_assistant_with_tool_calls(self):
        tool_calls = [{"id": "call_1", "function": {"name": "fn", "arguments": "{}"}}]
        d = Dialogue()
        d.put(Message(role="system", content="sys"))
        d.put(Message(role="assistant", tool_calls=tool_calls))
        result = d.get_llm_dialogue()
        assert result[1]["tool_calls"] == tool_calls
        assert "content" not in result[1]

    # ------------------------------------------------------------------
    # trim_history
    # ------------------------------------------------------------------

    def test_trim_history_no_trim_needed(self):
        d = Dialogue()
        d.put(Message(role="system", content="sys"))
        d.put(Message(role="user", content="q1"))
        d.put(Message(role="assistant", content="a1"))
        removed = d.trim_history(max_turns=5)
        assert removed == 0
        assert len(d.dialogue) == 3

    def test_trim_history_removes_old_turns(self):
        d = Dialogue()
        d.put(Message(role="system", content="sys"))
        for i in range(20):
            d.put(Message(role="user", content=f"q{i}"))
            d.put(Message(role="assistant", content=f"a{i}"))
        removed = d.trim_history(max_turns=3)
        assert removed > 0
        system_msgs = [m for m in d.dialogue if m.role == "system"]
        assert len(system_msgs) == 1

    def test_trim_history_preserves_tool_chains(self):
        d = Dialogue()
        d.put(Message(role="system", content="sys"))
        for i in range(8):
            d.put(Message(role="user", content=f"q{i}"))
            d.put(Message(role="assistant", content=f"a{i}"))
        # Add a tool-call chain at the end
        d.put(Message(role="user", content="use tool"))
        tc = [{"id": "c1", "function": {"name": "fn", "arguments": "{}"}}]
        d.put(Message(role="assistant", tool_calls=tc))
        d.put(Message(role="tool", content="tool-result", tool_call_id="c1"))
        d.put(Message(role="assistant", content="final answer"))

        d.trim_history(max_turns=3)

        roles = [m.role for m in d.dialogue if m.role != "system"]
        assert "tool" in roles, "Tool messages must survive trimming when part of kept turns"

    def test_trim_history_keeps_system_messages(self):
        d = Dialogue()
        d.put(Message(role="system", content="important system prompt"))
        for i in range(20):
            d.put(Message(role="user", content=f"q{i}"))
            d.put(Message(role="assistant", content=f"a{i}"))
        d.trim_history(max_turns=2)
        assert d.dialogue[0].role == "system"
        assert d.dialogue[0].content == "important system prompt"

    # ------------------------------------------------------------------
    # get_llm_dialogue_with_memory — injection
    # ------------------------------------------------------------------

    def test_memory_injection(self):
        d = Dialogue()
        d.put(Message(role="system", content="Hello <memory>old stuff</memory> world"))
        d.put(Message(role="user", content="hi"))
        result = d.get_llm_dialogue_with_memory("new memory content")
        sys_content = result[0]["content"]
        assert "new memory content" in sys_content
        assert "old stuff" not in sys_content

    def test_emotion_injection(self):
        d = Dialogue()
        d.put(Message(role="system", content="Prefix <emotional_state>neutral</emotional_state> suffix"))
        d.put(Message(role="user", content="hi"))
        result = d.get_llm_dialogue_with_memory(None, None, emotion_desc="happy and excited")
        sys_content = result[0]["content"]
        assert "happy and excited" in sys_content
        assert "neutral" not in sys_content

    def test_current_time_replacement(self):
        d = Dialogue()
        d.put(Message(role="system", content="The time is {{current_time}} now."))
        d.put(Message(role="user", content="what time"))
        result = d.get_llm_dialogue_with_memory(None)
        sys_content = result[0]["content"]
        assert "{{current_time}}" not in sys_content
        # Should contain HH:MM format
        now_hm = datetime.now().strftime("%H:%M")
        assert now_hm in sys_content

    def test_update_system_message_existing(self):
        d = Dialogue()
        d.put(Message(role="system", content="old"))
        d.update_system_message("new")
        assert d.dialogue[0].content == "new"

    def test_update_system_message_creates_if_absent(self):
        d = Dialogue()
        d.put(Message(role="user", content="hi"))
        d.update_system_message("sys prompt")
        system_msgs = [m for m in d.dialogue if m.role == "system"]
        assert len(system_msgs) == 1
        assert system_msgs[0].content == "sys prompt"
