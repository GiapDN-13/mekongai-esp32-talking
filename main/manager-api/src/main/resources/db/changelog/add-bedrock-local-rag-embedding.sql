-- Add Bedrock (AWS Titan) and Local (sentence-transformers) embedding options for RAG
-- Supports: gemini, openai, bedrock, local, fastembed

-- =========================================================================
-- 1. Update RAG provider form fields: add Bedrock + Local options
-- =========================================================================
UPDATE ai_model_provider
SET fields = JSON_ARRAY(
    JSON_OBJECT('key', 'url', 'label', 'Qdrant URL', 'type', 'text', 'required', true, 'default', 'http://localhost:6333'),
    JSON_OBJECT('key', 'api_key', 'label', 'Qdrant API key (optional)', 'type', 'password', 'required', false, 'default', ''),
    JSON_OBJECT('key', 'collection_name', 'label', 'Collection name', 'type', 'text', 'required', true, 'default', 'xiaozhi_knowledge_v2'),
    JSON_OBJECT(
        'key', 'embedding_provider',
        'label', 'Embedding provider',
        'type', 'select',
        'required', true,
        'default', 'local',
        'options', JSON_ARRAY(
            JSON_OBJECT('label', 'Local BGE-M3 (offline, no API key)', 'value', 'local'),
            JSON_OBJECT('label', 'Gemini API', 'value', 'gemini'),
            JSON_OBJECT('label', 'OpenAI API', 'value', 'openai'),
            JSON_OBJECT('label', 'AWS Bedrock Titan', 'value', 'bedrock'),
            JSON_OBJECT('label', 'Fastembed (local ONNX)', 'value', 'fastembed')
        )
    ),
    JSON_OBJECT('key', 'embedding_model', 'label', 'Embedding model', 'type', 'text', 'required', true, 'default', 'BAAI/bge-m3'),
    JSON_OBJECT('key', 'vector_size', 'label', 'Vector dimensions', 'type', 'number', 'required', true, 'default', 1024),
    JSON_OBJECT('key', 'gemini_api_key', 'label', 'Gemini API key', 'type', 'password', 'required', false, 'default', ''),
    JSON_OBJECT('key', 'openai_api_key', 'label', 'OpenAI API key', 'type', 'password', 'required', false, 'default', ''),
    JSON_OBJECT('key', 'openai_base_url', 'label', 'OpenAI base URL', 'type', 'text', 'required', false, 'default', 'https://api.openai.com/v1'),
    JSON_OBJECT('key', 'bedrock_region', 'label', 'AWS Region', 'type', 'text', 'required', false, 'default', 'us-east-1'),
    JSON_OBJECT('key', 'bedrock_access_key', 'label', 'AWS Access Key ID', 'type', 'password', 'required', false, 'default', ''),
    JSON_OBJECT('key', 'bedrock_secret_key', 'label', 'AWS Secret Access Key', 'type', 'password', 'required', false, 'default', ''),
    JSON_OBJECT('key', 'top_k', 'label', 'Top K results', 'type', 'number', 'required', false, 'default', 3),
    JSON_OBJECT('key', 'score_threshold', 'label', 'Score threshold (0.0-1.0)', 'type', 'text', 'required', false, 'default', '0.3'),
    JSON_OBJECT('key', 'chunk_size', 'label', 'Chunk size (chars)', 'type', 'number', 'required', false, 'default', 1500),
    JSON_OBJECT('key', 'chunk_overlap', 'label', 'Chunk overlap (chars)', 'type', 'number', 'required', false, 'default', 150)
)
WHERE id = 'SYSTEM_RAG_Qdrant';

