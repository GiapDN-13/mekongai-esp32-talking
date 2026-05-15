"""Tests for plugins_func.register — FunctionRegistry, DeviceTypeRegistry, enums."""

from unittest.mock import MagicMock
from plugins_func.register import (
    Action,
    ActionResponse,
    ToolType,
    FunctionItem,
    FunctionRegistry,
    DeviceTypeRegistry,
)


class TestActionEnum:
    def test_error_code(self):
        assert Action.ERROR.code == -1

    def test_notfound_code(self):
        assert Action.NOTFOUND.code == 0

    def test_response_code(self):
        assert Action.RESPONSE.code == 2

    def test_reqllm_code(self):
        assert Action.REQLLM.code == 3


class TestToolTypeEnum:
    def test_wait_code(self):
        assert ToolType.WAIT.code == 2

    def test_system_ctl_code(self):
        assert ToolType.SYSTEM_CTL.code == 4


class TestActionResponse:
    def test_attributes(self):
        resp = ActionResponse(Action.RESPONSE, result="data", response="hello")
        assert resp.action == Action.RESPONSE
        assert resp.result == "data"
        assert resp.response == "hello"


class TestFunctionRegistry:
    def test_register_and_get(self):
        reg = FunctionRegistry()
        item = FunctionItem("test_fn", "desc", lambda: None, ToolType.WAIT)
        reg.register_function("test_fn", func_item=item)
        assert reg.get_function("test_fn") is item

    def test_unregister_existing(self):
        reg = FunctionRegistry()
        item = FunctionItem("fn", "d", lambda: None, ToolType.NONE)
        reg.register_function("fn", func_item=item)
        assert reg.unregister_function("fn") is True
        assert reg.get_function("fn") is None

    def test_unregister_nonexistent(self):
        reg = FunctionRegistry()
        assert reg.unregister_function("ghost") is False

    def test_get_all_functions(self):
        reg = FunctionRegistry()
        item1 = FunctionItem("a", "da", lambda: None, ToolType.NONE)
        item2 = FunctionItem("b", "db", lambda: None, ToolType.WAIT)
        reg.register_function("a", func_item=item1)
        reg.register_function("b", func_item=item2)
        all_fns = reg.get_all_functions()
        assert len(all_fns) == 2

    def test_get_all_function_desc(self):
        reg = FunctionRegistry()
        desc = {"type": "function", "function": {"name": "x"}}
        item = FunctionItem("x", desc, lambda: None, ToolType.WAIT)
        reg.register_function("x", func_item=item)
        descs = reg.get_all_function_desc()
        assert descs == [desc]


class TestDeviceTypeRegistry:
    def test_generate_device_type_id_deterministic(self):
        registry = DeviceTypeRegistry()
        descriptor = {
            "name": "light",
            "properties": {"brightness": {}, "color": {}},
            "methods": {"turn_on": {}, "turn_off": {}},
        }
        id1 = registry.generate_device_type_id(descriptor)
        id2 = registry.generate_device_type_id(descriptor)
        assert id1 == id2

    def test_generate_device_type_id_format(self):
        registry = DeviceTypeRegistry()
        descriptor = {
            "name": "light",
            "properties": {"brightness": {}},
            "methods": {"turn_on": {}},
        }
        type_id = registry.generate_device_type_id(descriptor)
        assert type_id.startswith("light:")
        assert "brightness" in type_id
        assert "turn_on" in type_id

    def test_register_and_get_device_functions(self):
        registry = DeviceTypeRegistry()
        funcs = {"fn1": FunctionItem("fn1", "d", lambda: None, ToolType.IOT_CTL)}
        registry.register_device_type("type-1", funcs)
        assert registry.get_device_functions("type-1") == funcs

    def test_get_unregistered_type_returns_empty(self):
        registry = DeviceTypeRegistry()
        assert registry.get_device_functions("unknown") == {}
