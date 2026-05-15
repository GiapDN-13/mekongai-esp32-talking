"""
LightRAG Provider — GraphRAG with knowledge graph + vector hybrid search.

Uses LightRAG (EMNLP 2025) for automatic entity extraction, knowledge graph
construction, and dual-level retrieval. Supports Qdrant as vector backend.
"""

import os
import asyncio
import importlib
from functools import partial
from typing import List, Optional, Dict, Any

import numpy as np

# Import lightrag at module load time to avoid shadowing issues in async context.
# The installed package is 'lightrag-hku', import name 'lightrag'.
_lightrag_mod = importlib.import_module("lightrag")
_lightrag_openai = importlib.import_module("lightrag.llm.openai")
_lightrag_utils = importlib.import_module("lightrag.utils")

LightRAGCore = _lightrag_mod.LightRAG
QueryParam = _lightrag_mod.QueryParam
openai_complete_if_cache = _lightrag_openai.openai_complete_if_cache
openai_embed = _lightrag_openai.openai_embed
EmbeddingFunc = _lightrag_utils.EmbeddingFunc

from config.logger import setup_logging
from core.providers.rag.base import RAGProviderBase, SearchResult

TAG = __name__
logger = setup_logging()


class RAGProvider(RAGProviderBase):
    """LightRAG-based GraphRAG provider.

    Wraps LightRAG core library to provide the same interface as QdrantRAGProvider.
    Entity extraction + knowledge graph is handled internally by LightRAG.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

        self.working_dir = config.get("working_dir", "data/lightrag_storage")
        os.makedirs(self.working_dir, exist_ok=True)

        # Vector storage config — reuse Qdrant if available
        self.vector_storage = config.get("vector_storage", "QdrantVectorDBStorage")
        self.qdrant_url = config.get("url", "http://localhost:6333")
        self.qdrant_api_key = config.get("api_key", None)

        # Embedding config
        self.embedding_model = config.get("embedding_model", "text-embedding-3-small")
        self.embedding_dim = int(config.get("vector_size", 1536))
        self.openai_api_key = config.get("openai_api_key", "")
        self.openai_base_url = config.get("openai_base_url", None)

        # LLM config for entity extraction
        self.llm_model = config.get("llm_model", "gpt-4o-mini")
        self.llm_api_key = config.get("llm_api_key", "") or self.openai_api_key

        # Search config
        self.default_top_k = int(config.get("top_k", 5))
        self.default_score_threshold = float(config.get("score_threshold", 0.5))
        self.search_mode = config.get("search_mode", "hybrid")

        # Chunking config
        self.chunk_token_size = int(config.get("chunk_token_size", 1200))
        self.chunk_overlap_token_size = int(config.get("chunk_overlap_token_size", 100))

        # Entity extraction config
        self.entity_extract_max_gleaning = int(config.get("max_gleaning", 1))

        self._rag = None
        self._initialized = False

    def _setup_env(self):
        """Set environment variables required by LightRAG storage backends."""
        if self.qdrant_url:
            os.environ["QDRANT_URL"] = self.qdrant_url
        if self.qdrant_api_key:
            os.environ["QDRANT_API_KEY"] = self.qdrant_api_key

        api_key = self.openai_api_key or self.llm_api_key or os.environ.get("OPENAI_API_KEY", "")
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key

    async def _ensure_initialized(self):
        """Lazy-init LightRAG instance."""
        if self._initialized and self._rag is not None:
            return

        self._setup_env()

        llm_api_key = self.llm_api_key
        llm_model = self.llm_model
        llm_base_url = self.openai_base_url

        async def llm_func(prompt, system_prompt=None, history_messages=None, **kwargs):
            kw = {}
            if llm_api_key:
                kw["api_key"] = llm_api_key
            if llm_base_url:
                kw["base_url"] = llm_base_url
            return await openai_complete_if_cache(
                llm_model,
                prompt,
                system_prompt=system_prompt,
                history_messages=history_messages or [],
                **kw,
                **kwargs,
            )

        embed_api_key = self.openai_api_key
        embed_model = self.embedding_model
        embed_base_url = self.openai_base_url

        async def embed_func(texts: list[str]) -> np.ndarray:
            kw = {}
            if embed_api_key:
                kw["api_key"] = embed_api_key
            if embed_base_url:
                kw["base_url"] = embed_base_url
            return await openai_embed.func(texts, model=embed_model, **kw)

        embedding_func = EmbeddingFunc(
            embedding_dim=self.embedding_dim,
            max_token_size=8192,
            func=embed_func,
            model_name=self.embedding_model,
        )

        self._rag = LightRAGCore(
            working_dir=self.working_dir,
            llm_model_func=llm_func,
            embedding_func=embedding_func,
            vector_storage=self.vector_storage,
            chunk_token_size=self.chunk_token_size,
            chunk_overlap_token_size=self.chunk_overlap_token_size,
            entity_extract_max_gleaning=self.entity_extract_max_gleaning,
            enable_llm_cache=True,
            enable_llm_cache_for_entity_extract=True,
        )

        await self._rag.initialize_storages()
        self._initialized = True
        logger.bind(tag=TAG).info(
            f"LightRAG initialized: working_dir={self.working_dir}, "
            f"vector_storage={self.vector_storage}, "
            f"embedding={self.embedding_model} ({self.embedding_dim}d), "
            f"llm={self.llm_model}"
        )

    async def warmup(self):
        """Pre-initialize LightRAG (embedding model + storage connections)."""
        await self._ensure_initialized()

    async def search(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: float = 0.5,
        filter_tags: Optional[List[str]] = None,
    ) -> List[SearchResult]:
        await self._ensure_initialized()

        mode = self.search_mode
        param = QueryParam(mode=mode, top_k=top_k or self.default_top_k)

        response = await self._rag.aquery(query, param=param)

        if not response or not str(response).strip():
            return []

        response_text = str(response).strip()
        return [
            SearchResult(
                content=response_text,
                score=1.0,
                source="lightrag_graph",
                chunk_index=0,
                metadata={"mode": mode, "query": query},
            )
        ]

    async def add_documents(self, documents: List[Dict[str, Any]]) -> int:
        await self._ensure_initialized()

        total_inserted = 0
        for doc in documents:
            content = doc.get("content", "")
            if not content.strip():
                continue

            source = doc.get("source", "unknown")
            doc_id = doc.get("doc_id", None)

            try:
                await self._rag.ainsert(
                    content,
                    ids=[doc_id] if doc_id else None,
                    file_paths=[source] if source != "unknown" else None,
                )
                total_inserted += 1
                logger.bind(tag=TAG).info(
                    f"Document ingested via LightRAG: source={source}"
                )
            except Exception as e:
                logger.bind(tag=TAG).error(
                    f"Failed to ingest document {source}: {e}"
                )

        return total_inserted

    async def delete_documents(self, doc_ids: List[str]) -> int:
        await self._ensure_initialized()

        deleted = 0
        for doc_id in doc_ids:
            try:
                await self._rag.adelete_by_doc_id(doc_id)
                deleted += 1
            except Exception as e:
                logger.bind(tag=TAG).warning(
                    f"Failed to delete doc {doc_id}: {e}"
                )
        return deleted

    async def get_collection_info(self) -> Dict[str, Any]:
        await self._ensure_initialized()

        doc_status = {}
        try:
            if hasattr(self._rag, 'doc_status'):
                status_store = self._rag.doc_status
                if hasattr(status_store, 'get_all'):
                    doc_status = await status_store.get_all() or {}
        except Exception:
            pass

        return {
            "name": "lightrag",
            "working_dir": self.working_dir,
            "vector_storage": self.vector_storage,
            "embedding_model": self.embedding_model,
            "llm_model": self.llm_model,
            "search_mode": self.search_mode,
            "documents_count": len(doc_status),
            "status": "ready" if self._initialized else "not_initialized",
        }

    async def close(self):
        if self._rag is not None:
            try:
                if hasattr(self._rag, 'finalize_storages'):
                    await self._rag.finalize_storages()
            except Exception as e:
                logger.bind(tag=TAG).warning(f"Error closing LightRAG: {e}")
            self._rag = None
            self._initialized = False
            logger.bind(tag=TAG).info("LightRAG provider closed")