-- =========================================================================
-- 2. Update Plugin provider form: search_from_qdrant
-- =========================================================================
UPDATE ai_model_provider
SET fields = JSON_ARRAY(
    JSON_OBJECT('key', 'description', 'type', 'string', 'label', 'Plugin description (for LLM)', 'default', 'Tìm kiếm thông tin trong knowledge base nội bộ'),
    JSON_OBJECT('key', 'url', 'type', 'string', 'label', 'Qdrant URL', 'default', 'http://localhost:6333'),
    JSON_OBJECT('key', 'collection_name', 'type', 'string', 'label', 'Collection name', 'default', 'xiaozhi_knowledge_v2'),
    JSON_OBJECT(
        'key', 'embedding_provider',
        'type', 'select',
        'label', 'Embedding provider',
        'default', 'local',
        'options', JSON_ARRAY(
            JSON_OBJECT('label', 'Local BGE-M3 (offline)', 'value', 'local'),
            JSON_OBJECT('label', 'Gemini API', 'value', 'gemini'),
            JSON_OBJECT('label', 'OpenAI API', 'value', 'openai'),
            JSON_OBJECT('label', 'AWS Bedrock Titan', 'value', 'bedrock'),
            JSON_OBJECT('label', 'Fastembed (local ONNX)', 'value', 'fastembed')
        )
    ),
    JSON_OBJECT('key', 'embedding_model', 'type', 'string', 'label', 'Embedding model name', 'default', 'BAAI/bge-m3'),
    JSON_OBJECT('key', 'vector_size', 'type', 'number', 'label', 'Vector dimensions', 'default', 1024),
    JSON_OBJECT('key', 'gemini_api_key', 'type', 'password', 'label', 'Gemini API key', 'default', ''),
    JSON_OBJECT('key', 'openai_api_key', 'type', 'password', 'label', 'OpenAI API key', 'default', ''),
    JSON_OBJECT('key', 'openai_base_url', 'type', 'string', 'label', 'OpenAI base URL', 'default', 'https://api.openai.com/v1'),
    JSON_OBJECT('key', 'bedrock_region', 'type', 'text', 'label', 'AWS Region', 'default', 'us-east-1'),
    JSON_OBJECT('key', 'bedrock_access_key', 'type', 'password', 'label', 'AWS Access Key ID', 'default', ''),
    JSON_OBJECT('key', 'bedrock_secret_key', 'type', 'password', 'label', 'AWS Secret Access Key', 'default', ''),
    JSON_OBJECT('key', 'top_k', 'type', 'number', 'label', 'Top K results', 'default', 3),
    JSON_OBJECT('key', 'score_threshold', 'type', 'string', 'label', 'Score threshold', 'default', '0.3')
)
WHERE id = 'SYSTEM_PLUGIN_QDRANT_SEARCH';

-- =========================================================================
-- 3. Add Bedrock Titan embedding model config
-- =========================================================================
DELETE FROM ai_model_config WHERE id = 'RAG_Qdrant_Bedrock_Titan';
INSERT INTO ai_model_config (
    id, model_type, model_code, model_name,
    is_default, is_enabled,
    config_json,
    doc_link, remark, sort,
    creator, create_date, updater, update_date
) VALUES (
    'RAG_Qdrant_Bedrock_Titan', 'RAG', 'qdrant', 'Qdrant + Bedrock Titan v2',
    0, 1,
    '{"type":"qdrant","url":"http://localhost:6333","collection_name":"xiaozhi_knowledge_v2","embedding_provider":"bedrock","embedding_model":"amazon.titan-embed-text-v2:0","vector_size":1024,"bedrock_region":"us-east-1","bedrock_access_key":"","bedrock_secret_key":"","top_k":3,"score_threshold":0.3,"chunk_size":1500,"chunk_overlap":150}',
    'https://docs.aws.amazon.com/bedrock/latest/userguide/titan-embedding-models.html',
    'Qdrant + AWS Bedrock Titan Embed v2 (1024-dim). Multilingual, tốt cho tiếng Việt. Cần AWS credentials.',
    4,
    1, NOW(), 1, NOW()
);

-- =========================================================================
-- 4. Add Local BGE-M3 (sentence-transformers) model config
-- =========================================================================
DELETE FROM ai_model_config WHERE id = 'RAG_Qdrant_Local_BGE_M3';
INSERT INTO ai_model_config (
    id, model_type, model_code, model_name,
    is_default, is_enabled,
    config_json,
    doc_link, remark, sort,
    creator, create_date, updater, update_date
) VALUES (
    'RAG_Qdrant_Local_BGE_M3', 'RAG', 'qdrant', 'Qdrant + BGE-M3 (local, offline)',
    1, 1,
    '{"type":"qdrant","url":"http://localhost:6333","collection_name":"xiaozhi_knowledge_v2","embedding_provider":"local","embedding_model":"BAAI/bge-m3","vector_size":1024,"top_k":3,"score_threshold":0.3,"chunk_size":1500,"chunk_overlap":150}',
    'https://huggingface.co/BAAI/bge-m3',
    'Qdrant + BGE-M3 sentence-transformers (1024-dim). Chạy offline, không cần API key. Download ~2GB lần đầu.',
    0,
    1, NOW(), 1, NOW()
);

-- =========================================================================
-- 5. Update existing presets: unset old defaults
-- =========================================================================
UPDATE ai_model_config SET is_default = 0 WHERE id IN ('RAG_Qdrant_OpenAI_Small', 'RAG_Qdrant_OpenAI_Large', 'RAG_Qdrant_Gemini_004', 'RAG_Qdrant_BGE_M3');
