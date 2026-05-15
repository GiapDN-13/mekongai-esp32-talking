import os
import sys
import importlib
from config.logger import setup_logging

logger = setup_logging()


def create_instance(class_name: str, *args, **kwargs):
    """Factory function tạo RAG provider instance.

    Tìm kiếm provider theo pattern:
        core/providers/rag/{class_name}/{class_name}.py

    Args:
        class_name: Tên provider, ví dụ "qdrant".
        *args, **kwargs: Tham số truyền vào constructor của provider.

    Returns:
        Instance của RAGProvider tương ứng.

    Raises:
        ValueError: Nếu không tìm thấy provider.

    Example:
        rag = create_instance("qdrant", {"url": "http://localhost:6333", ...})
    """
    dir_name = class_name
    # Avoid shadowing the installed 'lightrag' package
    if class_name == "lightrag":
        dir_name = "lightrag_provider"

    provider_path = os.path.join(
        "core", "providers", "rag", dir_name, f"{class_name}.py"
    )
    if os.path.exists(provider_path):
        lib_name = f"core.providers.rag.{dir_name}.{class_name}"
        if lib_name not in sys.modules:
            sys.modules[lib_name] = importlib.import_module(lib_name)
        return sys.modules[lib_name].RAGProvider(*args, **kwargs)

    raise ValueError(
        f"Unsupported RAG provider: '{class_name}'. "
        f"Expected file at: {provider_path}"
    )
