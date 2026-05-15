-- Force-delete unused RAG model configs that were only disabled in previous migration.
DELETE FROM ai_model_config
WHERE id IN ('RAG_Qdrant_OpenAI_Small', 'RAG_Qdrant_OpenAI_Large', 'RAG_Qdrant_BGE_M3');
