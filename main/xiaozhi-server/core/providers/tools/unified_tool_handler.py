"""Unified tool handler: registers executors and routes LLM function calls."""

import json
from typing import Dict, List, Any, Optional
from config.logger import setup_logging
from plugins_func.loadplugins import auto_import_modules

from .base import ToolType
from plugins_func.register import Action, ActionResponse
from .unified_tool_manager import ToolManager
from .server_plugins import ServerPluginExecutor
from .server_mcp import ServerMCPExecutor
from .device_iot import DeviceIoTExecutor
from .device_mcp import DeviceMCPExecutor
from .mcp_endpoint import MCPEndpointExecutor

# Legacy placeholder substring from older default config (avoid non-ASCII in source)
_LEGACY_MCP_PLACEHOLDER = "\u4f60\u7684\u63a5\u5165\u70b9"


class UnifiedToolHandler:
    """Coordinates tool executors and LLM tool calls for a connection."""

    def __init__(self, conn):
        self.conn = conn
        self.config = conn.config
        self.logger = setup_logging()

        self.tool_manager = ToolManager(conn)

        self.server_plugin_executor = ServerPluginExecutor(conn)
        self.server_mcp_executor = ServerMCPExecutor(conn)
        self.device_iot_executor = DeviceIoTExecutor(conn)
        self.device_mcp_executor = DeviceMCPExecutor(conn)
        self.mcp_endpoint_executor = MCPEndpointExecutor(conn)

        self.tool_manager.register_executor(
            ToolType.SERVER_PLUGIN, self.server_plugin_executor
        )
        self.tool_manager.register_executor(
            ToolType.SERVER_MCP, self.server_mcp_executor
        )
        self.tool_manager.register_executor(
            ToolType.DEVICE_IOT, self.device_iot_executor
        )
        self.tool_manager.register_executor(
            ToolType.DEVICE_MCP, self.device_mcp_executor
        )
        self.tool_manager.register_executor(
            ToolType.MCP_ENDPOINT, self.mcp_endpoint_executor
        )

        self.finish_init = False

    @staticmethod
    def _skip_mcp_endpoint_url(url: str) -> bool:
        """True if URL is empty, null, or still the template placeholder."""
        if not url or url == "null":
            return True
        u = url.strip().lower()
        if _LEGACY_MCP_PLACEHOLDER in url:
            return True
        if "your-mcp-endpoint" in u:
            return True
        return False

    async def _initialize(self):
        """Load plugins and optional MCP / Home Assistant integrations."""
        try:
            auto_import_modules("plugins_func.functions")

            await self.server_mcp_executor.initialize()

            await self._initialize_mcp_endpoint()

            self._initialize_home_assistant()

            self.finish_init = True
            self.logger.debug("Unified tool handler initialized")

            self.current_support_functions()

        except Exception as e:
            self.logger.error(f"Unified tool handler init failed: {e}")

    async def _initialize_mcp_endpoint(self):
        """Connect to configured MCP endpoint WebSocket, if any."""
        try:
            from .mcp_endpoint import connect_mcp_endpoint

            mcp_endpoint_url = self.config.get("mcp_endpoint", "")

            if not self._skip_mcp_endpoint_url(mcp_endpoint_url):
                self.logger.info(f"Initializing MCP endpoint: {mcp_endpoint_url}")
                mcp_endpoint_client = await connect_mcp_endpoint(
                    mcp_endpoint_url, self.conn
                )

                if mcp_endpoint_client:
                    self.conn.mcp_endpoint_client = mcp_endpoint_client
                    self.logger.info("MCP endpoint initialized")
                else:
                    self.logger.warning("MCP endpoint initialization failed")

        except Exception as e:
            self.logger.error(f"MCP endpoint init failed: {e}")

    def _initialize_home_assistant(self):
        """Append HA device list to prompt when the plugin is available."""
        try:
            from plugins_func.functions.hass_init import append_devices_to_prompt

            append_devices_to_prompt(self.conn)
        except ImportError:
            pass
        except Exception as e:
            self.logger.error(f"Home Assistant init failed: {e}")

    def get_functions(self) -> List[Dict[str, Any]]:
        """Return OpenAI-style tool definitions for all registered tools."""
        return self.tool_manager.get_function_descriptions()

    def current_support_functions(self) -> List[str]:
        """Log and return registered tool names."""
        func_names = self.tool_manager.get_supported_tool_names()
        self.logger.info(f"Supported tools: {func_names}")
        return func_names

    def upload_functions_desc(self):
        """Invalidate tool cache after external changes."""
        self.tool_manager.refresh_tools()
        self.logger.info("Tool definitions refreshed")

    def has_tool(self, tool_name: str) -> bool:
        return self.tool_manager.has_tool(tool_name)

    async def handle_llm_function_call(
        self, conn, function_call_data: Dict[str, Any]
    ) -> Optional[ActionResponse]:
        """Dispatch a single or batch function call from the LLM."""
        try:
            if "function_calls" in function_call_data:
                responses = []
                for call in function_call_data["function_calls"]:
                    result = await self.tool_manager.execute_tool(
                        call["name"], call.get("arguments", {})
                    )
                    responses.append(result)
                return self._combine_responses(responses)

            function_name = function_call_data["name"]
            arguments = function_call_data.get("arguments", {})

            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments) if arguments else {}
                except json.JSONDecodeError:
                    self.logger.error(f"Invalid JSON for tool arguments: {arguments}")
                    return ActionResponse(
                        action=Action.ERROR,
                        response="Failed to parse tool arguments as JSON",
                    )

            self.logger.debug(f"Tool call: {function_name}, args={arguments}")
            try:
                if hasattr(self.conn, "mark_latency_tool_start"):
                    self.conn.mark_latency_tool_start(function_name)
            except Exception:
                pass

            result = await self.tool_manager.execute_tool(function_name, arguments)

            try:
                if hasattr(self.conn, "mark_latency_tool_end"):
                    self.conn.mark_latency_tool_end()
            except Exception:
                pass

            return result

        except Exception as e:
            self.logger.error(f"Function call handling error: {e}")
            return ActionResponse(action=Action.ERROR, response=str(e))

    def _combine_responses(self, responses: List[ActionResponse]) -> ActionResponse:
        """Merge batch tool results into one ActionResponse."""
        if not responses:
            return ActionResponse(action=Action.NONE, response="No response")

        for response in responses:
            if response.action == Action.ERROR:
                return response

        contents = []
        responses_text = []

        for response in responses:
            if response.content:
                contents.append(response.content)
            if response.response:
                responses_text.append(response.response)

        final_action = Action.RESPONSE
        for response in responses:
            if response.action == Action.REQLLM:
                final_action = Action.REQLLM
                break

        return ActionResponse(
            action=final_action,
            result="; ".join(contents) if contents else None,
            response="; ".join(responses_text) if responses_text else None,
        )

    async def register_iot_tools(self, descriptors: List[Dict[str, Any]]):
        self.device_iot_executor.register_iot_tools(descriptors)
        self.tool_manager.refresh_tools()
        self.logger.info(f"Registered IoT tools from {len(descriptors)} device(s)")

    def get_tool_statistics(self) -> Dict[str, int]:
        return self.tool_manager.get_tool_statistics()

    async def cleanup(self):
        try:
            await self.server_mcp_executor.cleanup()

            if (
                hasattr(self.conn, "mcp_endpoint_client")
                and self.conn.mcp_endpoint_client
            ):
                await self.conn.mcp_endpoint_client.close()

            self.logger.info("Tool handler cleanup finished")
        except Exception as e:
            self.logger.error(f"Tool handler cleanup failed: {e}")
