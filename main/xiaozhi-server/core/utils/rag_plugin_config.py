"""
Cấu hình plugin search_from_qdrant — merge API keys từ LLM config.
Hỗ trợ cả OpenAI và Gemini embedding providers.
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def _extract_usable_key(llm_cfg: Dict[str, Any]) -> str:
    api_key = llm_cfg.get("api_key", "")
    if not api_key or api_key in ("your_api_key", "your-api-key", ""):
        return ""
    return str(api_key).strip()


def _looks_like_gemini_key(k: str) -> bool:
    return k.startswith("AIza")


def merge_llm_keys_into_rag_config(
    rag_config: Dict[str, Any], connection_config: Dict[str, Any]
) -> Dict[str, Any]:
    """Bổ sung API keys (OpenAI / Gemini) từ LLM config nếu plugin chưa có."""
    rag = dict(rag_config)

    llm_configs = connection_config.get("LLM", {})
    if not isinstance(llm_configs, dict):
        logger.debug("merge_llm_keys: LLM config missing or not a dict")
        return rag

    sel = (connection_config.get("selected_module") or {}).get("LLM")
    logger.debug("merge_llm_keys: selected_module.LLM=%s, LLM keys=%s",
                 sel, list(llm_configs.keys()))

    # Try OpenAI key
    existing_oai = rag.get("openai_api_key") or ""
    existing_llm = rag.get("llm_api_key") or ""
    if not existing_oai and not existing_llm:
        openai_key = ""
        if sel and sel in llm_configs:
            cfg = llm_configs[sel]
            if isinstance(cfg, dict):
                k = _extract_usable_key(cfg)
                t = (cfg.get("type") or "").strip()
                if k and t == "openai":
                    openai_key = k
        if not openai_key:
            for _name, llm_cfg in llm_configs.items():
                if not isinstance(llm_cfg, dict):
                    continue
                k = _extract_usable_key(llm_cfg)
                if k and (llm_cfg.get("type") or "").strip() == "openai":
                    openai_key = k
                    break
        if openai_key:
            rag["openai_api_key"] = openai_key
            rag["llm_api_key"] = openai_key
            logger.info("merge_llm_keys: injected OpenAI key from LLM config (key=...%s)",
                        openai_key[-4:] if len(openai_key) > 4 else "****")
        else:
            logger.debug("merge_llm_keys: no usable OpenAI key found in LLM configs")

    # Try Gemini key (backward compat)
    existing_gemini = rag.get("gemini_api_key") or ""
    if not existing_gemini:
        gemini_key = ""
        if sel and sel in llm_configs:
            cfg = llm_configs[sel]
            if isinstance(cfg, dict):
                k = _extract_usable_key(cfg)
                t = (cfg.get("type") or "").strip()
                if k and (t == "gemini" or (not t and _looks_like_gemini_key(k))):
                    gemini_key = k
        if not gemini_key:
            for _name, llm_cfg in llm_configs.items():
                if not isinstance(llm_cfg, dict):
                    continue
                k = _extract_usable_key(llm_cfg)
                if not k:
                    continue
                llm_type = (llm_cfg.get("type") or "").strip()
                if llm_type == "gemini" or (not llm_type and _looks_like_gemini_key(k)):
                    gemini_key = k
                    break
        if gemini_key:
            rag["gemini_api_key"] = gemini_key
            logger.info("merge_llm_keys: injected Gemini key from LLM config")

    return rag
