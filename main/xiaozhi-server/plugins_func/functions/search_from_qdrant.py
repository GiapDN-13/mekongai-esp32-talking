import asyncio
import time
from collections import deque
from concurrent.futures import TimeoutError as FutureTimeoutError
from config.logger import setup_logging
from plugins_func.register import register_function, ToolType, ActionResponse, Action
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler

TAG = __name__
logger = setup_logging()

# Ngưỡng chờ cho truy vấn KB qua voice.
# 5s là khá gắt khi có network jitter tới Gemini/Qdrant;
# dùng 12s để giảm false-timeout trong môi trường thực tế.
RAG_MAX_USER_WAIT_SEC = 12

# Rolling latency buffer for p95/p99 logging (last 200 searches)
_RAG_LAT_MS = deque(maxlen=200)


def _int_from_cfg(val, default: int) -> int:
    try:
        if val is None or val == "":
            return default
        return int(float(val))
    except (TypeError, ValueError):
        return default


def _percentile(values, p: float) -> float:
    if not values:
        return 0.0
    arr = sorted(values)
    n = len(arr)
    if n == 1:
        return float(arr[0])
    rank = (p / 100.0) * (n - 1)
    lo = int(rank)
    hi = min(lo + 1, n - 1)
    frac = rank - lo
    return float(arr[lo] * (1.0 - frac) + arr[hi] * frac)

# Function description cho LLM — mô tả rõ khi nào nên gọi plugin này.
# Chỉnh sửa phần "description" để phù hợp với domain knowledge base của bạn.
SEARCH_FROM_QDRANT_FUNCTION_DESC = {
    "type": "function",
    "function": {
        "name": "search_from_qdrant",
        "description": (
            "BẮT BUỘC gọi TRƯỚC KHI trả lời khi bé hỏi về: truyện, nhân vật trong truyện, nội dung câu chuyện, "
            "hoặc khi cần tìm truyện để kể cho bé. "
            "KHÔNG được tự sáng tác khi có thể tra knowledge base. "
            "Chỉ không gọi khi: thời tiết, tin tức, toán, hoặc trò chuyện xã giao thuần túy."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "Câu hỏi hoặc từ khóa cần tìm kiếm trong knowledge base",
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Tags để lọc kết quả theo chủ đề (optional)",
                },
            },
            "required": ["question"],
        },
    },
}


