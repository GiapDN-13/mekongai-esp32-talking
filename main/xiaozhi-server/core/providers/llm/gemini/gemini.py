import os, json, uuid
from types import SimpleNamespace
from typing import Any, Dict, List

import requests
from google import generativeai as genai
from google.generativeai import types, GenerationConfig

from core.providers.llm.base import LLMProviderBase
from core.utils.util import check_model_key
from config.logger import setup_logging
from requests import RequestException

log = setup_logging()
TAG = __name__


def test_proxy(proxy_url: str, test_url: str) -> bool:
    try:
        resp = requests.get(test_url, proxies={"http": proxy_url, "https": proxy_url})
        return 200 <= resp.status_code < 400
    except RequestException:
        return False


def setup_proxy_env(http_proxy: str | None, https_proxy: str | None):
    """
    分别测试 HTTP 和 HTTPS 代理是否可用，并设置环境变量。
    如果 HTTPS 代理不可用但 HTTP 可用，会将 HTTPS_PROXY 也指向 HTTP。
    """
    test_http_url = "http://www.google.com"
    test_https_url = "https://www.google.com"

    ok_http = ok_https = False

    if http_proxy:
        ok_http = test_proxy(http_proxy, test_http_url)
        if ok_http:
            os.environ["HTTP_PROXY"] = http_proxy
            log.bind(tag=TAG).info(f"Gemini HTTP proxy OK: {http_proxy}")
        else:
            log.bind(tag=TAG).warning(f"Gemini HTTP proxy unavailable: {http_proxy}")

    if https_proxy:
        ok_https = test_proxy(https_proxy, test_https_url)
        if ok_https:
            os.environ["HTTPS_PROXY"] = https_proxy
            log.bind(tag=TAG).info(f"Gemini HTTPS proxy OK: {https_proxy}")
        else:
            log.bind(tag=TAG).warning(
                f"Gemini HTTPS proxy unavailable: {https_proxy}"
            )

    # 如果https_proxy不可用，但http_proxy可用且能走通https，则复用http_proxy作为https_proxy
    if ok_http and not ok_https:
        if test_proxy(http_proxy, test_https_url):
            os.environ["HTTPS_PROXY"] = http_proxy
            ok_https = True
            log.bind(tag=TAG).info(f"Reusing HTTP proxy as HTTPS proxy: {http_proxy}")

    if not ok_http and not ok_https:
        log.bind(tag=TAG).error(
            "Gemini proxy setup failed: both HTTP and HTTPS proxies are unavailable; check config"
        )
        raise RuntimeError("Both HTTP and HTTPS proxies are unavailable; check config")


