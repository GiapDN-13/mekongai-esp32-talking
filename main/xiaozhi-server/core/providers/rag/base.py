from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class SearchResult:
    """Kết quả tìm kiếm từ vector database."""
    content: str
    score: float
    source: str
    chunk_index: int
    metadata: Dict[str, Any] = field(default_factory=dict)


class RAGProviderBase(ABC):
    """Abstract base class cho tất cả RAG providers."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    @abstractmethod
    async def search(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: float = 0.5,
        filter_tags: Optional[List[str]] = None,
        story_id: Optional[str] = None,
    ) -> List[SearchResult]:
        """Tìm kiếm chunks liên quan đến query.

        Args:
            query: Câu hỏi hoặc từ khóa tìm kiếm.
            top_k: Số lượng kết quả tối đa trả về.
            score_threshold: Ngưỡng điểm tương đồng tối thiểu (0.0 - 1.0).
            filter_tags: Danh sách tags để lọc kết quả (optional).
            story_id: Filter theo story_id (optional, dùng cho Metadata Filtering).

        Returns:
            Danh sách SearchResult được sắp xếp theo score giảm dần.
        """
        pass

    @abstractmethod
    async def add_documents(self, documents: List[Dict[str, Any]]) -> int:
        """Nạp tài liệu vào knowledge base.

        Args:
            documents: Danh sách dict với keys:
                - content (str): Nội dung tài liệu.
                - source (str): Tên file/URL nguồn.
                - doc_id (str, optional): UUID của document (tự tạo nếu không có).
                - tags (List[str], optional): Tags phân loại.
                - language (str, optional): Ngôn ngữ, mặc định "vi".

        Returns:
            Số lượng chunks đã được thêm vào.
        """
        pass

    @abstractmethod
    async def delete_documents(self, doc_ids: List[str]) -> int:
        """Xóa tài liệu theo doc_id.

        Args:
            doc_ids: Danh sách doc_id cần xóa.

        Returns:
            Số lượng points đã xóa.
        """
        pass

    @abstractmethod
    async def get_collection_info(self) -> Dict[str, Any]:
        """Lấy thông tin thống kê của collection.

        Returns:
            Dict chứa: name, points_count, vectors_count, status, embedding_model.
        """
        pass

    @abstractmethod
    async def close(self):
        """Đóng kết nối và giải phóng tài nguyên."""
        pass