@register_function(
    "search_from_qdrant", SEARCH_FROM_QDRANT_FUNCTION_DESC, ToolType.WAIT
)
def search_from_qdrant(conn: "ConnectionHandler", question=None, tags=None):
    """Plugin tìm kiếm knowledge base qua Qdrant vector search (Mode A: Function Calling).

    Được gọi bởi LLM khi cần tra cứu thông tin từ knowledge base nội bộ.
    Sử dụng RAG singleton manager để tái sử dụng connection + embedding model.
    Trả về ActionResponse.REQLLM để LLM tổng hợp câu trả lời từ context tìm được.
    """
    if not question or not str(question).strip():
        return ActionResponse(
            Action.RESPONSE, None, "Vui lòng cung cấp câu hỏi để tìm kiếm."
        )

    question = str(question).strip()

    # Lấy RAG config từ connection config.
    # Private config từ manager-api có thể gửi dạng legacy JSON-string (demo kb),
    # thiếu các trường Qdrant/Gemini cần cho plugin hiện tại.
    raw_rag_cfg = conn.config.get("plugins", {}).get("search_from_qdrant", {})
    if isinstance(raw_rag_cfg, str):
        import json
        try:
            raw_rag_cfg = json.loads(raw_rag_cfg)
        except Exception:
            raw_rag_cfg = {}

    rag_config = dict(raw_rag_cfg or {})

    # Always merge with server-level config as base, private config overrides
    try:
        from config.config_loader import load_config
        base_cfg = load_config() or {}
        base_rag = dict((base_cfg.get("plugins", {}) or {}).get("search_from_qdrant", {}) or {})
        if base_rag:
            merged = dict(base_rag)
            for k, v in rag_config.items():
                if v is not None and v != "":
                    merged[k] = v
            rag_config = merged
    except Exception as cfg_err:
        logger.bind(tag=TAG).warning(f"Failed to merge server-level RAG config: {cfg_err}")

    logger.bind(tag=TAG).info(
        f"RAG config: provider={rag_config.get('rag_provider','?')}, "
        f"threshold={rag_config.get('score_threshold','?')}, "
        f"collection={rag_config.get('collection_name','?')}"
    )

    if not rag_config:
        logger.bind(tag=TAG).error(
            "search_from_qdrant plugin config not found in config.yaml"
        )
        return ActionResponse(
            Action.RESPONSE, None, "Knowledge base chưa được cấu hình."
        )

    from core.utils.rag_plugin_config import merge_llm_keys_into_rag_config

    _before_keys = bool(rag_config.get("gemini_api_key") or rag_config.get("openai_api_key"))
    rag_config = merge_llm_keys_into_rag_config(rag_config, conn.config)
    if not _before_keys and (rag_config.get("gemini_api_key") or rag_config.get("openai_api_key")):
        logger.bind(tag=TAG).info(
            f"Auto-configured embedding key from LLM config, "
            f"model={rag_config.get('embedding_model')}, vector_size={rag_config.get('vector_size')}"
        )

    try:
        from core.utils.rag_manager import rag_manager

        cold = rag_manager.will_recreate_provider(rag_config)

        rag_provider = rag_manager.get_provider(rag_config)

        loop = conn.loop
        if loop is None or not loop.is_running():
            logger.bind(tag=TAG).error("No running event loop available")
            return ActionResponse(
                Action.RESPONSE, None, "Lỗi nội bộ: không có event loop."
            )

        filter_tags = None  # Tags from LLM intent are unreliable; rely on semantic search only

        raw_to = _int_from_cfg(
            rag_config.get("search_timeout")
            or rag_config.get("search_timeout_warm")
            or rag_config.get("search_timeout_cold"),
            RAG_MAX_USER_WAIT_SEC,
        )
        search_timeout = max(1, min(raw_to, RAG_MAX_USER_WAIT_SEC))

        top_k = rag_config.get("top_k", 5)
        score_threshold = rag_config.get("score_threshold", 0.5)
        try:
            score_threshold = float(score_threshold)
        except (TypeError, ValueError):
            score_threshold = 0.5

        async def _search_only():
            return await rag_provider.search(
                query=question,
                top_k=top_k,
                score_threshold=score_threshold,
                filter_tags=filter_tags,
            )

        is_warm_ready = getattr(rag_provider, "_initialized", False) or bool(
            getattr(rag_provider, "_gemini_model", None)
            and getattr(rag_provider, "_client", None)
        ) or bool(
            getattr(rag_provider, "_local_model", None)
            and getattr(rag_provider, "_client", None)
        ) or bool(
            getattr(rag_provider, "_openai_client", None)
            and getattr(rag_provider, "_client", None)
        )

        if cold or not is_warm_ready:
            logger.bind(tag=TAG).warning(
                f"RAG provider not warm-ready (cold={cold}, ready={is_warm_ready}); "
                "running warmup with short wait"
            )
            try:
                warmup_future = asyncio.run_coroutine_threadsafe(rag_provider.warmup(), loop)
                # Chờ ngắn để bắt lỗi cấu hình sớm (vd thiếu API key),
                # đồng thời vẫn bảo toàn SLA không chờ quá lâu.
                warmup_future.result(timeout=min(3, search_timeout))
            except TimeoutError:
                return ActionResponse(
                    Action.RESPONSE,
                    None,
                    "Knowledge base đang khởi tạo, vui lòng thử lại sau vài giây.",
                )
            except Exception as warmup_err:
                logger.bind(tag=TAG).error(
                    f"RAG warmup failed before search: {type(warmup_err).__name__}: {warmup_err}"
                )
                return ActionResponse(
                    Action.RESPONSE,
                    None,
                    f"Knowledge base chưa sẵn sàng: {warmup_err}",
                )

            is_warm_ready = getattr(rag_provider, "_initialized", False) or bool(
                getattr(rag_provider, "_gemini_model", None)
                and getattr(rag_provider, "_client", None)
            ) or bool(
                getattr(rag_provider, "_local_model", None)
                and getattr(rag_provider, "_client", None)
            ) or bool(
                getattr(rag_provider, "_openai_client", None)
                and getattr(rag_provider, "_client", None)
            )
            if not is_warm_ready:
                return ActionResponse(
                    Action.RESPONSE,
                    None,
                    "Knowledge base đang khởi tạo, vui lòng thử lại sau vài giây.",
                )

        logger.bind(tag=TAG).info(
            f"RAG search user-wait cap={search_timeout}s (cold={cold}, ready={is_warm_ready}); search-only path"
        )

        t0 = time.perf_counter()
        future = asyncio.run_coroutine_threadsafe(_search_only(), loop)
        try:
            results = future.result(timeout=search_timeout)
        except FutureTimeoutError:
            future.cancel()
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            logger.bind(tag=TAG).warning(
                f"RAG search timeout after {elapsed_ms:.1f}ms "
                f"(cap={search_timeout}s, query={question!r})"
            )
            return ActionResponse(
                Action.RESPONSE,
                None,
                "Tra cứu knowledge base đang chậm, vui lòng thử lại sau vài giây.",
            )
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        _RAG_LAT_MS.append(elapsed_ms)
        p95 = _percentile(_RAG_LAT_MS, 95)
        p99 = _percentile(_RAG_LAT_MS, 99)

        if not results:
            logger.bind(tag=TAG).info(
                f"RAG search '{question}': no results above threshold; "
                f"latency_ms={elapsed_ms:.1f}, p95={p95:.1f}, p99={p99:.1f}, n={len(_RAG_LAT_MS)}"
            )
            return ActionResponse(
                Action.REQLLM,
                f"Không tìm thấy thông tin liên quan đến: {question}",
                None,
            )

        # Format context cho LLM
        context_parts = []
        for i, r in enumerate(results, 1):
            source_info = f" (nguồn: {r.source})" if r.source != "unknown" else ""
            context_parts.append(f"[{i}]{source_info}\n{r.content}")

        context_text = (
            f"# Kết quả tìm kiếm knowledge base cho: \"{question}\"\n\n"
            + "\n\n---\n\n".join(context_parts)
        )

        # Sync _rag_story_state so that RAG Inline "continue" intent works
        # even when the first story was fetched via this tool call path.
        top = results[0]
        meta = getattr(top, "metadata", {}) or {}
        found_story_id = meta.get("story_id", "")
        found_doc_id = meta.get("doc_id", "")
        if found_story_id and found_doc_id and hasattr(conn, "_rag_story_state"):
            total_parts = meta.get("total_parts", 0)
            conn._rag_story_state = {
                "story_id": found_story_id,
                "doc_id": found_doc_id,
                "last_part_index": -1,
                "total_parts": total_parts,
                "sub_offset": 0,
            }
            logger.bind(tag=TAG).info(
                f"Synced _rag_story_state: story_id='{found_story_id}', "
                f"doc_id='{found_doc_id}', total_parts={total_parts}"
            )

        logger.bind(tag=TAG).info(
            f"RAG search '{question}': {len(results)} results, "
            f"scores: {[round(r.score, 3) for r in results]}, "
            f"latency_ms={elapsed_ms:.1f}, p95={p95:.1f}, p99={p99:.1f}, n={len(_RAG_LAT_MS)}"
        )
        return ActionResponse(Action.REQLLM, context_text, None)

    except Exception as e:
        logger.bind(tag=TAG).error(
            f"RAG search error [{type(e).__name__}]: {e}"
        )
        return ActionResponse(
            Action.RESPONSE,
            None,
            f"Lỗi khi tìm kiếm knowledge base: {str(e)}",
        )
