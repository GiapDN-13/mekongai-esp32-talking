import httpx
import openai
from openai.types import CompletionUsage
from config.logger import setup_logging
from core.utils.util import check_model_key
from core.providers.llm.base import LLMProviderBase

TAG = __name__
logger = setup_logging()


class LLMProvider(LLMProviderBase):
    def __init__(self, config):
        self.model_name = config.get("model_name")
        self.api_key = config.get("api_key")
        if "base_url" in config:
            self.base_url = config.get("base_url")
        else:
            self.base_url = config.get("url")
        timeout = config.get("timeout", 300)
        self.timeout = int(timeout) if timeout else 300

        param_defaults = {
            "max_tokens": int,
            "temperature": lambda x: round(float(x), 1),
            "top_p": lambda x: round(float(x), 1),
            "frequency_penalty": lambda x: round(float(x), 1),
        }

        for param, converter in param_defaults.items():
            value = config.get(param)
            try:
                setattr(
                    self,
                    param,
                    converter(value) if value not in (None, "") else None,
                )
            except (ValueError, TypeError):
                setattr(self, param, None)

        if self.temperature is None:
            self.temperature = 0.3

        logger.debug(
            f"意图识别参数初始化: {self.temperature}, {self.max_tokens}, {self.top_p}, {self.frequency_penalty}"
        )

        model_key_msg = check_model_key("LLM", self.api_key)
        if model_key_msg:
            logger.bind(tag=TAG).error(model_key_msg)
        self.client = openai.OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=httpx.Timeout(self.timeout))

    @staticmethod
    def normalize_dialogue(dialogue):
        """自动修复 dialogue 中缺失 content 的消息"""
        for msg in dialogue:
            if "role" in msg and "content" not in msg:
                msg["content"] = ""
        return dialogue

    def _log_usage(self, usage_info):
        """Log token usage including cache stats if available."""
        prompt_tokens = getattr(usage_info, 'prompt_tokens', '?')
        completion_tokens = getattr(usage_info, 'completion_tokens', '?')
        total_tokens = getattr(usage_info, 'total_tokens', '?')

        details = getattr(usage_info, 'prompt_tokens_details', None)
        cached = getattr(details, 'cached_tokens', 0) if details else 0

        if cached:
            logger.bind(tag=TAG).info(
                f"Token usage: input={prompt_tokens} (cached={cached}), "
                f"output={completion_tokens}, total={total_tokens}"
            )
        else:
            logger.bind(tag=TAG).info(
                f"Token usage: input={prompt_tokens}, "
                f"output={completion_tokens}, total={total_tokens}"
            )

    def response(self, session_id, dialogue, **kwargs):
        dialogue = self.normalize_dialogue(dialogue)

        request_params = {
            "model": self.model_name,
            "messages": dialogue,
            "stream": True,
            "stream_options": {"include_usage": True},
        }

        # 添加可选参数,只有当参数不为None时才添加
        optional_params = {
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "temperature": kwargs.get("temperature", self.temperature),
            "top_p": kwargs.get("top_p", self.top_p),
            "frequency_penalty": kwargs.get("frequency_penalty", self.frequency_penalty),
        }

        for key, value in optional_params.items():
            if value is not None:
                request_params[key] = value

        responses = self.client.chat.completions.create(**request_params)

        is_active = True
        for chunk in responses:
            try:
                delta = chunk.choices[0].delta if getattr(chunk, "choices", None) else None
                content = getattr(delta, "content", "") if delta else ""
            except IndexError:
                content = ""
            if content:
                if "<think>" in content:
                    is_active = False
                    content = content.split("<think>")[0]
                if "</think>" in content:
                    is_active = True
                    content = content.split("</think>")[-1]
                if is_active:
                    yield content

            usage_info = getattr(chunk, "usage", None)
            if isinstance(usage_info, CompletionUsage):
                self._log_usage(usage_info)

    def response_with_functions(self, session_id, dialogue, functions=None, **kwargs):
        dialogue = self.normalize_dialogue(dialogue)

        request_params = {
            "model": self.model_name,
            "messages": dialogue,
            "stream": True,
            "stream_options": {"include_usage": True},
            "tools": functions,
        }

        optional_params = {
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "temperature": kwargs.get("temperature", self.temperature),
            "top_p": kwargs.get("top_p", self.top_p),
            "frequency_penalty": kwargs.get("frequency_penalty", self.frequency_penalty),
        }

        for key, value in optional_params.items():
            if value is not None:
                request_params[key] = value

        stream = self.client.chat.completions.create(**request_params)

        for chunk in stream:
            if getattr(chunk, "choices", None):
                delta = chunk.choices[0].delta
                content = getattr(delta, "content", "")
                tool_calls = getattr(delta, "tool_calls", None)
                yield content, tool_calls

            usage_info = getattr(chunk, "usage", None)
            if isinstance(usage_info, CompletionUsage):
                self._log_usage(usage_info)
