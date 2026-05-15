-- Ensure Plugin provider UI for search_from_qdrant includes Gemini options

UPDATE ai_model_provider
SET fields = JSON_ARRAY(
    JSON_OBJECT('key', 'description', 'type', 'string', 'label', 'Plugin description (for LLM)', 'default', 'Tìm kiếm thông tin trong knowledge base nội bộ về sản phẩm, dịch vụ, chính sách'),
    JSON_OBJECT('key', 'url', 'type', 'string', 'label', 'Qdrant URL', 'default', 'http://localhost:6333'),
    JSON_OBJECT('key', 'collection_name', 'type', 'string', 'label', 'Collection name', 'default', 'xiaozhi_knowledge'),
    JSON_OBJECT(
        'key', 'embedding_provider',
        'type', 'select',
        'label', 'Embedding provider (gemini / openai / fastembed)',
        'default', 'gemini',
        'options', JSON_ARRAY(
            JSON_OBJECT('label', 'Gemini API', 'value', 'gemini'),
            JSON_OBJECT('label', 'OpenAI API', 'value', 'openai'),
            JSON_OBJECT('label', 'Fastembed (local ONNX)', 'value', 'fastembed')
        )
    ),
    JSON_OBJECT('key', 'embedding_model', 'type', 'string', 'label', 'Embedding model name', 'default', 'text-embedding-004'),
    JSON_OBJECT('key', 'vector_size', 'type', 'number', 'label', 'Vector dimensions', 'default', 768),
    JSON_OBJECT('key', 'gemini_api_key', 'type', 'password', 'label', 'Gemini API key (optional; auto-use LLM key if empty)', 'default', ''),
    JSON_OBJECT('key', 'openai_api_key', 'type', 'password', 'label', 'OpenAI API key (for embedding)', 'default', ''),
    JSON_OBJECT('key', 'openai_base_url', 'type', 'string', 'label', 'OpenAI base URL', 'default', 'https://api.openai.com/v1'),
    JSON_OBJECT('key', 'top_k', 'type', 'number', 'label', 'Top K results', 'default', 3),
    JSON_OBJECT('key', 'score_threshold', 'type', 'string', 'label', 'Score threshold', 'default', '0.55')
)
WHERE id = 'SYSTEM_PLUGIN_QDRANT_SEARCH';
