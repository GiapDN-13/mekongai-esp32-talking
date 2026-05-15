-- Add OpenAI as LLM provider and default OpenAI model config
-- Provider: openai (OpenAI-compatible API)
INSERT INTO `ai_model_provider` (`id`, `model_type`, `provider_code`, `name`, `fields`, `sort`, `creator`, `create_date`, `updater`, `update_date`)
VALUES (
    'SYSTEM_LLM_openai',
    'LLM',
    'openai',
    'OpenAI',
    '[{"key":"api_key","label":"API key","type":"password"},{"key":"base_url","label":"Base URL","type":"string"},{"key":"model_name","label":"Model name","type":"string"},{"key":"temperature","label":"Temperature","type":"string"},{"key":"max_tokens","label":"Max tokens","type":"string"},{"key":"top_p","label":"Top P","type":"string"},{"key":"frequency_penalty","label":"Frequency penalty","type":"string"}]',
    2, 1, NOW(), 1, NOW()
) ON DUPLICATE KEY UPDATE `name` = VALUES(`name`), `fields` = VALUES(`fields`), `update_date` = NOW();

-- Model config: OpenAI GPT-4o-mini (enabled, not default)
INSERT INTO `ai_model_config` (`id`, `model_type`, `model_code`, `model_name`, `is_default`, `is_enabled`, `config_json`, `doc_link`, `remark`, `sort`)
VALUES (
    'LLM_OpenAILLM',
    'LLM',
    'OpenAILLM',
    'OpenAI',
    0,
    1,
    '{"type": "openai", "model_name": "gpt-4o-mini", "base_url": "https://api.openai.com/v1", "api_key": "your_api_key"}',
    'https://platform.openai.com/docs/api-reference',
    'OpenAI GPT models via official API.\n1. Get API key at https://platform.openai.com/api-keys\n2. Supports: gpt-4o, gpt-4o-mini, gpt-4-turbo, gpt-3.5-turbo\n3. Supports function calling for intent recognition',
    2
) ON DUPLICATE KEY UPDATE `model_name` = VALUES(`model_name`), `config_json` = VALUES(`config_json`), `remark` = VALUES(`remark`);
