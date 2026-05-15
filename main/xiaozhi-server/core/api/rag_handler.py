"""
RAG HTTP API Handler — cung cấp REST endpoints cho manager-web UI.

Endpoints được implement (khớp với knowledgeBase.js):
  GET    /datasets                          → list datasets
  POST   /datasets                          → create dataset
  PUT    /datasets/{dataset_id}             → update dataset
  DELETE /datasets/{dataset_id}             → delete dataset
  DELETE /datasets/batch?ids=id1,id2        → batch delete datasets

  GET    /datasets/{dataset_id}/documents   → list documents
  POST   /datasets/{dataset_id}/documents   → upload & ingest document
  DELETE /datasets/{dataset_id}/documents/{doc_id} → delete document

  POST   /datasets/{dataset_id}/chunks      → parse/ingest document (trigger)
  GET    /datasets/{dataset_id}/documents/{doc_id}/chunks → list chunks

  POST   /datasets/{dataset_id}/retrieval-test → test retrieval
"""

import json
import os
import tempfile
import asyncio
from typing import Optional

from aiohttp import web
from config.logger import setup_logging
from core.api.base_handler import BaseHandler
from core.utils.rag_storage import (
    RAGStorage,
    PARSE_STATUS_PENDING,
    PARSE_STATUS_PARSING,
    PARSE_STATUS_DONE,
    PARSE_STATUS_FAILED,
)

TAG = __name__
logger = setup_logging()


def _ok(data=None, msg="success") -> web.Response:
    """Trả về response thành công theo format chuẩn của hệ thống."""
    body = {"code": 0, "msg": msg, "data": data}
    return web.Response(
        text=json.dumps(body, ensure_ascii=False),
        content_type="application/json",
    )


def _err(msg: str, code: int = 1) -> web.Response:
    """Trả về response lỗi."""
    body = {"code": code, "msg": msg, "data": None}
    return web.Response(
        text=json.dumps(body, ensure_ascii=False),
        content_type="application/json",
        status=200,  # UI expect 200 với code != 0 để hiển thị lỗi
    )


