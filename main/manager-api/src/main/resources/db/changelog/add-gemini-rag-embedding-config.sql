-- Add Gemini embedding option for RAG (Qdrant)

-- 1) Add/refresh Gemini preset model config
DELETE FROM ai_model_config WHERE id = 'RAG_Qdrant_Gemini_004';

INSERT INTO ai_model_config (
    id, model_type, model_code, model_name,
    is_default, is_enabled,
    config_json,
    doc_link, remark, sort,
    creator, create_date, updater, update_date
) VALUES (
    'RAG_Qdrant_Gemini_004', 'RAG', 'qdrant', 'Qdrant + Gemini 004',
    0, 1,
    '{"type":"qdrant","url":"http://localhost:6333","collection_name":"xiaozhi_knowledge","embedding_provider":"gemini","embedding_model":"text-embedding-004","vector_size":768,"gemini_api_key":"","top_k":3,"score_threshold":0.55,"chunk_size":700,"chunk_overlap":60}',
    'https://ai.google.dev/gemini-api/docs/embeddings',
    'Qdrant + Gemini text-embedding-004 (768-dim). Nhanh, tối ưu chi phí, tốt cho tiếng Việt.',
    0,
    1, NOW(), 1, NOW()
);

-- 2) Update RAG provider form fields: add Gemini option + key field
UPDATE ai_model_provider
SET fields = JSON_ARRAY(
    JSON_OBJECT('key', 'url', 'label', 'Qdrant URL', 'type', 'text', 'required', true, 'default', 'http://localhost:6333'),
    JSON_OBJECT('key', 'api_key', 'label', 'Qdrant API key (optional)', 'type', 'password', 'required', false, 'default', ''),
    JSON_OBJECT('key', 'collection_name', 'label', 'Collection name', 'type', 'text', 'required', true, 'default', 'xiaozhi_knowledge'),
    JSON_OBJECT(
        'key', 'embedding_provider',
        'label', 'Embedding provider',
        'type', 'select',
        'required', true,
        'default', 'gemini',
        'options', JSON_ARRAY(
            JSON_OBJECT('label', 'Gemini API', 'value', 'gemini'),
            JSON_OBJECT('label', 'OpenAI API', 'value', 'openai'),
            JSON_OBJECT('label', 'Fastembed (local ONNX)', 'value', 'fastembed')
        )
    ),
    JSON_OBJECT('key', 'embedding_model', 'label', 'Embedding model', 'type', 'text', 'required', true, 'default', 'text-embedding-004'),
    JSON_OBJECT('key', 'vector_size', 'label', 'Vector dimensions', 'type', 'number', 'required', true, 'default', 768),
    JSON_OBJECT('key', 'gemini_api_key', 'label', 'Gemini API key (optional; can auto-use LLM Gemini key)', 'type', 'password', 'required', false, 'default', ''),
    JSON_OBJECT('key', 'openai_api_key', 'label', 'OpenAI API key (for embedding)', 'type', 'password', 'required', false, 'default', ''),
    JSON_OBJECT('key', 'openai_base_url', 'label', 'OpenAI base URL', 'type', 'text', 'required', false, 'default', 'https://api.openai.com/v1'),
    JSON_OBJECT('key', 'top_k', 'label', 'Top K results', 'type', 'number', 'required', false, 'default', 3),
    JSON_OBJECT('key', 'score_threshold', 'label', 'Score threshold (0.0-1.0)', 'type', 'text', 'required', false, 'default', '0.55'),
    JSON_OBJECT('key', 'chunk_size', 'label', 'Chunk size (chars)', 'type', 'number', 'required', false, 'default', 700),
    JSON_OBJECT('key', 'chunk_overlap', 'label', 'Chunk overlap (chars)', 'type', 'number', 'required', false, 'default', 60)
)
WHERE id = 'SYSTEM_RAG_Qdrant';

-- 3) Update Plugin provider form: search_from_qdrant (Knowledge Base search)
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
