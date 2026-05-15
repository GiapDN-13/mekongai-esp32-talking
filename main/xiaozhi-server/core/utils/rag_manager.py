"""
RAG Manager — Singleton quản lý RAG provider instance.

Tránh tạo mới RAGProvider (và reconnect Qdrant + reload embedding model)
mỗi lần search. Một instance duy nhất được tạo lần đầu và tái sử dụng.

Usage:
    from core.utils.rag_manager import rag_manager

    # Lấy shared provider (lazy init lần đầu)
    provider = rag_manager.get_provider(config)

    # Search
    results = await provider.search(query="...", top_k=5)

    # Shutdown khi tắt server
    await rag_manager.shutdown()
"""

import asyncio
import threading
from typing import Dict, Any, Optional

from config.logger import setup_logging

TAG = __name__
logger = setup_logging()


class RAGManager:
    """Thread-safe singleton manager cho RAG provider.

    Đảm bảo chỉ tạo 1 RAGProvider instance cho toàn bộ server.
    Embedding model + Qdrant client được khởi tạo 1 lần, tái sử dụng.
    """

    def __init__(self):
        self._provider = None
        self._lock = threading.Lock()
        self._config_hash = None

    def _compute_config_hash(self, config: Dict[str, Any]) -> str:
        """Tạo hash từ config để detect config thay đổi."""
        keys = [
            "rag_provider", "url", "api_key", "collection_name",
            "embedding_provider", "embedding_model", "vector_size",
            "gemini_api_key", "openai_api_key", "llm_model",
            "working_dir", "vector_storage", "search_mode",
        ]
        parts = []
        for k in keys:
            v = config.get(k, "")
            if isinstance(v, str):
                v = v.strip()
            elif k == "vector_size" and v not in (None, ""):
                try:
                    v = int(v)
                except (TypeError, ValueError):
                    v = str(v)
            parts.append(f"{k}={v}")
        return "|".join(parts)

    def compute_config_hash(self, config: Dict[str, Any]) -> str:  # TODO: dead code — remove (0 external callers)
        """Public: hash dùng để so sánh trước khi get_provider (timeout / cold path)."""
        return self._compute_config_hash(config)

    def will_recreate_provider(self, config: Dict[str, Any]) -> bool:
        """True nếu get_provider sẽ tạo mới hoặc chưa có provider (embed/Qdrant cold)."""
        h = self._compute_config_hash(config)
        return self._provider is None or self._config_hash != h

    def get_provider(self, config: Dict[str, Any]):
        """Lấy hoặc tạo RAG provider instance.

        Thread-safe. Nếu config thay đổi (ví dụ: đổi embedding model),
        provider cũ sẽ được đóng và tạo mới.

        Args:
            config: RAG plugin config dict (plugins.search_from_qdrant).

        Returns:
            RAGProvider instance.
        """
        config_hash = self._compute_config_hash(config)

        with self._lock:
            if self._provider is not None and self._config_hash == config_hash:
                return self._provider

            # Config thay đổi hoặc chưa khởi tạo
            if self._provider is not None:
                logger.bind(tag=TAG).info(
                    "RAG config changed, recreating provider..."
                )
                # Close old provider in background (best effort)
                old_provider = self._provider
                self._provider = None
                try:
                    # Try to close asynchronously
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.run_coroutine_threadsafe(
                            old_provider.close(), loop
                        )
                    else:
                        asyncio.run(old_provider.close())
                except Exception as e:
                    logger.bind(tag=TAG).warning(
                        f"Failed to close old RAG provider: {e}"
                    )

            from core.utils.rag import create_instance
            provider_name = config.get("rag_provider", "qdrant")
            self._provider = create_instance(provider_name, config)
            self._config_hash = config_hash
            logger.bind(tag=TAG).info(
                f"RAG provider initialized: type={provider_name}, "
                f"model={config.get('embedding_model', 'unknown')}"
            )
            return self._provider

    async def warmup(self, config: Dict[str, Any]):
        """Pre-load RAG provider khi server khởi động.

        Gọi trong app.py startup để embedding model + Qdrant connection
        được load sẵn, user không phải chờ lần search đầu tiên.

        Args:
            config: RAG plugin config dict (plugins.search_from_qdrant).
        """
        if not config:
            logger.bind(tag=TAG).info("RAG warmup skipped: no config")
            return

        try:
            provider = self.get_provider(config)
            if hasattr(provider, 'warmup'):
                await provider.warmup()
        except Exception as e:
            logger.bind(tag=TAG).error(f"RAG warmup failed: {e}")

    async def shutdown(self):
        """Đóng provider khi server shutdown. Gọi trong cleanup."""
        with self._lock:
            if self._provider is not None:
                try:
                    await self._provider.close()
                    logger.bind(tag=TAG).info("RAG provider shutdown successfully")
                except Exception as e:
                    logger.bind(tag=TAG).error(
                        f"Error shutting down RAG provider: {e}"
                    )
                finally:
                    self._provider = None
                    self._config_hash = None

    def get_status(self) -> Dict[str, Any]:
        """Trạng thái sẵn sàng của RAG provider cho health/readiness endpoint."""
        with self._lock:
            provider = self._provider
            initialized = provider is not None
            ready = initialized and getattr(provider, "_initialized", True)

            return {
                "initialized": initialized,
                "ready": ready,
                "provider_type": type(provider).__module__ if provider else None,
                "config_hash": self._config_hash,
            }

    @property
    def is_initialized(self) -> bool:
        """Kiểm tra provider đã được khởi tạo chưa."""
        return self._provider is not None


# Global singleton instance
rag_manager = RAGManager()

# Dedicated singleton for RAG Inline (always Qdrant, shared across connections)
inline_rag_manager = RAGManager()
