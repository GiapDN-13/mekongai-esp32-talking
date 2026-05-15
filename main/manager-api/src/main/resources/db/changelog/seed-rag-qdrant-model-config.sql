-- Seed RAG model providers and configs: Qdrant with multiple embedding options
-- This provides RAG model options in the Knowledge Base Management UI

-- =========================================================================
-- 1. RAG Model Provider — defines the UI form fields
-- =========================================================================
DELETE FROM ai_model_provider WHERE id = 'SYSTEM_RAG_Qdrant';
INSERT INTO ai_model_provider (
    id, model_type, provider_code, name, fields, sort,
    creator, create_date, updater, update_date
) VALUES (
    'SYSTEM_RAG_Qdrant', 'RAG', 'qdrant', 'Qdrant Vector DB',
    JSON_ARRAY(
        JSON_OBJECT(
            'key', 'url',
            'label', 'Qdrant URL',
            'type', 'text',
            'required', true,
            'default', 'http://localhost:6333'
        ),
        JSON_OBJECT(
            'key', 'api_key',
            'label', 'Qdrant API key (optional)',
            'type', 'password',
            'required', false,
            'default', ''
        ),
        JSON_OBJECT(
            'key', 'collection_name',
            'label', 'Collection name',
            'type', 'text',
            'required', true,
            'default', 'xiaozhi_knowledge'
        ),
        JSON_OBJECT(
            'key', 'embedding_provider',
            'label', 'Embedding provider',
            'type', 'select',
            'required', true,
            'default', 'openai',
            'options', JSON_ARRAY(
                JSON_OBJECT('label', 'OpenAI API', 'value', 'openai'),
                JSON_OBJECT('label', 'Fastembed (local ONNX)', 'value', 'fastembed')
            )
        ),
        JSON_OBJECT(
            'key', 'embedding_model',
            'label', 'Embedding model',
            'type', 'text',
            'required', true,
            'default', 'text-embedding-3-small'
        ),
        JSON_OBJECT(
            'key', 'vector_size',
            'label', 'Vector dimensions',
            'type', 'number',
            'required', true,
            'default', 1536
        ),
        JSON_OBJECT(
            'key', 'openai_api_key',
            'label', 'OpenAI API key (for embedding)',
            'type', 'password',
            'required', false,
            'default', ''
        ),
        JSON_OBJECT(
            'key', 'openai_base_url',
            'label', 'OpenAI base URL',
            'type', 'text',
            'required', false,
            'default', 'https://api.openai.com/v1'
        ),
        JSON_OBJECT(
            'key', 'top_k',
            'label', 'Top K results',
            'type', 'number',
            'required', false,
            'default', 5
        ),
        JSON_OBJECT(
            'key', 'score_threshold',
            'label', 'Score threshold (0.0-1.0)',
            'type', 'text',
            'required', false,
            'default', '0.5'
        ),
        JSON_OBJECT(
            'key', 'chunk_size',
            'label', 'Chunk size (chars)',
            'type', 'number',
            'required', false,
            'default', 512
        ),
        JSON_OBJECT(
            'key', 'chunk_overlap',
            'label', 'Chunk overlap (chars)',
            'type', 'number',
            'required', false,
            'default', 64
        )
    ),
    0,
    1, NOW(), 1, NOW()
);

-- =========================================================================
-- 2. RAG Model Configs — preset configurations users can choose
-- =========================================================================

-- Config 1: OpenAI text-embedding-3-small (recommended for Vietnamese)
DELETE FROM ai_model_config WHERE id = 'RAG_Qdrant';
DELETE FROM ai_model_config WHERE id = 'RAG_Qdrant_OpenAI_Small';
DELETE FROM ai_model_config WHERE id = 'RAG_Qdrant_OpenAI_Large';
DELETE FROM ai_model_config WHERE id = 'RAG_Qdrant_BGE_M3';

INSERT INTO ai_model_config (
    id, model_type, model_code, model_name,
    is_default, is_enabled,
    config_json,
    doc_link, remark, sort,
    creator, create_date, updater, update_date
) VALUES (
    'RAG_Qdrant_OpenAI_Small', 'RAG', 'qdrant', 'Qdrant + OpenAI Small',
    1, 1,
    '{"type":"qdrant","url":"http://localhost:6333","collection_name":"xiaozhi_knowledge","embedding_provider":"openai","embedding_model":"text-embedding-3-small","vector_size":1536,"openai_api_key":"","openai_base_url":"https://api.openai.com/v1","top_k":5,"score_threshold":0.5,"chunk_size":512,"chunk_overlap":64}',
    'https://platform.openai.com/docs/guides/embeddings',
    'Qdrant + OpenAI text-embedding-3-small (1536-dim). Tốt cho tiếng Việt, multilingual. Cần OpenAI API key.',
    1,
    1, NOW(), 1, NOW()
);

