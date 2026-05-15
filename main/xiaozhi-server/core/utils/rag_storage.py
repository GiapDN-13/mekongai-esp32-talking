"""
RAG metadata storage — lưu thông tin datasets và documents vào file JSON local.

Lý do dùng JSON thay vì SQLite:
- Không cần thêm dependency
- Phù hợp với quy mô nhỏ (vài chục datasets, vài trăm documents)
- Dễ backup và inspect
- Thread-safe với portalocker (đã có trong requirements.txt)

Cấu trúc file data/rag_metadata.json:
{
  "datasets": {
    "dataset_uuid": {
      "id": "uuid",
      "datasetId": "uuid",   # alias cho id, dùng trong UI
      "name": "Tên KB",
      "description": "...",
      "status": 1,
      "collection_name": "xiaozhi_knowledge",
      "createdAt": "ISO timestamp",
      "documentCount": 3
    }
  },
  "documents": {
    "doc_uuid": {
      "id": "uuid",
      "datasetId": "dataset_uuid",
      "name": "filename.pdf",
      "source": "filename.pdf",
      "parseStatusCode": 0,  # 0=pending, 1=parsing, 2=done, 3=failed, 4=done_with_error
      "sliceCount": 12,
      "createdAt": "ISO timestamp",
      "tags": ["tag1"]
    }
  }
}
"""

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

import portalocker
from config.logger import setup_logging

TAG = __name__
logger = setup_logging()

# Parse status codes (khớp với UI)
PARSE_STATUS_PENDING = 0    # Chưa parse
PARSE_STATUS_PARSING = 1    # Đang parse
PARSE_STATUS_DONE = 2       # Parse xong
PARSE_STATUS_FAILED = 3     # Parse thất bại
PARSE_STATUS_PARTIAL = 4    # TODO: dead code — remove (0 callers)


