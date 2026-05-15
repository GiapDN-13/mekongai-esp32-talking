-- Remove unused/test RAG model configs completely.
-- Keep only: RAG_Qdrant_Gemini_004 (production) and RAG_LightRAG_OpenAI (Knowledge Graph).

-- Delete unused Qdrant models
DELETE FROM ai_model_config
WHERE id IN ('RAG_Qdrant_OpenAI_Small', 'RAG_Qdrant_OpenAI_Large', 'RAG_Qdrant_BGE_M3');

-- Update Gemini model: canonical gemini-embedding-001, align defaults
UPDATE ai_model_config
SET model_name = 'Qdrant + Gemini',
    config_json = JSON_SET(
        config_json,
        '$.embedding_model', 'gemini-embedding-001',
        '$.vector_size', 768,
        '$.top_k', 3,
        '$.score_threshold', 0.5,
        '$.chunk_size', 700,
        '$.chunk_overlap', 60
    ),
    remark = 'Qdrant + Gemini gemini-embedding-001 (768d). Dùng cho RAG Inline và Function Calling.',
    is_default = 1
WHERE id = 'RAG_Qdrant_Gemini_004';

-- Ensure LightRAG is not default
UPDATE ai_model_config
SET is_default = 0
WHERE id = 'RAG_LightRAG_OpenAI';