class RAGHandler(BaseHandler):
    """Handler cho tất cả RAG-related API endpoints."""

    def __init__(self, config: dict):
        super().__init__(config)
        data_dir = config.get("log", {}).get("data_dir", "data")
        self.storage = RAGStorage(data_dir=data_dir)
        raw_config = config.get("plugins", {}).get("search_from_qdrant", {})
        if raw_config:
            from core.utils.rag_plugin_config import merge_llm_keys_into_rag_config
            self._rag_config = merge_llm_keys_into_rag_config(dict(raw_config), config)
        else:
            self._rag_config = {}

    def _get_rag_provider(self):
        """Lấy RAG provider instance từ singleton manager (không tạo mới mỗi lần)."""
        if not self._rag_config:
            raise ValueError(
                "search_from_qdrant plugin not configured in config.yaml"
            )
        from core.utils.rag_manager import rag_manager
        return rag_manager.get_provider(self._rag_config)

    async def _rebuild_story_registry(self, rag_provider):
        """Rebuild the global StoryRegistry after document changes."""
        from core.utils.story_registry import story_registry
        if hasattr(rag_provider, "list_unique_stories"):
            try:
                count = await story_registry.rebuild(rag_provider)
                logger.bind(tag=TAG).info(
                    f"StoryRegistry rebuilt: {count} stories"
                )
            except Exception as e:
                logger.bind(tag=TAG).warning(
                    f"StoryRegistry rebuild failed: {e}"
                )

    # =========================================================================
    # CORS
    # =========================================================================

    async def handle_options(self, request):
        response = web.Response(body=b"", content_type="text/plain")
        self._add_cors_headers(response)
        response.headers["Access-Control-Allow-Methods"] = (
            "GET, POST, PUT, DELETE, OPTIONS"
        )
        return response

    def _cors(self, response: web.Response) -> web.Response:
        """Thêm CORS headers vào response."""
        self._add_cors_headers(response)
        return response

    # =========================================================================
    # DATASET ENDPOINTS
    # =========================================================================

    async def list_datasets(self, request: web.Request) -> web.Response:
        """GET /datasets — Lấy danh sách knowledge bases."""
        try:
            page = int(request.rel_url.query.get("page", 1))
            page_size = int(request.rel_url.query.get("page_size", 10))
            name = request.rel_url.query.get("name", "")
            result = self.storage.list_datasets(
                page=page, page_size=page_size, name_filter=name
            )
            return self._cors(_ok(result))
        except Exception as e:
            logger.bind(tag=TAG).error(f"list_datasets error: {e}")
            return self._cors(_err(str(e)))

    async def create_dataset(self, request: web.Request) -> web.Response:
        """POST /datasets — Tạo knowledge base mới."""
        try:
            body = await request.json()
            name = body.get("name", "").strip()
            if not name:
                return self._cors(_err("Tên knowledge base không được để trống"))

            description = body.get("description", "")
            status = int(body.get("status", 1))
            rag_model_id = body.get("ragModelId")

            # Lấy collection_name từ config (hoặc dùng default)
            collection_name = self._rag_config.get(
                "collection_name", "xiaozhi_knowledge"
            )

            dataset = self.storage.create_dataset(
                name=name,
                description=description,
                status=status,
                collection_name=collection_name,
                rag_model_id=rag_model_id,
            )
            return self._cors(_ok(dataset, "Tạo knowledge base thành công"))
        except Exception as e:
            logger.bind(tag=TAG).error(f"create_dataset error: {e}")
            return self._cors(_err(str(e)))

    async def update_dataset(self, request: web.Request) -> web.Response:
        """PUT /datasets/{dataset_id} — Cập nhật knowledge base."""
        try:
            dataset_id = request.match_info["dataset_id"]
            body = await request.json()
            updated = self.storage.update_dataset(dataset_id, body)
            if updated is None:
                return self._cors(_err(f"Không tìm thấy dataset: {dataset_id}"))
            return self._cors(_ok(updated, "Cập nhật thành công"))
        except Exception as e:
            logger.bind(tag=TAG).error(f"update_dataset error: {e}")
            return self._cors(_err(str(e)))

    async def delete_dataset(self, request: web.Request) -> web.Response:
        """DELETE /datasets/{dataset_id} — Xóa knowledge base."""
        try:
            dataset_id = request.match_info["dataset_id"]
            dataset = self.storage.get_dataset(dataset_id)
            if dataset is None:
                return self._cors(_err(f"Không tìm thấy dataset: {dataset_id}"))

            # Xóa tất cả vectors trong Qdrant
            docs = self.storage.get_documents_by_dataset(dataset_id)
            if docs:
                try:
                    rag = self._get_rag_provider()
                    doc_ids = [d["id"] for d in docs]
                    await rag.delete_documents(doc_ids)
                except Exception as qdrant_err:
                    logger.bind(tag=TAG).warning(
                        f"Failed to delete Qdrant vectors for dataset {dataset_id}: {qdrant_err}"
                    )

            self.storage.delete_dataset(dataset_id)

            # Xóa files đã lưu cho dataset (best-effort)
            try:
                self.storage.delete_dataset_files(dataset_id)
            except Exception as file_err:
                logger.bind(tag=TAG).warning(
                    f"Failed to delete stored files for dataset {dataset_id}: {file_err}"
                )

            return self._cors(_ok(None, "Xóa knowledge base thành công"))
        except Exception as e:
            logger.bind(tag=TAG).error(f"delete_dataset error: {e}")
            return self._cors(_err(str(e)))

    async def batch_delete_datasets(self, request: web.Request) -> web.Response:
        """DELETE /datasets/batch?ids=id1,id2 — Xóa nhiều knowledge bases."""
        try:
            ids_str = request.rel_url.query.get("ids", "")
            if not ids_str:
                return self._cors(_err("Không có dataset_id nào được cung cấp"))

            dataset_ids = [i.strip() for i in ids_str.split(",") if i.strip()]
            deleted = 0
            for dataset_id in dataset_ids:
                dataset = self.storage.get_dataset(dataset_id)
                if dataset:
                    docs = self.storage.get_documents_by_dataset(dataset_id)
                    if docs:
                        try:
                            rag = self._get_rag_provider()
                            doc_ids = [d["id"] for d in docs]
                            await rag.delete_documents(doc_ids)
                        except Exception as qdrant_err:
                            logger.bind(tag=TAG).warning(
                                f"Qdrant delete error for {dataset_id}: {qdrant_err}"
                            )
                    self.storage.delete_dataset(dataset_id)
                    try:
                        self.storage.delete_dataset_files(dataset_id)
                    except Exception as file_err:
                        logger.bind(tag=TAG).warning(
                            f"Failed to delete stored files for dataset {dataset_id}: {file_err}"
                        )
                    deleted += 1

            return self._cors(_ok({"deleted": deleted}, f"Đã xóa {deleted} knowledge base"))
        except Exception as e:
            logger.bind(tag=TAG).error(f"batch_delete_datasets error: {e}")
            return self._cors(_err(str(e)))

    # =========================================================================
    # DOCUMENT ENDPOINTS
    # =========================================================================

    async def list_documents(self, request: web.Request) -> web.Response:
        """GET /datasets/{dataset_id}/documents — Lấy danh sách documents."""
        try:
            dataset_id = request.match_info["dataset_id"]
            page = int(request.rel_url.query.get("page", 1))
            page_size = int(request.rel_url.query.get("page_size", 10))
            name = request.rel_url.query.get("name", "")

            if not self.storage.get_dataset(dataset_id):
                return self._cors(_err(f"Không tìm thấy dataset: {dataset_id}"))

            result = self.storage.list_documents(
                dataset_id=dataset_id,
                page=page,
                page_size=page_size,
                name_filter=name,
            )
            return self._cors(_ok(result))
        except Exception as e:
            logger.bind(tag=TAG).error(f"list_documents error: {e}")
            return self._cors(_err(str(e)))

    async def upload_document(self, request: web.Request) -> web.Response:
        """POST /datasets/{dataset_id}/documents — Upload và ingest document."""
        try:
            dataset_id = request.match_info["dataset_id"]
            dataset = self.storage.get_dataset(dataset_id)
            if not dataset:
                return self._cors(_err(f"Không tìm thấy dataset: {dataset_id}"))

            filename = None
            file_content = None

            try:
                reader = await request.multipart()
                while True:
                    field = await reader.next()
                    if field is None:
                        break
                    if field.name == "file":
                        filename = field.filename or "unknown_file"
                        file_content = await field.read()
                        break
            except Exception as mp_err:
                logger.bind(tag=TAG).warning(
                    f"Multipart parse failed, trying raw body: {mp_err}"
                )
                file_content = await request.read()
                filename = request.headers.get(
                    "X-Filename",
                    request.rel_url.query.get("filename", "unknown_file"),
                )

            if not file_content:
                return self._cors(_err("Không tìm thấy file hoặc file rỗng"))

            doc = self.storage.create_document(
                dataset_id=dataset_id,
                name=filename,
                source=filename,
                tags=[],
            )

            if doc is None:
                return self._cors(_err("Không thể tạo document record"))

            saved_path = self.storage.save_document_file(
                dataset_id=dataset_id,
                doc_id=doc["id"],
                filename=filename,
                content=file_content,
            )

            asyncio.create_task(
                self._ingest_document_async(
                    doc_id=doc["id"],
                    file_path=saved_path,
                    filename=filename,
                    dataset=dataset,
                )
            )

            return self._cors(_ok(doc, f"Đã upload '{filename}', đang xử lý..."))

        except Exception as e:
            logger.bind(tag=TAG).error(f"upload_document error: {e}")
            return self._cors(_err(str(e)))

    async def _ingest_document_async(
        self,
        doc_id: str,
        file_path: str,
        filename: str,
        dataset: dict,
    ):
        """Ingest document vào Qdrant bất đồng bộ (chạy trong background)."""
        try:
            # Cập nhật trạng thái: đang parse
            self.storage.update_document_status(doc_id, PARSE_STATUS_PARSING)

            # Load content từ file
            content = await asyncio.get_event_loop().run_in_executor(
                None, self._load_file_content, file_path, filename
            )

            if not content or not content.strip():
                self.storage.update_document_status(doc_id, PARSE_STATUS_FAILED)
                logger.bind(tag=TAG).warning(
                    f"Empty content from file: {filename}"
                )
                return

            # Ingest vào Qdrant
            rag = self._get_rag_provider()
            count = await rag.add_documents([{
                "content": content,
                "source": filename,
                "doc_id": doc_id,
                "dataset_id": dataset.get("id") or dataset.get("datasetId"),
                "tags": [],
                "language": "vi",
            }])

            # Cập nhật trạng thái: done
            self.storage.update_document_status(
                doc_id, PARSE_STATUS_DONE, slice_count=count
            )
            logger.bind(tag=TAG).info(
                f"Ingested '{filename}': {count} chunks (doc_id={doc_id})"
            )

            # Rebuild story registry so new story is immediately fuzzy-matchable
            await self._rebuild_story_registry(rag)

        except Exception as e:
            logger.bind(tag=TAG).error(
                f"Ingest failed for '{filename}' (doc_id={doc_id}): {e}"
            )
            self.storage.update_document_status(doc_id, PARSE_STATUS_FAILED)
        finally:
            # Không xóa file đã lưu (cần để re-parse)
            pass

    def _load_file_content(self, file_path: str, filename: str) -> str:
        """Load content từ file (synchronous, chạy trong thread pool)."""
        ext = os.path.splitext(filename)[1].lower()
        try:
            if ext == ".pdf":
                from pypdf import PdfReader
                reader = PdfReader(file_path)
                pages = [
                    p.extract_text() for p in reader.pages
                    if p.extract_text()
                ]
                return "\n\n".join(pages)
            elif ext in (".docx", ".doc"):
                from docx import Document
                doc = Document(file_path)
                return "\n\n".join(
                    p.text for p in doc.paragraphs if p.text.strip()
                )
            else:
                # TXT, MD, RST, CSV, etc.
                for encoding in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
                    try:
                        with open(file_path, "r", encoding=encoding) as f:
                            return f.read()
                    except UnicodeDecodeError:
                        continue
                raise ValueError(f"Cannot decode file: {filename}")
        except Exception as e:
            logger.bind(tag=TAG).error(
                f"Failed to load file '{filename}': {e}"
            )
            raise

    async def delete_document(self, request: web.Request) -> web.Response:
        """DELETE /datasets/{dataset_id}/documents/{doc_id} — Xóa document."""
        try:
            dataset_id = request.match_info["dataset_id"]
            doc_id = request.match_info["doc_id"]

            doc = self.storage.get_document(doc_id)
            if doc is None or doc["datasetId"] != dataset_id:
                return self._cors(_err(f"Không tìm thấy document: {doc_id}"))

            # Xóa vectors trong Qdrant
            try:
                rag = self._get_rag_provider()
                await rag.delete_documents([doc_id])
            except Exception as qdrant_err:
                logger.bind(tag=TAG).warning(
                    f"Qdrant delete error for doc {doc_id}: {qdrant_err}"
                )

            # Xóa file đã lưu (best-effort)
            try:
                self.storage.delete_document_file(dataset_id=dataset_id, doc_id=doc_id)
            except Exception as file_err:
                logger.bind(tag=TAG).warning(
                    f"Failed to delete stored file for doc {doc_id}: {file_err}"
                )

            self.storage.delete_document(doc_id)

            # Rebuild story registry after deletion
            try:
                rag = self._get_rag_provider()
                await self._rebuild_story_registry(rag)
            except Exception as reg_err:
                logger.bind(tag=TAG).warning(
                    f"StoryRegistry rebuild after delete failed: {reg_err}"
                )

            return self._cors(_ok(None, "Xóa document thành công"))
        except Exception as e:
            logger.bind(tag=TAG).error(f"delete_document error: {e}")
            return self._cors(_err(str(e)))

    # =========================================================================
    # PARSE / CHUNKS ENDPOINTS
    # =========================================================================

    async def parse_documents(self, request: web.Request) -> web.Response:
        """POST /datasets/{dataset_id}/chunks — Trigger re-parse documents."""
        try:
            dataset_id = request.match_info["dataset_id"]
            dataset = self.storage.get_dataset(dataset_id)
            if not dataset:
                return self._cors(_err(f"Không tìm thấy dataset: {dataset_id}"))

            body = await request.json()
            doc_ids = body.get("document_ids", [])

            if not doc_ids:
                return self._cors(_err("Không có document_id nào được cung cấp"))

            triggered = []
            for doc_id in doc_ids:
                doc = self.storage.get_document(doc_id)
                if doc and doc["datasetId"] == dataset_id:
                    # Reset về pending để trigger re-parse
                    self.storage.update_document_status(
                        doc_id, PARSE_STATUS_PENDING, slice_count=0
                    )
                    # Trigger ingest lại từ file đã lưu
                    file_path = self.storage.get_document_file_path(dataset_id, doc_id)
                    if not file_path or not os.path.exists(file_path):
                        # Mark failed nếu không còn file
                        self.storage.update_document_status(doc_id, PARSE_STATUS_FAILED)
                        continue
                    asyncio.create_task(
                        self._ingest_document_async(
                            doc_id=doc_id,
                            file_path=file_path,
                            filename=doc.get("name", "unknown_file"),
                            dataset=dataset,
                        )
                    )
                    triggered.append(doc_id)

            return self._cors(
                _ok(
                    {"triggered": triggered},
                    f"Đã kích hoạt parse cho {len(triggered)} document(s)"
                )
            )
        except Exception as e:
            logger.bind(tag=TAG).error(f"parse_documents error: {e}")
            return self._cors(_err(str(e)))

    async def list_chunks(self, request: web.Request) -> web.Response:
        """GET /datasets/{dataset_id}/documents/{doc_id}/chunks — Lấy danh sách chunks."""
        try:
            dataset_id = request.match_info["dataset_id"]
            doc_id = request.match_info["doc_id"]
            page = int(request.rel_url.query.get("page", 1))
            page_size = int(request.rel_url.query.get("page_size", 10))
            keywords = request.rel_url.query.get("keywords", "")

            doc = self.storage.get_document(doc_id)
            if doc is None or doc["datasetId"] != dataset_id:
                return self._cors(_err(f"Không tìm thấy document: {doc_id}"))

            # Lấy chunks từ Qdrant theo doc_id filter
            try:
                from qdrant_client.models import Filter, FieldCondition, MatchValue
                rag = self._get_rag_provider()
                client = await rag._get_client()

                # Scroll để lấy tất cả chunks của document
                scroll_filter = Filter(
                    must=[
                        FieldCondition(
                            key="doc_id",
                            match=MatchValue(value=doc_id),
                        )
                    ]
                )
                if keywords:
                    # Thêm keyword filter nếu có
                    pass  # Qdrant không hỗ trợ full-text search trực tiếp

                results, _ = await client.scroll(
                    collection_name=rag.collection_name,
                    scroll_filter=scroll_filter,
                    limit=1000,
                    with_payload=True,
                    with_vectors=False,
                )

                chunks = []
                for point in results:
                    chunk = {
                        "id": str(point.id),
                        "content": point.payload.get("content", ""),
                        "chunk_index": point.payload.get("chunk_index", 0),
                        "source": point.payload.get("source", ""),
                    }
                    if keywords:
                        if keywords.lower() in chunk["content"].lower():
                            chunks.append(chunk)
                    else:
                        chunks.append(chunk)

                # Sort by chunk_index
                chunks.sort(key=lambda x: x["chunk_index"])

                # Phân trang
                total = len(chunks)
                start = (page - 1) * page_size
                end = start + page_size
                page_chunks = chunks[start:end]

                return self._cors(_ok({
                    "list": page_chunks,
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                }))

            except Exception as qdrant_err:
                logger.bind(tag=TAG).warning(
                    f"Failed to get chunks from Qdrant: {qdrant_err}"
                )
                return self._cors(_ok({
                    "list": [],
                    "total": 0,
                    "page": page,
                    "page_size": page_size,
                }))

        except Exception as e:
            logger.bind(tag=TAG).error(f"list_chunks error: {e}")
            return self._cors(_err(str(e)))

    # =========================================================================
    # RETRIEVAL TEST ENDPOINT
    # =========================================================================

    async def retrieval_test(self, request: web.Request) -> web.Response:
        """POST /datasets/{dataset_id}/retrieval-test — Test retrieval."""
        try:
            dataset_id = request.match_info["dataset_id"]
            if not self.storage.get_dataset(dataset_id):
                return self._cors(_err(f"Không tìm thấy dataset: {dataset_id}"))

            body = await request.json()
            query = body.get("query", "").strip()
            top_k = int(body.get("top_k", 5))
            score_threshold = float(body.get("score_threshold", 0.3))

            if not query:
                return self._cors(_err("Query không được để trống"))

            logger.bind(tag=TAG).info(
                f"retrieval_test: query='{query}', top_k={top_k}, "
                f"score_threshold={score_threshold}, dataset_id={dataset_id}"
            )

            rag = self._get_rag_provider()

            results = await rag.search(
                query=query,
                top_k=top_k,
                score_threshold=score_threshold,
            )

            chunks = [
                {
                    "content": r.content,
                    "score": round(r.score, 4),
                    "source": r.source,
                    "chunk_index": r.chunk_index,
                }
                for r in results
            ]

            return self._cors(_ok({
                "query": query,
                "results": chunks,
                "total": len(chunks),
            }))

        except Exception as e:
            logger.bind(tag=TAG).error(f"retrieval_test error: {e}")
            return self._cors(_err(str(e)))

    # =========================================================================
    # RAG MODELS ENDPOINT
    # =========================================================================

    async def get_rag_models(self, request: web.Request) -> web.Response:
        """GET /datasets/rag-models — Lấy danh sách RAG models có sẵn."""
        try:
            rag_cfg = self._rag_config
            qdrant_url = rag_cfg.get("url", "http://localhost:6333") if rag_cfg else "http://localhost:6333"
            collection = rag_cfg.get("collection_name", "xiaozhi_knowledge") if rag_cfg else "xiaozhi_knowledge"
            provider = rag_cfg.get("rag_provider", "qdrant") if rag_cfg else "qdrant"

            active_model = (rag_cfg.get("embedding_model") or "text-embedding-3-small") if rag_cfg else "text-embedding-3-small"

            presets = [
                {
                    "id": "lightrag-openai-small",
                    "modelName": f"LightRAG + OpenAI text-embedding-3-small (1536d)",
                    "modelCode": "lightrag",
                    "embeddingProvider": "openai",
                    "embeddingModel": "text-embedding-3-small",
                    "collectionName": collection,
                    "vectorSize": 1536,
                    "qdrantUrl": qdrant_url,
                    "isEnabled": 1,
                    "description": "LightRAG GraphRAG: knowledge graph + vector hybrid search",
                },
            ]

            for model in presets:
                model["isDefault"] = 1 if model["embeddingModel"] == active_model else 0

            if not any(m["isDefault"] for m in presets):
                presets[0]["isDefault"] = 1

            logger.bind(tag=TAG).debug(
                f"get_rag_models: returning {len(presets)} model(s), "
                f"active: {provider}/{active_model}"
            )
            return self._cors(_ok(presets))

        except Exception as e:
            logger.bind(tag=TAG).error(f"get_rag_models error: {e}")
            return self._cors(_err(str(e)))

    async def rag_readiness(self, request: web.Request) -> web.Response:
        """GET /datasets/rag-readiness — trạng thái warmup/ready của RAG provider."""
        try:
            from core.utils.rag_manager import rag_manager

            status = rag_manager.get_status()
            return self._cors(_ok(status))
        except Exception as e:
            logger.bind(tag=TAG).error(f"rag_readiness error: {e}")
            return self._cors(_err(str(e)))