-- Config 2: OpenAI text-embedding-3-large (highest quality)
INSERT INTO ai_model_config (
    id, model_type, model_code, model_name,
    is_default, is_enabled,
    config_json,
    doc_link, remark, sort,
    creator, create_date, updater, update_date
) VALUES (
    'RAG_Qdrant_OpenAI_Large', 'RAG', 'qdrant', 'Qdrant + OpenAI Large',
    0, 1,
    '{"type":"qdrant","url":"http://localhost:6333","collection_name":"xiaozhi_knowledge","embedding_provider":"openai","embedding_model":"text-embedding-3-large","vector_size":3072,"openai_api_key":"","openai_base_url":"https://api.openai.com/v1","top_k":5,"score_threshold":0.5,"chunk_size":512,"chunk_overlap":64}',
    'https://platform.openai.com/docs/guides/embeddings',
    'Qdrant + OpenAI text-embedding-3-large (3072-dim). Chất lượng cao nhất, phù hợp Vietnamese corpus lớn.',
    2,
    1, NOW(), 1, NOW()
);

-- Config 3: Fastembed BGE-M3 (local, no API key needed)
INSERT INTO ai_model_config (
    id, model_type, model_code, model_name,
    is_default, is_enabled,
    config_json,
    doc_link, remark, sort,
    creator, create_date, updater, update_date
) VALUES (
    'RAG_Qdrant_BGE_M3', 'RAG', 'qdrant', 'Qdrant + BGE-M3 (local)',
    0, 1,
    '{"type":"qdrant","url":"http://localhost:6333","collection_name":"xiaozhi_knowledge","embedding_provider":"fastembed","embedding_model":"BAAI/bge-m3","vector_size":1024,"model_cache_dir":"models/embeddings","top_k":5,"score_threshold":0.5,"chunk_size":512,"chunk_overlap":64}',
    'https://huggingface.co/BAAI/bge-m3',
    'Qdrant + BGE-M3 local ONNX embedding (1024-dim). Không cần API key, chạy offline. ~570MB download lần đầu.',
    3,
    1, NOW(), 1, NOW()
);

-- =========================================================================
-- 3. Plugin Provider: search_from_qdrant (for function calling)
-- =========================================================================
DELETE FROM ai_model_provider WHERE id = 'SYSTEM_PLUGIN_QDRANT_SEARCH';
INSERT INTO ai_model_provider (
    id, model_type, provider_code, name, fields,
    sort, creator, create_date, updater, update_date
) VALUES (
    'SYSTEM_PLUGIN_QDRANT_SEARCH',
    'Plugin',
    'search_from_qdrant',
    'Knowledge Base search (Qdrant)',
    JSON_ARRAY(
        JSON_OBJECT(
            'key', 'description',
            'type', 'string',
            'label', 'Plugin description (for LLM)',
            'default', 'Tìm kiếm thông tin trong knowledge base nội bộ về sản phẩm, dịch vụ, chính sách'
        ),
        JSON_OBJECT(
            'key', 'url',
            'type', 'string',
            'label', 'Qdrant URL',
            'default', 'http://localhost:6333'
        ),
        JSON_OBJECT(
            'key', 'collection_name',
            'type', 'string',
            'label', 'Collection name',
            'default', 'xiaozhi_knowledge'
        ),
        JSON_OBJECT(
            'key', 'embedding_provider',
            'type', 'string',
            'label', 'Embedding provider (openai / fastembed)',
            'default', 'openai'
        ),
        JSON_OBJECT(
            'key', 'embedding_model',
            'type', 'string',
            'label', 'Embedding model name',
            'default', 'text-embedding-3-small'
        ),
        JSON_OBJECT(
            'key', 'vector_size',
            'type', 'number',
            'label', 'Vector dimensions',
            'default', 1536
        ),
        JSON_OBJECT(
            'key', 'openai_api_key',
            'type', 'password',
            'label', 'OpenAI API key (for embedding)',
            'default', ''
        ),
        JSON_OBJECT(
            'key', 'openai_base_url',
            'type', 'string',
            'label', 'OpenAI base URL',
            'default', 'https://api.openai.com/v1'
        ),
        JSON_OBJECT(
            'key', 'top_k',
            'type', 'number',
            'label', 'Top K results',
            'default', 5
        ),
        JSON_OBJECT(
            'key', 'score_threshold',
            'type', 'string',
            'label', 'Score threshold',
            'default', '0.5'
        )
    ),
    80, 0, NOW(), 0, NOW()
);
