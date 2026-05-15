-- Add Mem0 Local (OSS + Qdrant) memory provider with Bedrock embedding support
-- Allows switching between OpenAI / Bedrock / Huggingface embedders from UI

-- =========================================================================
-- 1. Add mem0_local provider definition with configurable embedding
-- =========================================================================
DELETE FROM ai_model_provider WHERE id = 'SYSTEM_Memory_mem0_local';
INSERT INTO ai_model_provider (
    id, model_type, provider_code, name, fields, sort,
    creator, create_date, updater, update_date
) VALUES (
    'SYSTEM_Memory_mem0_local', 'Memory', 'mem0_local', 'Mem0 Local (Qdrant)',
    JSON_ARRAY(
        JSON_OBJECT(
            'key', 'qdrant_host',
            'label', 'Qdrant Host',
            'type', 'text',
            'required', true,
            'default', 'localhost'
        ),
        JSON_OBJECT(
            'key', 'qdrant_port',
            'label', 'Qdrant Port',
            'type', 'number',
            'required', true,
            'default', 6333
        ),
        JSON_OBJECT(
            'key', 'collection_name',
            'label', 'Collection name',
            'type', 'text',
            'required', true,
            'default', 'xiaozhi_memory_v2'
        ),
        JSON_OBJECT(
            'key', 'embedder_provider',
            'label', 'Embedding provider',
            'type', 'select',
            'required', true,
            'default', 'aws_bedrock',
            'options', JSON_ARRAY(
                JSON_OBJECT('label', 'AWS Bedrock Titan', 'value', 'aws_bedrock'),
                JSON_OBJECT('label', 'OpenAI API', 'value', 'openai'),
                JSON_OBJECT('label', 'Huggingface (local)', 'value', 'huggingface')
            )
        ),
        JSON_OBJECT(
            'key', 'embedding_model',
            'label', 'Embedding model',
            'type', 'text',
            'required', true,
            'default', 'amazon.titan-embed-text-v2:0'
        ),
        JSON_OBJECT(
            'key', 'aws_region',
            'label', 'AWS Region',
            'type', 'text',
            'required', false,
            'default', 'us-east-1'
        ),
        JSON_OBJECT(
            'key', 'aws_access_key_id',
            'label', 'AWS Access Key ID',
            'type', 'password',
            'required', false,
            'default', ''
        ),
        JSON_OBJECT(
            'key', 'aws_secret_access_key',
            'label', 'AWS Secret Access Key',
            'type', 'password',
            'required', false,
            'default', ''
        ),
        JSON_OBJECT(
            'key', 'openai_api_key',
            'label', 'OpenAI API key (if using openai provider)',
            'type', 'password',
            'required', false,
            'default', ''
        )
    ),
    5,
    1, NOW(), 1, NOW()
);

-- =========================================================================
-- 2. Add mem0_local + Bedrock model config
-- =========================================================================
DELETE FROM ai_model_config WHERE id = 'Memory_mem0_local_bedrock';
INSERT INTO ai_model_config (
    id, model_type, model_code, model_name,
    is_default, is_enabled,
    config_json,
    doc_link, remark, sort,
    creator, create_date, updater, update_date
) VALUES (
    'Memory_mem0_local_bedrock', 'Memory', 'mem0_local', 'Mem0 Local + Bedrock Titan',
    0, 1,
    '{"type":"mem0_local","qdrant_host":"localhost","qdrant_port":6333,"collection_name":"xiaozhi_memory_v2","embedder_provider":"aws_bedrock","embedding_model":"amazon.titan-embed-text-v2:0","aws_region":"us-east-1","aws_access_key_id":"","aws_secret_access_key":""}',
    'https://docs.mem0.ai/components/embedders/overview',
    'Mem0 OSS + Qdrant + AWS Bedrock Titan Embed v2 (1024-dim). Long-term memory, không cần OpenAI.',
    5,
    1, NOW(), 1, NOW()
);

-- =========================================================================
-- 3. Add mem0_local + OpenAI model config (backup option)
-- =========================================================================
DELETE FROM ai_model_config WHERE id = 'Memory_mem0_local_openai';
INSERT INTO ai_model_config (
    id, model_type, model_code, model_name,
    is_default, is_enabled,
    config_json,
    doc_link, remark, sort,
    creator, create_date, updater, update_date
) VALUES (
    'Memory_mem0_local_openai', 'Memory', 'mem0_local', 'Mem0 Local + OpenAI',
    0, 1,
    '{"type":"mem0_local","qdrant_host":"localhost","qdrant_port":6333,"collection_name":"xiaozhi_memory","embedder_provider":"openai","embedding_model":"text-embedding-3-small","openai_api_key":""}',
    'https://docs.mem0.ai/components/embedders/overview',
    'Mem0 OSS + Qdrant + OpenAI text-embedding-3-small (1536-dim). Cần OpenAI API key.',
    6,
    1, NOW(), 1, NOW()
);
