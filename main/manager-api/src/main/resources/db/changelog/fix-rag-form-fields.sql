-- Clean up RAG Qdrant provider form fields:
-- 1. Rename OpenAI API Key → Gemini API Key (since we use Gemini embedding)
-- 2. Remove OpenAI-specific fields (openai_base_url)
-- 3. Simplify embedding_provider to Gemini-only

UPDATE ai_model_provider
SET fields = JSON_ARRAY(
    JSON_OBJECT('key', 'url',                'type', 'text',     'label', 'Qdrant URL',                                   'default', 'http://localhost:6333'),
    JSON_OBJECT('key', 'collection_name',    'type', 'text',     'label', 'Collection name',                              'default', 'xiaozhi_knowledge'),
    JSON_OBJECT('key', 'embedding_provider', 'type', 'select',   'label', 'Embedding provider',  'default', 'gemini',
        'options', JSON_ARRAY(
            JSON_OBJECT('label', 'Gemini API', 'value', 'gemini'),
            JSON_OBJECT('label', 'OpenAI API', 'value', 'openai')
        )
    ),
    JSON_OBJECT('key', 'embedding_model',    'type', 'text',     'label', 'Embedding model',                              'default', 'gemini-embedding-001'),
    JSON_OBJECT('key', 'vector_size',        'type', 'number',   'label', 'Vector dimensions',                            'default', 768),
    JSON_OBJECT('key', 'gemini_api_key',     'type', 'password', 'label', 'Gemini API Key (trống = lấy từ LLM Gemini)',   'default', ''),
    JSON_OBJECT('key', 'openai_api_key',     'type', 'password', 'label', 'OpenAI API Key (chỉ khi dùng OpenAI embed)',   'default', ''),
    JSON_OBJECT('key', 'top_k',             'type', 'number',   'label', 'Top K kết quả',                                'default', 3),
    JSON_OBJECT('key', 'score_threshold',    'type', 'text',     'label', 'Ngưỡng score (0.0-1.0)',                       'default', '0.5')
)
WHERE id = 'SYSTEM_RAG_Qdrant';
