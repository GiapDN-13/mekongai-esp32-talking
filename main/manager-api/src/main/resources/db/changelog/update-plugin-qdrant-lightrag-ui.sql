-- Update Plugin provider form: add LightRAG fields for UI configuration
-- Allows switching between "qdrant" (vector-only) and "lightrag" (GraphRAG) on UI

UPDATE ai_model_provider
SET fields = JSON_ARRAY(
    JSON_OBJECT('key', 'description', 'type', 'string', 'label', 'Plugin description (for LLM)', 'default', 'Tìm kiếm thông tin trong knowledge base về cổ vật, lịch sử Việt Nam, hiện vật bảo tàng'),
    JSON_OBJECT(
        'key', 'rag_provider',
        'type', 'select',
        'label', 'RAG Provider',
        'default', 'lightrag',
        'options', JSON_ARRAY(
            JSON_OBJECT('label', 'LightRAG (Knowledge Graph)', 'value', 'lightrag'),
            JSON_OBJECT('label', 'Qdrant (Vector only)', 'value', 'qdrant')
        )
    ),
    JSON_OBJECT('key', 'url', 'type', 'string', 'label', 'Qdrant URL', 'default', 'http://localhost:6333'),
    JSON_OBJECT('key', 'collection_name', 'type', 'string', 'label', 'Collection name', 'default', 'xiaozhi_knowledge'),
    JSON_OBJECT(
        'key', 'embedding_provider',
        'type', 'select',
        'label', 'Embedding Provider',
        'default', 'openai',
        'options', JSON_ARRAY(
            JSON_OBJECT('label', 'OpenAI', 'value', 'openai'),
            JSON_OBJECT('label', 'Gemini', 'value', 'gemini')
        )
    ),
    JSON_OBJECT('key', 'embedding_model', 'type', 'string', 'label', 'Embedding model', 'default', 'text-embedding-3-small'),
    JSON_OBJECT('key', 'vector_size', 'type', 'number', 'label', 'Vector dimensions', 'default', 1536),
    JSON_OBJECT('key', 'openai_api_key', 'type', 'password', 'label', 'OpenAI API Key (embedding + LightRAG)', 'default', ''),
    JSON_OBJECT('key', 'gemini_api_key', 'type', 'password', 'label', 'Gemini API key (if Gemini embedding)', 'default', ''),
    JSON_OBJECT('key', 'llm_model', 'type', 'string', 'label', 'LLM for entity extraction (LightRAG)', 'default', 'gpt-4o-mini'),
    JSON_OBJECT('key', 'llm_api_key', 'type', 'password', 'label', 'LLM API Key (LightRAG, empty=use OpenAI key)', 'default', ''),
    JSON_OBJECT(
        'key', 'search_mode',
        'type', 'select',
        'label', 'Search mode (LightRAG)',
        'default', 'hybrid',
        'options', JSON_ARRAY(
            JSON_OBJECT('label', 'Hybrid (recommend)', 'value', 'hybrid'),
            JSON_OBJECT('label', 'Local (entity-focused)', 'value', 'local'),
            JSON_OBJECT('label', 'Global (summary)', 'value', 'global'),
            JSON_OBJECT('label', 'Naive (vector only)', 'value', 'naive'),
            JSON_OBJECT('label', 'Mix (all modes)', 'value', 'mix')
        )
    ),
    JSON_OBJECT('key', 'top_k', 'type', 'number', 'label', 'Top K results', 'default', 3),
    JSON_OBJECT('key', 'score_threshold', 'type', 'string', 'label', 'Score threshold', 'default', '0.55')
)
WHERE id = 'SYSTEM_PLUGIN_QDRANT_SEARCH';
