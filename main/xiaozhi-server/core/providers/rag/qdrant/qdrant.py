import asyncio
import functools
import os
import re
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from config.logger import setup_logging
from core.providers.rag.base import RAGProviderBase, SearchResult

TAG = __name__
logger = setup_logging()

# Vietnamese-specific separators for better chunking
_VI_SEPARATORS = [
    "\n\n",           # Paragraph break
    "\n",             # Line break
    "。",             # CJK full stop (for mixed content)
    ". ",             # Latin full stop
    "! ",             # Exclamation
    "? ",             # Question mark
    "; ",             # Semicolon
    ", ",             # Comma
    ".\n",            # Period + newline
    "!\n",            # Exclamation + newline
    "?\n",            # Question + newline
    " ",              # Space (word boundary — important for Vietnamese)
    "",               # Fallback: character-level
]


class RAGProvider(RAGProviderBase):
    """Qdrant RAG with Gemini or OpenAI embedding.

    Lazy init client + model. Chunking tối ưu tiếng Việt.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.qdrant_url = config.get("url", "http://localhost:6333")
        self.qdrant_api_key = config.get("api_key", None)
        self.collection_name = config.get("collection_name", "xiaozhi_knowledge")

        raw_prov = (config.get("embedding_provider") or "gemini").strip().lower()
        self.embedding_provider = raw_prov if raw_prov in ("gemini", "openai", "local", "bedrock") else "gemini"
        default_models = {
            "openai": "text-embedding-3-small",
            "gemini": "gemini-embedding-001",
            "local": "BAAI/bge-m3",
            "bedrock": "amazon.titan-embed-text-v2:0",
        }
        default_dims = {"openai": 1536, "gemini": 768, "local": 1024, "bedrock": 1024}
        self.embedding_model_name = config.get("embedding_model", default_models.get(self.embedding_provider, "gemini-embedding-001"))
        self.vector_size = int(config.get("vector_size", default_dims.get(self.embedding_provider, 768)))
        self.gemini_api_key = config.get("gemini_api_key", "")
        self.openai_api_key = config.get("openai_api_key", "") or os.environ.get("OPENAI_API_KEY", "")
        self.openai_base_url = config.get("openai_base_url", None)
        self.bedrock_region = config.get("bedrock_region", "us-east-1")
        self.bedrock_access_key = config.get("bedrock_access_key", "")
        self.bedrock_secret_key = config.get("bedrock_secret_key", "")
        try:
            self.qdrant_http_timeout = int(config.get("qdrant_timeout", 5))
        except (TypeError, ValueError):
            self.qdrant_http_timeout = 5
        self.warmup_skip_embed_test = bool(config.get("warmup_skip_embed_test", True))

        self.default_top_k = config.get("top_k", 3)
        self.default_score_threshold = config.get("score_threshold", 0.5)
        self.chunk_size = config.get("chunk_size", 700)
        self.chunk_overlap = config.get("chunk_overlap", 60)

        self._client = None
        self._gemini_model = None
        self._openai_client = None
        self._local_model = None
        self._text_splitter = None

    def _get_text_splitter(self):
        """Lazy init text splitter với Vietnamese-optimized separators."""
        if self._text_splitter is None:
            try:
                from langchain_text_splitters import RecursiveCharacterTextSplitter
                self._text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=self.chunk_size,
                    chunk_overlap=self.chunk_overlap,
                    separators=_VI_SEPARATORS,
                    length_function=len,
                    is_separator_regex=False,
                )
            except ImportError:
                raise ImportError(
                    "langchain-text-splitters not installed. "
                    "Run: pip install langchain-text-splitters"
                )
        return self._text_splitter

    def _get_gemini_model(self):
        """Lazy init Gemini embedding model.

        Sử dụng google-generativeai SDK (đã có trong requirements.txt).
        Model: gemini-embedding-001 (768 dims với output_dimensionality mặc định).
        """
        if self._gemini_model is None:
            if not self.gemini_api_key:
                raise ValueError(
                    "Gemini API key required for embedding_provider='gemini'. "
                    "Set gemini_api_key in search_from_qdrant config."
                )
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.gemini_api_key)
                self._gemini_model = genai
                logger.bind(tag=TAG).info(
                    f"Gemini embedding initialized "
                    f"(model: {self.embedding_model_name})"
                )
            except ImportError:
                raise ImportError(
                    "google-generativeai not installed. "
                    "Run: pip install google-generativeai"
                )
        return self._gemini_model

    def _gemini_api_model_id(self) -> str:
        """Tên model đầy đủ cho `google.generativeai.embed_content`.

        `genai.list_models()` (2025+) trả embedding: `models/gemini-embedding-001`.
        Tên cũ (`text-embedding-004`, `embedding-001`) map sang `gemini-embedding-001`.
        """
        raw = (self.embedding_model_name or "gemini-embedding-001").strip()
        if raw.startswith("models/"):
            raw = raw[len("models/") :]
        legacy_map = {
            "text-embedding-004": "gemini-embedding-001",
            "text-embedding-004-latest": "gemini-embedding-001",
            "embedding-001": "gemini-embedding-001",
        }
        if raw in legacy_map:
            logger.bind(tag=TAG).info(
                "mapping embedding_model={} -> {} for Gemini embedContent",
                raw,
                f"models/{legacy_map[raw]}",
            )
            raw = legacy_map[raw]
        return f"models/{raw}"

    def _embed_gemini_sync(
        self, texts: List[str], *, task_type: str = "retrieval_document"
    ) -> List[List[float]]:
        """Embed texts via Gemini API synchronously.

        - retrieval_query: user / search queries (vector search)
        - retrieval_document: chunks khi ingest (khớp vector không gian với index)
        """
        genai = self._get_gemini_model()
        model_id = self._gemini_api_model_id()

        all_embeddings = []
        batch_size = 100  # Gemini giới hạn 100 texts/call
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            try:
                result = genai.embed_content(
                    model=model_id,
                    content=batch,
                    task_type=task_type,
                    output_dimensionality=self.vector_size,
                )
            except Exception as e:
                if task_type == "retrieval_query":
                    logger.bind(tag=TAG).warning(
                        f"embed_content retrieval_query failed ({e}); retrying with retrieval_document"
                    )
                    result = genai.embed_content(
                        model=model_id,
                        content=batch,
                        task_type="retrieval_document",
                        output_dimensionality=self.vector_size,
                    )
                else:
                    raise
            # result['embedding'] cho single text, result['embedding'] cho batch
            if isinstance(result['embedding'][0], list):
                all_embeddings.extend(result['embedding'])
            else:
                all_embeddings.append(result['embedding'])

        return all_embeddings

    def _embed_texts_sync(
        self, texts: List[str], *, for_query: bool = False
    ) -> List[List[float]]:
        """Embed texts synchronously (Gemini, OpenAI, Bedrock, or Local)."""
        if self.embedding_provider == "openai":
            return self._embed_openai_sync(texts)
        if self.embedding_provider == "local":
            return self._embed_local_sync(texts)
        if self.embedding_provider == "bedrock":
            return self._embed_bedrock_sync(texts)
        tt = "retrieval_query" if for_query else "retrieval_document"
        return self._embed_gemini_sync(texts, task_type=tt)

    def _get_local_model(self):
        """Lazy init local sentence-transformers model."""
        if self._local_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._local_model = SentenceTransformer(
                    self.embedding_model_name, trust_remote_code=True
                )
                logger.bind(tag=TAG).info(
                    f"Local embedding loaded: {self.embedding_model_name}"
                )
            except ImportError:
                raise ImportError(
                    "sentence-transformers not installed. "
                    "Run: pip install sentence-transformers"
                )
        return self._local_model

    def _embed_local_sync(self, texts: List[str]) -> List[List[float]]:
        """Embed texts using local sentence-transformers model."""
        model = self._get_local_model()
        embeddings = model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()

    def _embed_openai_sync(self, texts: List[str]) -> List[List[float]]:
        """Embed texts via OpenAI API synchronously."""
        if not self._openai_client:
            if not self.openai_api_key:
                raise ValueError("OpenAI API key required for embedding_provider='openai'.")
            try:
                from openai import OpenAI
                kwargs = {"api_key": self.openai_api_key}
                if self.openai_base_url:
                    kwargs["base_url"] = self.openai_base_url
                self._openai_client = OpenAI(**kwargs)
                logger.bind(tag=TAG).info(f"OpenAI embedding initialized (model: {self.embedding_model_name})")
            except ImportError:
                raise ImportError("openai not installed. Run: pip install openai")

        all_embeddings = []
        batch_size = 100
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            resp = self._openai_client.embeddings.create(model=self.embedding_model_name, input=batch)
            all_embeddings.extend([d.embedding for d in resp.data])
        return all_embeddings

    def _embed_bedrock_sync(self, texts: List[str]) -> List[List[float]]:
        """Embed texts via AWS Bedrock Titan Embeddings."""
        if not hasattr(self, "_bedrock_client") or self._bedrock_client is None:
            import boto3
            session_kwargs = {"region_name": self.bedrock_region}
            if self.bedrock_access_key and self.bedrock_secret_key:
                session_kwargs["aws_access_key_id"] = self.bedrock_access_key
                session_kwargs["aws_secret_access_key"] = self.bedrock_secret_key
            session = boto3.Session(**session_kwargs)
            self._bedrock_client = session.client("bedrock-runtime")
            logger.bind(tag=TAG).info(
                f"Bedrock embedding initialized (model: {self.embedding_model_name})"
            )

        import json
        all_embeddings = []
        for text in texts:
            body = json.dumps({"inputText": text, "dimensions": self.vector_size, "normalize": True})
            resp = self._bedrock_client.invoke_model(
                modelId=self.embedding_model_name,
                body=body,
                contentType="application/json",
                accept="application/json",
            )
            result = json.loads(resp["body"].read())
            all_embeddings.append(result["embedding"])
        return all_embeddings

    async def _embed_texts(
        self, texts: List[str], *, for_query: bool = False
    ) -> List[List[float]]:
        """Embed texts asynchronously (offload blocking work sang thread pool)."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            functools.partial(self._embed_texts_sync, texts, for_query=for_query),
        )

    # =========================================================================
    # QDRANT CLIENT
    # =========================================================================

    async def _get_client(self):
        """Lazy init Qdrant async client và đảm bảo collection tồn tại."""
        if self._client is None:
            try:
                from qdrant_client import AsyncQdrantClient
                self._client = AsyncQdrantClient(
                    url=self.qdrant_url,
                    api_key=self.qdrant_api_key,
                    timeout=self.qdrant_http_timeout,
                )
                await self._ensure_collection()
                logger.bind(tag=TAG).info(
                    f"Connected to Qdrant at {self.qdrant_url}, "
                    f"collection: {self.collection_name}"
                )
            except ImportError:
                raise ImportError(
                    "qdrant-client not installed. Run: pip install qdrant-client"
                )
        return self._client

    async def _ensure_collection(self):
        """Tạo collection nếu chưa tồn tại. Recreate nếu vector_size thay đổi."""
        from qdrant_client.models import (
            VectorParams, Distance, HnswConfigDiff, OptimizersConfigDiff,
            PayloadSchemaType,
        )
        collections = await self._client.get_collections()
        existing_names = [c.name for c in collections.collections]

        if self.collection_name in existing_names:
            info = await self._client.get_collection(self.collection_name)
            existing_size = None
            if hasattr(info.config, 'params') and hasattr(info.config.params, 'vectors'):
                vectors_cfg = info.config.params.vectors
                if hasattr(vectors_cfg, 'size'):
                    existing_size = vectors_cfg.size

            if existing_size and existing_size != self.vector_size:
                raise ValueError(
                    f"Qdrant collection '{self.collection_name}' vector_size mismatch: "
                    f"existing={existing_size}, required={self.vector_size}. "
                    f"Refusing to auto-recreate collection to prevent data loss. "
                    f"Please migrate to a new collection_name or recreate manually."
                )
            else:
                logger.bind(tag=TAG).debug(
                    f"Collection already exists: {self.collection_name} "
                    f"(vector_size={existing_size or 'unknown'})"
                )
        else:
            await self._client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=Distance.COSINE,
                    hnsw_config=HnswConfigDiff(
                        m=16,
                        ef_construct=100,
                        full_scan_threshold=10000,
                    ),
                    on_disk=False,
                ),
                optimizers_config=OptimizersConfigDiff(
                    indexing_threshold=20000,
                ),
            )
            logger.bind(tag=TAG).info(
                f"Created Qdrant collection: {self.collection_name} "
                f"(vector_size={self.vector_size}, distance=COSINE)"
            )

        # Ensure payload indexes for fast metadata filtering
        for field_name in ("story_id", "doc_id"):
            try:
                await self._client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name=field_name,
                    field_schema=PayloadSchemaType.KEYWORD,
                )
                logger.bind(tag=TAG).debug(f"Payload index ensured: {field_name}")
            except Exception:
                pass

    # =========================================================================
    # SEARCH
    # =========================================================================

    async def _reset_client(self):
        """Close stale client so next _get_client() reconnects."""
        if self._client is not None:
            try:
                await self._client.close()
            except Exception:
                pass
            self._client = None

    async def search(
        self,
        query: str,
        top_k: int = None,
        score_threshold: float = None,
        dataset_id: Optional[str] = None,
        doc_ids: Optional[List[str]] = None,
        filter_tags: Optional[List[str]] = None,
        story_id: Optional[str] = None,
    ) -> List[SearchResult]:
        """Tìm kiếm chunks liên quan đến query bằng vector similarity."""
        if top_k is None:
            top_k = self.default_top_k
        if score_threshold is None:
            score_threshold = self.default_score_threshold

        if not query or not query.strip():
            return []

        client = await self._get_client()

        query_vectors = await self._embed_texts([query.strip()], for_query=True)
        query_vector = query_vectors[0]

        search_filter = None
        if dataset_id or doc_ids or filter_tags or story_id:
            from qdrant_client.models import Filter, FieldCondition, MatchAny, MatchValue
            must = []
            if dataset_id:
                must.append(
                    FieldCondition(
                        key="dataset_id",
                        match=MatchValue(value=dataset_id),
                    )
                )
            if doc_ids:
                must.append(
                    FieldCondition(
                        key="doc_id",
                        match=MatchAny(any=doc_ids),
                    )
                )
            if filter_tags:
                must.append(
                    FieldCondition(
                        key="tags",
                        match=MatchAny(any=filter_tags),
                    )
                )
            if story_id:
                must.append(
                    FieldCondition(
                        key="story_id",
                        match=MatchValue(value=story_id),
                    )
                )
            search_filter = Filter(must=must)

        # qdrant-client >= 1.10 dùng query_points thay vì search
        for attempt in range(2):
            try:
                try:
                    response = await client.query_points(
                        collection_name=self.collection_name,
                        query=query_vector,
                        limit=top_k,
                        score_threshold=score_threshold,
                        query_filter=search_filter,
                        with_payload=True,
                    )
                    results = response.points if hasattr(response, 'points') else response
                except AttributeError:
                    # Fallback cho qdrant-client cũ
                    results = await client.search(
                        collection_name=self.collection_name,
                        query_vector=query_vector,
                        limit=top_k,
                        score_threshold=score_threshold,
                        query_filter=search_filter,
                        with_payload=True,
                    )
                break
            except Exception as e:
                if attempt == 0:
                    logger.bind(tag=TAG).warning(
                        f"Qdrant query failed ({e}), reconnecting..."
                    )
                    await self._reset_client()
                    client = await self._get_client()
                else:
                    logger.bind(tag=TAG).error(f"Qdrant query failed after reconnect: {e}")
                    return []

        search_results = [
            SearchResult(
                content=r.payload.get("content", ""),
                score=r.score,
                source=r.payload.get("source", "unknown"),
                chunk_index=r.payload.get("part_index", r.payload.get("chunk_index", 0)),
                metadata={
                    k: v for k, v in r.payload.items()
                    if k not in ("content",)
                },
            )
            for r in results
            if r.payload.get("content")
        ]

        logger.bind(tag=TAG).info(
            f"Search '{query[:50]}': {len(search_results)} results "
            f"(top_k={top_k}, threshold={score_threshold}, "
            f"raw_points={len(results)}, collection={self.collection_name})"
        )
        return search_results

    # =========================================================================
    # DOCUMENT MANAGEMENT
    # =========================================================================

    async def add_documents(self, documents: List[Dict[str, Any]]) -> int:
        """Nạp tài liệu vào Qdrant sau khi chunk và embed.

        Args:
            documents: List of dicts với keys: content, source, doc_id (optional),
                       tags (optional), language (optional).

        Returns:
            Tổng số chunks đã thêm.
        """
        from qdrant_client.models import PointStruct

        client = await self._get_client()
        splitter = self._get_text_splitter()
        total_added = 0

        for doc in documents:
            raw_content = doc.get("content", "").strip()
            if not raw_content:
                logger.bind(tag=TAG).warning(
                    f"Skipping empty document: {doc.get('source', 'unknown')}"
                )
                continue

            source = doc.get("source", "unknown")
            doc_id = doc.get("doc_id", str(uuid.uuid4()))
            dataset_id = doc.get("dataset_id")
            tags = doc.get("tags", [])
            language = doc.get("language", "vi")

            # Derive story_id and story_name from filename
            filename_stem = source.rsplit(".", 1)[0] if "." in source else source
            story_id = re.sub(r'(?<=[a-z])(?=[A-Z])', '-', filename_stem).lower()
            story_id = re.sub(r'[^a-z0-9-]', '-', story_id).strip('-')
            story_id = re.sub(r'-+', '-', story_id)
            story_name = filename_stem

            # Extract official_title from first line (e.g. "15. SỰ TÍCH CON DÃ TRÀNG")
            official_title = ""
            first_line = raw_content.split('\n', 1)[0].strip()
            if first_line:
                title_cleaned = re.sub(r'^\d+\.\s*', '', first_line).strip()
                if title_cleaned:
                    official_title = title_cleaned.title()

            # Auto-tag story content using LLM
            if not tags:
                auto_tags = await self._auto_tag_story(raw_content)
                if auto_tags:
                    tags = list(set(tags + auto_tags))
                    logger.bind(tag=TAG).info(
                        f"Auto-tagged '{source}': {tags}"
                    )

            # Chunk document
            chunks = splitter.split_text(raw_content)
            if not chunks:
                continue

            total_chunks = len(chunks)
            logger.bind(tag=TAG).info(
                f"Embedding {total_chunks} chunks from: {source} "
                f"(provider: {self.embedding_provider}, model: {self.embedding_model_name})"
            )

            # Batch embed tất cả chunks
            embeddings = await self._embed_texts(chunks)

            # Build Qdrant points
            points = []
            created_at = datetime.now(timezone.utc).isoformat()
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                points.append(
                    PointStruct(
                        id=str(uuid.uuid4()),
                        vector=embedding,
                        payload={
                            "content": chunk,
                            "source": source,
                            "doc_id": doc_id,
                            "dataset_id": dataset_id,
                            "story_id": story_id,
                            "story_name": story_name,
                            "official_title": official_title,
                            "part_index": i,
                            "total_parts": total_chunks,
                            "language": language,
                            "tags": tags,
                            "created_at": created_at,
                        },
                    )
                )

            # Upsert theo batch 100 points
            batch_size = 100
            for batch_start in range(0, len(points), batch_size):
                batch = points[batch_start:batch_start + batch_size]
                await client.upsert(
                    collection_name=self.collection_name,
                    points=batch,
                )

            total_added += len(points)
            logger.bind(tag=TAG).info(
                f"Added {len(points)} chunks from '{source}' (doc_id: {doc_id})"
            )

        return total_added

    async def _auto_tag_story(self, content_preview: str) -> List[str]:
        """Use LLM to generate topic tags for a story."""
        try:
            import json as _json
            prompt = (
                "Đọc đoạn truyện sau và trả về 3-5 tags tiếng Việt mô tả chủ đề "
                "(VD: động vật, trái cây, lịch sử, tình anh em, lòng hiếu thảo...). "
                "Trả về JSON array, KHÔNG giải thích.\n\n"
                f"{content_preview[:2000]}"
            )
            embeddings = await self._embed_texts([prompt])
            if not embeddings:
                return []
            # Try to use the configured LLM for tagging
            from core.providers.llm.openai.openai import OpenAILLM
            llm_config = self.config.get("LLM", {})
            if not llm_config:
                return []
            # Find first available LLM config
            llm_name = next(iter(llm_config.keys()), None)
            if not llm_name:
                return []
            llm_cfg = llm_config[llm_name]
            messages = [
                {"role": "system", "content": "Bạn là trợ lý phân loại truyện. Chỉ trả về JSON array các tags."},
                {"role": "user", "content": prompt},
            ]
            # Use a simple HTTP call to avoid complex LLM provider instantiation
            import aiohttp
            api_key = llm_cfg.get("api_key", "")
            base_url = llm_cfg.get("url", "https://api.openai.com/v1")
            model = llm_cfg.get("model_name", "gpt-4o-mini")
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json={"model": model, "messages": messages, "temperature": 0.3, "max_tokens": 100},
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        text = data["choices"][0]["message"]["content"].strip()
                        tags = _json.loads(text)
                        if isinstance(tags, list):
                            return [str(t).strip() for t in tags if t]
            return []
        except Exception as e:
            logger.bind(tag=TAG).warning(f"Auto-tagging failed: {e}")
            return []

    async def delete_documents(self, doc_ids: List[str]) -> int:
        """Xóa tất cả chunks thuộc các doc_id đã cho."""
        if not doc_ids:
            return 0

        from qdrant_client.models import Filter, FieldCondition, MatchAny, FilterSelector

        client = await self._get_client()
        await client.delete(
            collection_name=self.collection_name,
            points_selector=FilterSelector(
                filter=Filter(
                    must=[
                        FieldCondition(
                            key="doc_id",
                            match=MatchAny(any=doc_ids),
                        )
                    ]
                )
            ),
        )
        logger.bind(tag=TAG).info(
            f"Deleted documents: {doc_ids} from collection {self.collection_name}"
        )
        return len(doc_ids)

    async def get_collection_info(self) -> Dict[str, Any]:
        """Lấy thông tin thống kê của collection."""
        client = await self._get_client()
        info = await client.get_collection(self.collection_name)
        return {
            "name": self.collection_name,
            "vectors_count": info.vectors_count or 0,
            "points_count": info.points_count or 0,
            "status": info.status.value if info.status else "unknown",
            "vector_size": self.vector_size,
            "embedding_model": self.embedding_model_name,
            "embedding_provider": self.embedding_provider,
            "qdrant_url": self.qdrant_url,
        }

    async def warmup(self):
        """Pre-load embedding model + connect Qdrant khi server khởi động.

        Gọi method này ở startup để user không phải chờ lần search đầu tiên.
        Idempotent: đã có Gemini + Qdrant client thì trả ngay (không log/spam mỗi lượt tool).
        """
        if self.embedding_provider == "local":
            already_loaded = self._local_model is not None and self._client is not None
        elif self.embedding_provider == "openai":
            already_loaded = self._openai_client is not None and self._client is not None
        elif self.embedding_provider == "bedrock":
            already_loaded = getattr(self, "_bedrock_client", None) is not None and self._client is not None
        else:
            already_loaded = self._gemini_model is not None and self._client is not None

        if already_loaded:
            return

        logger.bind(tag=TAG).info("Warming up RAG provider...")

        if self.embedding_provider == "local":
            self._get_local_model()
        elif self.embedding_provider == "openai":
            pass
        elif self.embedding_provider == "bedrock":
            pass
        else:
            self._get_gemini_model()

        # Connect Qdrant + ensure collection
        await self._get_client()

        if self.warmup_skip_embed_test:
            logger.bind(tag=TAG).info(
                f"RAG warmup OK (embed test skipped): "
                f"model={self.embedding_model_name}, collection={self.collection_name}"
            )
            return

        test_embedding = await self._embed_texts(["warmup test"], for_query=True)
        if test_embedding and len(test_embedding[0]) == self.vector_size:
            logger.bind(tag=TAG).info(
                f"RAG warmup OK: embedding_provider={self.embedding_provider}, "
                f"model={self.embedding_model_name}, "
                f"vector_size={len(test_embedding[0])}, "
                f"collection={self.collection_name}"
            )
        else:
            logger.bind(tag=TAG).warning(
                f"RAG warmup: embedding test returned unexpected size"
            )

    async def get_chunks_by_doc_id(self, doc_id: str) -> List[Dict[str, Any]]:
        """Retrieve all chunks/parts of a document, sorted by part_index."""
        from qdrant_client.models import Filter, FieldCondition, MatchValue

        client = await self._get_client()
        all_points = []
        offset = None
        limit = 100

        while True:
            result = await client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="doc_id",
                            match=MatchValue(value=doc_id),
                        )
                    ]
                ),
                limit=limit,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )
            points, next_offset = result
            all_points.extend(points)
            if next_offset is None:
                break
            offset = next_offset

        chunks = []
        for p in all_points:
            payload = p.payload or {}
            chunks.append({
                "content": payload.get("content", ""),
                "part_index": payload.get("part_index", payload.get("chunk_index", 0)),
                "total_parts": payload.get("total_parts", payload.get("total_chunks", 0)),
                "story_id": payload.get("story_id", ""),
                "story_name": payload.get("story_name", ""),
                "doc_id": payload.get("doc_id", ""),
                "source": payload.get("source", ""),
            })

        chunks.sort(key=lambda c: c["part_index"])
        logger.bind(tag=TAG).info(
            f"get_chunks_by_doc_id('{doc_id}'): {len(chunks)} parts retrieved"
        )
        return chunks

    async def list_unique_stories(self) -> List[Dict[str, str]]:
        """Return deduplicated list of {story_id, story_name, official_title, tags} from all points."""
        from qdrant_client.models import Filter

        client = await self._get_client()
        seen = {}
        offset = None
        limit = 100

        while True:
            result = await client.scroll(
                collection_name=self.collection_name,
                limit=limit,
                offset=offset,
                with_payload=["story_id", "story_name", "official_title", "tags"],
                with_vectors=False,
            )
            points, next_offset = result
            for p in points:
                payload = p.payload or {}
                sid = payload.get("story_id", "")
                if sid and sid not in seen:
                    seen[sid] = {
                        "story_name": payload.get("story_name", sid),
                        "official_title": payload.get("official_title", ""),
                        "tags": payload.get("tags", []),
                    }
            if next_offset is None:
                break
            offset = next_offset

        stories = [
            {
                "story_id": sid,
                "story_name": meta["story_name"],
                "official_title": meta["official_title"],
                "tags": meta["tags"],
            }
            for sid, meta in seen.items()
        ]
        logger.bind(tag=TAG).info(
            f"list_unique_stories: {len(stories)} stories in collection"
        )
        return stories

    async def close(self):
        """Đóng kết nối Qdrant và giải phóng tài nguyên."""
        if self._client is not None:
            await self._client.close()
            self._client = None
            logger.bind(tag=TAG).debug("Qdrant client closed")