class LLMProvider(LLMProviderBase):
    def __init__(self, cfg: Dict[str, Any]):
        self.model_name = cfg.get("model_name", "gemini-2.5-flash")
        self.api_key = cfg["api_key"]
        http_proxy = cfg.get("http_proxy")
        https_proxy = cfg.get("https_proxy")

        model_key_msg = check_model_key("LLM", self.api_key)
        if model_key_msg:
            log.bind(tag=TAG).error(model_key_msg)

        if http_proxy or https_proxy:
            log.bind(tag=TAG).info(
                "Gemini proxy configured; testing connectivity and applying env..."
            )
            setup_proxy_env(http_proxy, https_proxy)
            log.bind(tag=TAG).info(
                f"Gemini proxy applied - HTTP: {http_proxy}, HTTPS: {https_proxy}"
            )
        # 配置API密钥
        genai.configure(api_key=self.api_key)

        # 设置请求超时（秒）
        self.timeout = cfg.get("timeout", 120)  # 默认120秒

        # 创建模型实例
        self.model = genai.GenerativeModel(self.model_name)

        self.gen_cfg = GenerationConfig(
            temperature=0.8,
            top_p=0.9,
            top_k=40,
            max_output_tokens=2048,
        )

    @staticmethod
    def _build_tools(funcs: List[Dict[str, Any]] | None):
        if not funcs:
            return None
        return [
            types.Tool(
                function_declarations=[
                    types.FunctionDeclaration(
                        name=f["function"]["name"],
                        description=f["function"]["description"],
                        parameters=f["function"]["parameters"],
                    )
                    for f in funcs
                ]
            )
        ]

    # Gemini文档提到，无需维护session-id，直接用dialogue拼接而成
    def response(self, session_id, dialogue, **kwargs):
        yield from self._generate(dialogue, None)

    def response_with_functions(self, session_id, dialogue, functions=None):
        yield from self._generate(dialogue, self._build_tools(functions))

    def _generate(self, dialogue, tools):
        role_map = {"assistant": "model", "user": "user"}
        contents: list = []
        # 拼接对话
        for m in dialogue:
            r = m["role"]

            if r == "assistant" and "tool_calls" in m:
                tc = m["tool_calls"][0]
                contents.append(
                    {
                        "role": "model",
                        "parts": [
                            {
                                "function_call": {
                                    "name": tc["function"]["name"],
                                    "args": json.loads(tc["function"]["arguments"]),
                                }
                            }
                        ],
                    }
                )
                continue

            if r == "tool":
                contents.append(
                    {
                        "role": "model",
                        "parts": [{"text": str(m.get("content", ""))}],
                    }
                )
                continue

            contents.append(
                {
                    "role": role_map.get(r, "user"),
                    "parts": [{"text": str(m.get("content", ""))}],
                }
            )

        # stream=True can raise RuntimeError("generator raised StopIteration") on google-generativeai
        # when the RPC returns a single chunk (PEP 479 inside GenerateContentResponse.__iter__).
        # Non-streaming avoids that and is fine for chat; logs still show full model text before TTS.
        resp = self.model.generate_content(
            contents=contents,
            generation_config=self.gen_cfg,
            tools=tools,
            stream=False,
            request_options=types.RequestOptions(timeout=self.timeout),
        )

        pf = getattr(resp, "prompt_feedback", None)
        if pf is not None and getattr(pf, "block_reason", None):
            log.bind(tag=TAG).warning(
                f"Gemini prompt blocked: {getattr(pf, 'block_reason', pf)}"
            )
            if tools is not None:
                yield None, None
            return

        cands = getattr(resp, "candidates", None) or []
        if not cands:
            log.bind(tag=TAG).warning("Gemini: empty candidates (safety or stop)")
            if tools is not None:
                yield None, None
            return

        cand = cands[0]
        content = getattr(cand, "content", None)
        parts = list(getattr(content, "parts", None) or [])

        plain_text_parts: list[str] = []
        for part in parts:
            if getattr(part, "function_call", None):
                fc = part.function_call
                yield None, [
                    SimpleNamespace(
                        id=uuid.uuid4().hex,
                        type="function",
                        function=SimpleNamespace(
                            name=fc.name,
                            arguments=json.dumps(
                                dict(fc.args), ensure_ascii=False
                            ),
                        ),
                    )
                ]
                if tools is not None:
                    yield None, None
                return
            tx = getattr(part, "text", None)
            if tx:
                plain_text_parts.append(tx)
                yield tx if tools is None else (tx, None)

        if tools is None and plain_text_parts:
            full = "".join(plain_text_parts)
            preview = full[:1200] + ("…" if len(full) > 1200 else "")
            log.bind(tag=TAG).info(f"Gemini reply (non-streaming): {preview}")

        if tools is not None:
            yield None, None

    # 关闭stream，预留后续打断对话功能的功能方法，官方文档推荐打断对话要关闭上一个流，可以有效减少配额计费和资源占用
    @staticmethod
    def _safe_finish_stream(stream: Any):
        if hasattr(stream, "resolve"):
            stream.resolve()  # Gemini SDK version ≥ 0.5.0
        elif hasattr(stream, "close"):
            stream.close()  # Gemini SDK version < 0.5.0
        else:
            for _ in stream:  # 兜底耗尽
                pass
