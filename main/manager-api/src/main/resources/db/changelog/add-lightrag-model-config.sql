-- Add LightRAG model config + provider so it appears on RAG page in UI
-- --------------------------------------------------------

-- 1. Add LightRAG provider (UI form fields)
INSERT IGNORE INTO `ai_model_provider`
  (`id`, `model_type`, `provider_code`, `name`, `fields`, `sort`, `creator`, `create_date`, `updater`, `update_date`)
VALUES
  ('SYSTEM_RAG_LightRAG', 'RAG', 'lightrag', 'LightRAG (Knowledge Graph)', JSON_ARRAY(
    JSON_OBJECT('key', 'url', 'type', 'string', 'label', 'Qdrant URL', 'default', 'http://localhost:6333'),
    JSON_OBJECT('key', 'collection_name', 'type', 'string', 'label', 'Collection name', 'default', 'xiaozhi_knowledge'),
    JSON_OBJECT('key', 'openai_api_key', 'type', 'password', 'label', 'OpenAI API Key'),
    JSON_OBJECT('key', 'embedding_model', 'type', 'string', 'label', 'Embedding model', 'default', 'text-embedding-3-small'),
    JSON_OBJECT('key', 'vector_size', 'type', 'number', 'label', 'Vector dimensions', 'default', 1536),
    JSON_OBJECT('key', 'llm_model', 'type', 'string', 'label', 'LLM for entity extraction', 'default', 'gpt-4o-mini'),
    JSON_OBJECT('key', 'llm_api_key', 'type', 'password', 'label', 'LLM API Key (empty = use OpenAI key)'),
    JSON_OBJECT(
        'key', 'search_mode',
        'type', 'select',
        'label', 'Search mode',
        'default', 'hybrid',
        'options', JSON_ARRAY(
            JSON_OBJECT('label', 'Hybrid (recommend)', 'value', 'hybrid'),
            JSON_OBJECT('label', 'Local (entity-focused)', 'value', 'local'),
            JSON_OBJECT('label', 'Global (summary)', 'value', 'global'),
            JSON_OBJECT('label', 'Naive (vector only)', 'value', 'naive'),
            JSON_OBJECT('label', 'Mix (all modes)', 'value', 'mix')
        )
    ),
    JSON_OBJECT('key', 'working_dir', 'type', 'string', 'label', 'LightRAG storage dir', 'default', 'data/lightrag_storage'),
    JSON_OBJECT('key', 'top_k', 'type', 'number', 'label', 'Top K results', 'default', 3),
    JSON_OBJECT('key', 'score_threshold', 'type', 'string', 'label', 'Score threshold', 'default', '0.55')
  ), 5, 1, NOW(), 1, NOW());

-- 2. Add LightRAG model config (instance)
INSERT IGNORE INTO `ai_model_config`
  (`id`, `model_type`, `model_code`, `model_name`, `is_default`, `is_enabled`, `config_json`, `doc_link`, `remark`, `sort`, `creator`, `create_date`, `updater`, `update_date`)
VALUES
  ('RAG_LightRAG_OpenAI', 'RAG', 'LightRAG_OpenAI', 'LightRAG + OpenAI (Knowledge Graph)', 0, 1,
   '{"type": "lightrag", "url": "http://localhost:6333", "collection_name": "xiaozhi_knowledge", "openai_api_key": "", "embedding_model": "text-embedding-3-small", "vector_size": 1536, "llm_model": "gpt-4o-mini", "llm_api_key": "", "search_mode": "hybrid", "working_dir": "data/lightrag_storage", "top_k": 3, "score_threshold": "0.55"}',
   'https://github.com/HKUDS/LightRAG', 'Knowledge Graph + Vector hybrid search via LightRAG with OpenAI embedding', 5, NULL, NULL, NULL, NULL);
