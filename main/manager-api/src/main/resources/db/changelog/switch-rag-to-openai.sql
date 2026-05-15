-- Switch RAG model from Gemini to OpenAI embedding
UPDATE ai_model_config
SET model_name = 'Qdrant + OpenAI',
    config_json = JSON_SET(
        config_json,
        '$.embedding_provider', 'openai',
        '$.embedding_model', 'text-embedding-3-small',
        '$.vector_size', 1536,
        '$.score_threshold', 0.3,
        '$.top_k', 3
    ),
    remark = 'Qdrant + OpenAI text-embedding-3-small (1536d).'
WHERE id = 'RAG_Qdrant_Gemini_004';
