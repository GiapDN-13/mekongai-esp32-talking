import json
import boto3
from config.logger import setup_logging
from core.providers.llm.base import LLMProviderBase

TAG = __name__
logger = setup_logging()


class LLMProvider(LLMProviderBase):
    def __init__(self, config):
        self.model_id = config.get("model_id", "anthropic.claude-3-5-sonnet-20241022-v2:0")
        self.region = config.get("region", "us-east-1")
        self.max_tokens = int(config.get("max_tokens", 600))
        self.temperature = float(config.get("temperature", 0.3))

        aws_access_key_id = config.get("aws_access_key_id")
        aws_secret_access_key = config.get("aws_secret_access_key")

        session_kwargs = {"region_name": self.region}
        if aws_access_key_id and aws_secret_access_key:
            session_kwargs["aws_access_key_id"] = aws_access_key_id
            session_kwargs["aws_secret_access_key"] = aws_secret_access_key

        session = boto3.Session(**session_kwargs)
        self.client = session.client("bedrock-runtime")
        logger.bind(tag=TAG).info(f"Bedrock LLM initialized: model={self.model_id}, region={self.region}")

    def _build_messages(self, dialogue):
        """Convert OpenAI-style dialogue to Bedrock Converse format."""
        system_prompts = []
        messages = []

        for msg in dialogue:
            role = msg.get("role", "")
            content = msg.get("content", "") or ""

            if role == "system":
                system_prompts.append({"text": content})
            elif role == "assistant":
                messages.append({"role": "assistant", "content": [{"text": content}]})
            else:
                messages.append({"role": "user", "content": [{"text": content}]})

        # Bedrock requires messages to start with user and alternate roles
        if messages and messages[0]["role"] != "user":
            messages.insert(0, {"role": "user", "content": [{"text": ""}]})

        # Merge consecutive same-role messages
        merged = []
        for msg in messages:
            if merged and merged[-1]["role"] == msg["role"]:
                merged[-1]["content"].extend(msg["content"])
            else:
                merged.append(msg)

        return system_prompts, merged

    def response(self, session_id, dialogue, **kwargs):
        system_prompts, messages = self._build_messages(dialogue)

        inference_config = {
            "maxTokens": kwargs.get("max_tokens") or self.max_tokens,
            "temperature": kwargs.get("temperature") or self.temperature,
        }

        request_params = {
            "modelId": self.model_id,
            "messages": messages,
            "inferenceConfig": inference_config,
        }
        if system_prompts:
            request_params["system"] = system_prompts

        response = self.client.converse_stream(**request_params)

        is_active = True
        input_tokens = 0
        output_tokens = 0

        for event in response["stream"]:
            if "contentBlockDelta" in event:
                delta = event["contentBlockDelta"]["delta"]
                text = delta.get("text", "")
                if text:
                    if "<think>" in text:
                        is_active = False
                        text = text.split("<think>")[0]
                    if "</think>" in text:
                        is_active = True
                        text = text.split("</think>")[-1]
                    if is_active and text:
                        yield text

            elif "metadata" in event:
                usage = event["metadata"].get("usage", {})
                input_tokens = usage.get("inputTokens", 0)
                output_tokens = usage.get("outputTokens", 0)

        if input_tokens or output_tokens:
            logger.bind(tag=TAG).info(
                f"Token usage: input={input_tokens}, output={output_tokens}, "
                f"total={input_tokens + output_tokens}"
            )

    def response_with_functions(self, session_id, dialogue, functions=None, **kwargs):
        """Bedrock Converse supports tool use natively."""
        system_prompts, messages = self._build_messages(dialogue)

        inference_config = {
            "maxTokens": kwargs.get("max_tokens") or self.max_tokens,
            "temperature": kwargs.get("temperature") or self.temperature,
        }

        request_params = {
            "modelId": self.model_id,
            "messages": messages,
            "inferenceConfig": inference_config,
        }
        if system_prompts:
            request_params["system"] = system_prompts

        # Convert OpenAI function format to Bedrock tool config
        if functions:
            tool_config = self._convert_tools(functions)
            if tool_config:
                request_params["toolConfig"] = tool_config

        response = self.client.converse_stream(**request_params)

        current_tool_call = None
        tool_call_args = ""

        for event in response["stream"]:
            if "contentBlockStart" in event:
                start = event["contentBlockStart"].get("start", {})
                if "toolUse" in start:
                    current_tool_call = {
                        "id": start["toolUse"]["toolUseId"],
                        "function": {"name": start["toolUse"]["name"], "arguments": ""},
                    }
                    tool_call_args = ""

            elif "contentBlockDelta" in event:
                delta = event["contentBlockDelta"]["delta"]
                if "text" in delta:
                    yield delta["text"], None
                elif "toolUse" in delta:
                    tool_call_args += delta["toolUse"].get("input", "")

            elif "contentBlockStop" in event:
                if current_tool_call:
                    current_tool_call["function"]["arguments"] = tool_call_args
                    # Yield in OpenAI-compatible format
                    tool_call_obj = type("ToolCall", (), {
                        "index": 0,
                        "id": current_tool_call["id"],
                        "function": type("Function", (), {
                            "name": current_tool_call["function"]["name"],
                            "arguments": tool_call_args,
                        })(),
                        "type": "function",
                    })()
                    yield "", [tool_call_obj]
                    current_tool_call = None
                    tool_call_args = ""

    @staticmethod
    def _convert_tools(openai_tools):
        """Convert OpenAI tools format to Bedrock toolConfig format."""
        bedrock_tools = []
        for tool in openai_tools:
            if tool.get("type") == "function":
                func = tool["function"]
                bedrock_tool = {
                    "toolSpec": {
                        "name": func["name"],
                        "description": func.get("description", ""),
                        "inputSchema": {
                            "json": func.get("parameters", {"type": "object", "properties": {}})
                        },
                    }
                }
                bedrock_tools.append(bedrock_tool)

        if bedrock_tools:
            return {"tools": bedrock_tools}
        return None
