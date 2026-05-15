-- Move RAG/Embedding credentials to sys_params for UI management
-- These will override config.yaml defaults when configured via UI

-- RAG Embedding provider
INSERT IGNORE INTO sys_params (id, param_code, param_value, value_type, param_type, remark, creator, create_date, updater, update_date)
VALUES (1900000001, 'plugins.search_from_qdrant.embedding_provider', 'local', 'string', 1, 'Embedding provider: local / gemini / openai / bedrock', 1, NOW(), 1, NOW());

INSERT IGNORE INTO sys_params (id, param_code, param_value, value_type, param_type, remark, creator, create_date, updater, update_date)
VALUES (1900000002, 'plugins.search_from_qdrant.embedding_model', 'BAAI/bge-m3', 'string', 1, 'Embedding model name', 1, NOW(), 1, NOW());

INSERT IGNORE INTO sys_params (id, param_code, param_value, value_type, param_type, remark, creator, create_date, updater, update_date)
VALUES (1900000003, 'plugins.search_from_qdrant.vector_size', '1024', 'number', 1, 'Vector dimensions (must match collection)', 1, NOW(), 1, NOW());

INSERT IGNORE INTO sys_params (id, param_code, param_value, value_type, param_type, remark, creator, create_date, updater, update_date)
VALUES (1900000004, 'plugins.search_from_qdrant.collection_name', 'xiaozhi_knowledge_v2', 'string', 1, 'Qdrant collection name', 1, NOW(), 1, NOW());

INSERT IGNORE INTO sys_params (id, param_code, param_value, value_type, param_type, remark, creator, create_date, updater, update_date)
VALUES (1900000005, 'plugins.search_from_qdrant.url', 'http://localhost:6333', 'string', 1, 'Qdrant URL', 1, NOW(), 1, NOW());

-- Bedrock credentials
INSERT IGNORE INTO sys_params (id, param_code, param_value, value_type, param_type, remark, creator, create_date, updater, update_date)
VALUES (1900000006, 'plugins.search_from_qdrant.bedrock_region', 'us-east-1', 'string', 1, 'AWS Bedrock Region', 1, NOW(), 1, NOW());

INSERT IGNORE INTO sys_params (id, param_code, param_value, value_type, param_type, remark, creator, create_date, updater, update_date)
VALUES (1900000007, 'plugins.search_from_qdrant.bedrock_access_key', '', 'string', 1, 'AWS Bedrock Access Key ID', 1, NOW(), 1, NOW());

INSERT IGNORE INTO sys_params (id, param_code, param_value, value_type, param_type, remark, creator, create_date, updater, update_date)
VALUES (1900000008, 'plugins.search_from_qdrant.bedrock_secret_key', '', 'string', 1, 'AWS Bedrock Secret Access Key', 1, NOW(), 1, NOW());

-- Gemini / OpenAI keys
INSERT IGNORE INTO sys_params (id, param_code, param_value, value_type, param_type, remark, creator, create_date, updater, update_date)
VALUES (1900000009, 'plugins.search_from_qdrant.gemini_api_key', '', 'string', 1, 'Gemini API key (for embedding)', 1, NOW(), 1, NOW());

INSERT IGNORE INTO sys_params (id, param_code, param_value, value_type, param_type, remark, creator, create_date, updater, update_date)
VALUES (1900000010, 'plugins.search_from_qdrant.openai_api_key', '', 'string', 1, 'OpenAI API key (for embedding)', 1, NOW(), 1, NOW());

INSERT IGNORE INTO sys_params (id, param_code, param_value, value_type, param_type, remark, creator, create_date, updater, update_date)
VALUES (1900000011, 'plugins.search_from_qdrant.openai_base_url', 'https://api.openai.com/v1', 'string', 1, 'OpenAI base URL', 1, NOW(), 1, NOW());

-- Search parameters
INSERT IGNORE INTO sys_params (id, param_code, param_value, value_type, param_type, remark, creator, create_date, updater, update_date)
VALUES (1900000012, 'plugins.search_from_qdrant.top_k', '3', 'number', 1, 'Top K search results', 1, NOW(), 1, NOW());

INSERT IGNORE INTO sys_params (id, param_code, param_value, value_type, param_type, remark, creator, create_date, updater, update_date)
VALUES (1900000013, 'plugins.search_from_qdrant.score_threshold', '0.3', 'string', 1, 'Score threshold (0.0-1.0)', 1, NOW(), 1, NOW());

INSERT IGNORE INTO sys_params (id, param_code, param_value, value_type, param_type, remark, creator, create_date, updater, update_date)
VALUES (1900000014, 'plugins.search_from_qdrant.chunk_size', '1500', 'number', 1, 'Chunk size (chars)', 1, NOW(), 1, NOW());

INSERT IGNORE INTO sys_params (id, param_code, param_value, value_type, param_type, remark, creator, create_date, updater, update_date)
VALUES (1900000015, 'plugins.search_from_qdrant.chunk_overlap', '150', 'number', 1, 'Chunk overlap (chars)', 1, NOW(), 1, NOW());

-- Memory Bedrock credentials
INSERT IGNORE INTO sys_params (id, param_code, param_value, value_type, param_type, remark, creator, create_date, updater, update_date)
VALUES (1900000020, 'memory.bedrock_region', 'us-east-1', 'string', 1, 'Memory: AWS Bedrock Region', 1, NOW(), 1, NOW());

INSERT IGNORE INTO sys_params (id, param_code, param_value, value_type, param_type, remark, creator, create_date, updater, update_date)
VALUES (1900000021, 'memory.bedrock_access_key', '', 'string', 1, 'Memory: AWS Bedrock Access Key ID', 1, NOW(), 1, NOW());

INSERT IGNORE INTO sys_params (id, param_code, param_value, value_type, param_type, remark, creator, create_date, updater, update_date)
VALUES (1900000022, 'memory.bedrock_secret_key', '', 'string', 1, 'Memory: AWS Bedrock Secret Access Key', 1, NOW(), 1, NOW());