class RAGStorage:
    """Thread-safe JSON storage cho RAG metadata."""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.metadata_path = os.path.join(data_dir, "rag_metadata.json")
        self.documents_dir = os.path.join(data_dir, "rag_documents")
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(self.documents_dir, exist_ok=True)
        self._ensure_file()

    def _ensure_file(self):
        """Tạo file metadata nếu chưa tồn tại."""
        if not os.path.exists(self.metadata_path):
            self._write({"datasets": {}, "documents": {}})

    def _read(self) -> dict:
        """Đọc metadata từ file (thread-safe)."""
        try:
            with portalocker.Lock(self.metadata_path, "r", timeout=5,
                                  encoding="utf-8") as f:
                content = f.read()
                if not content.strip():
                    return {"datasets": {}, "documents": {}}
                return json.loads(content)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"datasets": {}, "documents": {}}
        except Exception as e:
            logger.bind(tag=TAG).error(f"RAGStorage read error: {e}")
            return {"datasets": {}, "documents": {}}

    def _write(self, data: dict):
        """Ghi metadata vào file (thread-safe)."""
        try:
            os.makedirs(self.data_dir, exist_ok=True)
            with portalocker.Lock(self.metadata_path, "w", timeout=5,
                                  encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.bind(tag=TAG).error(f"RAGStorage write error: {e}")
            raise

    def _now(self) -> str:
        """Trả về ISO timestamp hiện tại."""
        return datetime.now(timezone.utc).isoformat()

    # =========================================================================
    # DATASET CRUD
    # =========================================================================

    def create_dataset(
        self,
        name: str,
        description: str = "",
        status: int = 1,
        collection_name: str = "xiaozhi_knowledge",
        rag_model_id: Optional[str] = None,
    ) -> dict:
        """Tạo dataset mới. Trả về dataset dict."""
        data = self._read()
        dataset_id = str(uuid.uuid4())
        dataset = {
            "id": dataset_id,
            "datasetId": dataset_id,
            "name": name,
            "description": description,
            "status": status,
            "collection_name": collection_name,
            "ragModelId": rag_model_id,
            "createdAt": self._now(),
            "documentCount": 0,
        }
        data["datasets"][dataset_id] = dataset
        self._write(data)
        logger.bind(tag=TAG).info(f"Created dataset: {name} (id={dataset_id})")
        return dataset

    def get_dataset(self, dataset_id: str) -> Optional[dict]:
        """Lấy dataset theo id."""
        data = self._read()
        return data["datasets"].get(dataset_id)

    def list_datasets(
        self,
        page: int = 1,
        page_size: int = 10,
        name_filter: str = "",
    ) -> dict:
        """Lấy danh sách datasets có phân trang."""
        data = self._read()
        datasets = list(data["datasets"].values())

        # Filter theo tên
        if name_filter:
            name_lower = name_filter.lower()
            datasets = [d for d in datasets if name_lower in d["name"].lower()]

        # Cập nhật documentCount
        for ds in datasets:
            ds["documentCount"] = sum(
                1 for doc in data["documents"].values()
                if doc["datasetId"] == ds["id"]
            )

        # Sort by createdAt desc
        datasets.sort(key=lambda x: x.get("createdAt", ""), reverse=True)

        total = len(datasets)
        start = (page - 1) * page_size
        end = start + page_size
        page_data = datasets[start:end]

        return {"list": page_data, "total": total, "page": page, "page_size": page_size}

    def update_dataset(self, dataset_id: str, updates: dict) -> Optional[dict]:
        """Cập nhật dataset. Trả về dataset đã cập nhật."""
        data = self._read()
        if dataset_id not in data["datasets"]:
            return None
        allowed_fields = {"name", "description", "status", "ragModelId", "collection_name"}
        for key, value in updates.items():
            if key in allowed_fields:
                data["datasets"][dataset_id][key] = value
        self._write(data)
        return data["datasets"][dataset_id]

    def delete_dataset(self, dataset_id: str) -> bool:
        """Xóa dataset và tất cả documents của nó."""
        data = self._read()
        if dataset_id not in data["datasets"]:
            return False
        del data["datasets"][dataset_id]
        # Xóa tất cả documents thuộc dataset này
        doc_ids_to_delete = [
            doc_id for doc_id, doc in data["documents"].items()
            if doc["datasetId"] == dataset_id
        ]
        for doc_id in doc_ids_to_delete:
            del data["documents"][doc_id]
        self._write(data)
        logger.bind(tag=TAG).info(
            f"Deleted dataset {dataset_id} and {len(doc_ids_to_delete)} documents"
        )
        return True

    def delete_datasets(self, dataset_ids: List[str]) -> int:  # TODO: dead code — remove (0 callers)
        """Xóa nhiều datasets. Trả về số lượng đã xóa."""
        count = 0
        for dataset_id in dataset_ids:
            if self.delete_dataset(dataset_id):
                count += 1
        return count

    # =========================================================================
    # DOCUMENT CRUD
    # =========================================================================

    def create_document(
        self,
        dataset_id: str,
        name: str,
        source: str = "",
        tags: Optional[List[str]] = None,
    ) -> Optional[dict]:
        """Tạo document record. Trả về document dict."""
        data = self._read()
        if dataset_id not in data["datasets"]:
            return None
        doc_id = str(uuid.uuid4())
        document = {
            "id": doc_id,
            "datasetId": dataset_id,
            "name": name,
            "source": source or name,
            "filePath": "",  # set after saving file
            "parseStatusCode": PARSE_STATUS_PENDING,
            "sliceCount": 0,
            "tags": tags or [],
            "createdAt": self._now(),
        }
        data["documents"][doc_id] = document
        self._write(data)
        return document

    def get_document(self, doc_id: str) -> Optional[dict]:
        """Lấy document theo id."""
        data = self._read()
        return data["documents"].get(doc_id)

    def list_documents(
        self,
        dataset_id: str,
        page: int = 1,
        page_size: int = 10,
        name_filter: str = "",
    ) -> dict:
        """Lấy danh sách documents của một dataset."""
        data = self._read()
        docs = [
            doc for doc in data["documents"].values()
            if doc["datasetId"] == dataset_id
        ]
        if name_filter:
            name_lower = name_filter.lower()
            docs = [d for d in docs if name_lower in d["name"].lower()]

        docs.sort(key=lambda x: x.get("createdAt", ""), reverse=True)

        total = len(docs)
        start = (page - 1) * page_size
        end = start + page_size
        return {
            "list": docs[start:end],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    def update_document_status(
        self,
        doc_id: str,
        parse_status_code: int,
        slice_count: int = 0,
    ) -> Optional[dict]:
        """Cập nhật trạng thái parse và số chunks của document."""
        data = self._read()
        if doc_id not in data["documents"]:
            return None
        data["documents"][doc_id]["parseStatusCode"] = parse_status_code
        if slice_count > 0:
            data["documents"][doc_id]["sliceCount"] = slice_count
        self._write(data)
        return data["documents"][doc_id]

    def delete_document(self, doc_id: str) -> Optional[str]:
        """Xóa document. Trả về doc_id nếu thành công."""
        data = self._read()
        if doc_id not in data["documents"]:
            return None
        del data["documents"][doc_id]
        self._write(data)
        return doc_id

    # =========================================================================
    # DOCUMENT FILE STORAGE
    # =========================================================================

    def _safe_filename(self, filename: str) -> str:
        # Keep it simple; avoid path traversal and weird separators
        name = (filename or "document").replace("\\", "_").replace("/", "_").strip()
        return name if name else "document"

    def get_document_dir(self, dataset_id: str, doc_id: str) -> str:
        return os.path.join(self.documents_dir, dataset_id, doc_id)

    def get_document_file_path(self, dataset_id: str, doc_id: str) -> Optional[str]:
        doc = self.get_document(doc_id)
        if not doc or doc.get("datasetId") != dataset_id:
            return None
        return doc.get("filePath") or None

    def save_document_file(self, dataset_id: str, doc_id: str, filename: str, content: bytes) -> str:
        """Lưu file upload bền vững để phục vụ re-parse."""
        safe_name = self._safe_filename(filename)
        doc_dir = self.get_document_dir(dataset_id, doc_id)
        os.makedirs(doc_dir, exist_ok=True)

        file_path = os.path.join(doc_dir, safe_name)
        with open(file_path, "wb") as f:
            f.write(content)

        # Update metadata (best-effort, overwrite filePath)
        data = self._read()
        if doc_id in data["documents"]:
            data["documents"][doc_id]["filePath"] = file_path
            self._write(data)

        return file_path

    def delete_document_file(self, dataset_id: str, doc_id: str) -> bool:
        """Xóa file đã lưu và thư mục doc (best-effort)."""
        file_path = self.get_document_file_path(dataset_id, doc_id)
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass

        # Remove doc directory if empty
        doc_dir = self.get_document_dir(dataset_id, doc_id)
        try:
            if os.path.isdir(doc_dir):
                # attempt to delete all remnants
                for root, dirs, files in os.walk(doc_dir, topdown=False):
                    for fn in files:
                        try:
                            os.remove(os.path.join(root, fn))
                        except Exception:
                            pass
                    for dn in dirs:
                        try:
                            os.rmdir(os.path.join(root, dn))
                        except Exception:
                            pass
                try:
                    os.rmdir(doc_dir)
                except Exception:
                    pass
        except Exception:
            pass
        return True

    def delete_dataset_files(self, dataset_id: str) -> bool:
        """Xóa toàn bộ files đã lưu cho dataset (best-effort)."""
        dataset_dir = os.path.join(self.documents_dir, dataset_id)
        if not os.path.isdir(dataset_dir):
            return True
        try:
            for root, dirs, files in os.walk(dataset_dir, topdown=False):
                for fn in files:
                    try:
                        os.remove(os.path.join(root, fn))
                    except Exception:
                        pass
                for dn in dirs:
                    try:
                        os.rmdir(os.path.join(root, dn))
                    except Exception:
                        pass
            try:
                os.rmdir(dataset_dir)
            except Exception:
                pass
        except Exception:
            pass
        return True

    def get_documents_by_dataset(self, dataset_id: str) -> List[dict]:
        """Lấy tất cả documents của một dataset (không phân trang)."""
        data = self._read()
        return [
            doc for doc in data["documents"].values()
            if doc["datasetId"] == dataset_id
        ]
