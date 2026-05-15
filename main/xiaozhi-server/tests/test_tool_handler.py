"""Tests for tool handler — _skip_mcp_endpoint_url, _combine_responses."""

from unittest.mock import MagicMock, patch
from plugins_func.register import Action, ActionResponse


def _get_handler_cls():
    with patch("core.providers.tools.unified_tool_handler.setup_logging", return_value=MagicMock()):
        with patch("core.providers.tools.unified_tool_handler.auto_import_modules"):
            from core.providers.tools.unified_tool_handler import UnifiedToolHandler
    return UnifiedToolHandler


class TestSkipMcpEndpointUrl:
    def setup_method(self):
        self.cls = _get_handler_cls()

    def test_empty_string(self):
        assert self.cls._skip_mcp_endpoint_url("") is True

    def test_none(self):
        assert self.cls._skip_mcp_endpoint_url(None) is True

    def test_null_string(self):
        assert self.cls._skip_mcp_endpoint_url("null") is True

    def test_placeholder_legacy(self):
        assert self.cls._skip_mcp_endpoint_url("wss://你的接入点/mcp") is True

    def test_placeholder_english(self):
        assert self.cls._skip_mcp_endpoint_url("wss://your-mcp-endpoint/v1") is True

    def test_valid_url(self):
        assert self.cls._skip_mcp_endpoint_url("wss://mcp.example.com/v1") is False

    def test_localhost_valid(self):
        assert self.cls._skip_mcp_endpoint_url("ws://localhost:8080/mcp") is False


class TestCombineResponses:
    def setup_method(self):
        cls = _get_handler_cls()
        conn = MagicMock()
        conn.config = {}
        with patch.object(cls, "__init__", lambda self, c: None):
            self.handler = cls.__new__(cls)
            self.handler.conn = conn
            self.handler.logger = MagicMock()

    def test_empty_responses(self):
        result = self.handler._combine_responses([])
        assert result.action == Action.NONE

    def test_single_error_propagates(self):
        responses = [
            ActionResponse(action=Action.RESPONSE, result="ok"),
            ActionResponse(action=Action.ERROR, response="fail"),
        ]
        result = self.handler._combine_responses(responses)
        assert result.action == Action.ERROR

    def test_reqllm_takes_priority(self):
        responses = [
            ActionResponse(action=Action.RESPONSE, result="a", response="ra"),
            ActionResponse(action=Action.REQLLM, result="b", response="rb"),
        ]
        # _combine_responses accesses .content — ActionResponse uses .result
        # Patch objects to add .content alias
        for r in responses:
            r.content = r.result
        result = self.handler._combine_responses(responses)
        assert result.action == Action.REQLLM

    def test_results_joined(self):
        responses = [
            ActionResponse(action=Action.RESPONSE, result="r1", response="resp1"),
            ActionResponse(action=Action.RESPONSE, result="r2", response="resp2"),
        ]
        for r in responses:
            r.content = r.result
        result = self.handler._combine_responses(responses)
        assert "resp1" in result.response
        assert "resp2" in result.response

    def test_single_success(self):
        r = ActionResponse(action=Action.RESPONSE, result="data", response="ok")
        r.content = r.result
        result = self.handler._combine_responses([r])
        assert result.action == Action.RESPONSE
