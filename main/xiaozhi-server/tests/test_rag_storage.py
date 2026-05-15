"""Tests for core.utils.rag_storage.RAGStorage — CRUD with tmp_path."""

import os
import json
import pytest
from unittest.mock import MagicMock, patch

# Patch logger before importing RAGStorage so it doesn't try to load config
with patch("core.utils.rag_storage.setup_logging", return_value=MagicMock()):
    from core.utils.rag_storage import RAGStorage, PARSE_STATUS_DONE, PARSE_STATUS_PENDING


@pytest.fixture
def storage(tmp_path):
    """Create a RAGStorage backed by a temp directory."""
    return RAGStorage(data_dir=str(tmp_path))


class TestDatasetCRUD:
    def test_create_and_get(self, storage):
        ds = storage.create_dataset("Test KB", description="A test knowledge base")
        assert ds["name"] == "Test KB"
        assert ds["description"] == "A test knowledge base"
        assert ds["documentCount"] == 0

        fetched = storage.get_dataset(ds["id"])
        assert fetched is not None
        assert fetched["name"] == "Test KB"

    def test_get_nonexistent(self, storage):
        assert storage.get_dataset("does-not-exist") is None

    def test_list_datasets_pagination(self, storage):
        for i in range(5):
            storage.create_dataset(f"KB-{i}")
        result = storage.list_datasets(page=1, page_size=2)
        assert result["total"] == 5
        assert len(result["list"]) == 2
        assert result["page"] == 1

    def test_list_datasets_name_filter(self, storage):
        storage.create_dataset("Alpha")
        storage.create_dataset("Beta")
        storage.create_dataset("Alpha-2")
        result = storage.list_datasets(name_filter="alpha")
        assert result["total"] == 2

    def test_update_dataset(self, storage):
        ds = storage.create_dataset("Original")
        updated = storage.update_dataset(ds["id"], {"name": "Renamed", "status": 0})
        assert updated["name"] == "Renamed"
        assert updated["status"] == 0

    def test_update_nonexistent(self, storage):
        assert storage.update_dataset("fake-id", {"name": "x"}) is None

    def test_update_ignores_disallowed_fields(self, storage):
        ds = storage.create_dataset("DS")
        storage.update_dataset(ds["id"], {"id": "hacked", "name": "OK"})
        fetched = storage.get_dataset(ds["id"])
        assert fetched["id"] == ds["id"]  # id unchanged
        assert fetched["name"] == "OK"

    def test_delete_dataset_cascades_documents(self, storage):
        ds = storage.create_dataset("ToDelete")
        doc = storage.create_document(ds["id"], "doc.txt")
        assert doc is not None
        assert storage.delete_dataset(ds["id"]) is True
        assert storage.get_dataset(ds["id"]) is None
        assert storage.get_document(doc["id"]) is None

    def test_delete_nonexistent(self, storage):
        assert storage.delete_dataset("nope") is False


class TestDocumentCRUD:
    def test_create_and_get(self, storage):
        ds = storage.create_dataset("DS")
        doc = storage.create_document(ds["id"], "readme.pdf", tags=["intro"])
        assert doc["name"] == "readme.pdf"
        assert doc["parseStatusCode"] == PARSE_STATUS_PENDING
        assert doc["tags"] == ["intro"]

        fetched = storage.get_document(doc["id"])
        assert fetched["datasetId"] == ds["id"]

    def test_create_document_for_nonexistent_dataset(self, storage):
        assert storage.create_document("fake", "x.txt") is None

    def test_list_documents(self, storage):
        ds = storage.create_dataset("DS")
        for i in range(4):
            storage.create_document(ds["id"], f"doc{i}.txt")
        result = storage.list_documents(ds["id"], page=1, page_size=2)
        assert result["total"] == 4
        assert len(result["list"]) == 2

    def test_list_documents_name_filter(self, storage):
        ds = storage.create_dataset("DS")
        storage.create_document(ds["id"], "report.pdf")
        storage.create_document(ds["id"], "notes.txt")
        result = storage.list_documents(ds["id"], name_filter="report")
        assert result["total"] == 1

    def test_update_document_status(self, storage):
        ds = storage.create_dataset("DS")
        doc = storage.create_document(ds["id"], "d.txt")
        updated = storage.update_document_status(doc["id"], PARSE_STATUS_DONE, slice_count=10)
        assert updated["parseStatusCode"] == PARSE_STATUS_DONE
        assert updated["sliceCount"] == 10

    def test_update_nonexistent_document_status(self, storage):
        assert storage.update_document_status("fake", PARSE_STATUS_DONE) is None

    def test_delete_document(self, storage):
        ds = storage.create_dataset("DS")
        doc = storage.create_document(ds["id"], "d.txt")
        assert storage.delete_document(doc["id"]) == doc["id"]
        assert storage.get_document(doc["id"]) is None

    def test_delete_nonexistent_document(self, storage):
        assert storage.delete_document("nope") is None


class TestDocumentFileStorage:
    def test_save_and_get_file(self, storage):
        ds = storage.create_dataset("DS")
        doc = storage.create_document(ds["id"], "test.txt")
        content = b"hello world"
        path = storage.save_document_file(ds["id"], doc["id"], "test.txt", content)
        assert os.path.exists(path)
        with open(path, "rb") as f:
            assert f.read() == content

        fetched_path = storage.get_document_file_path(ds["id"], doc["id"])
        assert fetched_path == path

    def test_safe_filename_sanitization(self, storage):
        result = storage._safe_filename("../../etc/passwd")
        assert "/" not in result
        assert "\\" not in result
        assert storage._safe_filename("normal.txt") == "normal.txt"
        assert storage._safe_filename("") == "document"
        assert storage._safe_filename(None) == "document"

    def test_safe_filename_backslash(self, storage):
        assert "\\" not in storage._safe_filename("path\\to\\file.txt")
        assert "/" not in storage._safe_filename("path/to/file.txt")

    def test_delete_document_file(self, storage):
        ds = storage.create_dataset("DS")
        doc = storage.create_document(ds["id"], "x.txt")
        storage.save_document_file(ds["id"], doc["id"], "x.txt", b"data")
        assert storage.delete_document_file(ds["id"], doc["id"]) is True

    def test_get_documents_by_dataset(self, storage):
        ds = storage.create_dataset("DS")
        storage.create_document(ds["id"], "a.txt")
        storage.create_document(ds["id"], "b.txt")
        docs = storage.get_documents_by_dataset(ds["id"])
        assert len(docs) == 2
