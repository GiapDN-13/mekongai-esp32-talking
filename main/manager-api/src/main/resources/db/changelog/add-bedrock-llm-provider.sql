-- Add AWS Bedrock LLM provider and model config

-- 1. Provider definition
DELETE FROM ai_model_provider WHERE id = 'SYSTEM_LLM_bedrock';
INSERT INTO ai_model_provider (
    id, model_type, provider_code, name, fields, sort,
    creator, create_date, updater, update_date
) VALUES (
    'SYSTEM_LLM_bedrock', 'LLM', 'bedrock', 'AWS Bedrock',
    JSON_ARRAY(
        JSON_OBJECT('key', 'model_id', 'type', 'select', 'label', 'Model',
            'required', true, 'default', 'us.anthropic.claude-opus-4-6-v1',
            'options', JSON_ARRAY(
                JSON_OBJECT('label', 'Claude Opus 4', 'value', 'us.anthropic.claude-opus-4-6-v1'),
                JSON_OBJECT('label', 'Claude 3.5 Sonnet v2', 'value', 'anthropic.claude-3-5-sonnet-20241022-v2:0'),
                JSON_OBJECT('label', 'Claude 3.5 Haiku', 'value', 'anthropic.claude-3-5-haiku-20241022-v1:0'),
                JSON_OBJECT('label', 'Claude 3 Haiku', 'value', 'anthropic.claude-3-haiku-20240307-v1:0'),
                JSON_OBJECT('label', 'Claude 3 Sonnet', 'value', 'anthropic.claude-3-sonnet-20240229-v1:0'),
                JSON_OBJECT('label', 'Nova Pro', 'value', 'amazon.nova-pro-v1:0'),
                JSON_OBJECT('label', 'Nova Lite', 'value', 'amazon.nova-lite-v1:0'),
                JSON_OBJECT('label', 'Nova Micro', 'value', 'amazon.nova-micro-v1:0')
            )
        ),
        JSON_OBJECT('key', 'region', 'type', 'text', 'label', 'AWS Region', 'required', true, 'default', 'us-east-1'),
        JSON_OBJECT('key', 'aws_access_key_id', 'type', 'password', 'label', 'AWS Access Key ID', 'required', true, 'default', ''),
        JSON_OBJECT('key', 'aws_secret_access_key', 'type', 'password', 'label', 'AWS Secret Access Key', 'required', true, 'default', ''),
        JSON_OBJECT('key', 'max_tokens', 'type', 'string', 'label', 'Max tokens', 'required', false, 'default', '600'),
        JSON_OBJECT('key', 'temperature', 'type', 'string', 'label', 'Temperature', 'required', false, 'default', '0.3')
    ),
    2,
    1, NOW(), 1, NOW()
);

-- 2. Model config: Claude Opus 4 (strongest)
DELETE FROM ai_model_config WHERE id = 'LLM_BedrockClaudeOpus4';
INSERT INTO ai_model_config (
    id, model_type, model_code, model_name,
    is_default, is_enabled,
    config_json,
    doc_link, remark, sort,
    creator, create_date, updater, update_date
) VALUES (
    'LLM_BedrockClaudeOpus4', 'LLM', 'bedrock', 'Bedrock Claude Opus 4',
    0, 1,
    '{"type":"bedrock","model_id":"us.anthropic.claude-opus-4-6-v1","region":"us-east-1","aws_access_key_id":"","aws_secret_access_key":"","max_tokens":"600","temperature":"0.3"}',
    'https://docs.aws.amazon.com/bedrock/latest/userguide/models-supported.html',
    'AWS Bedrock Claude Opus 4 - Model manh nhat cua Anthropic, ho tro tieng Viet tot.',
    2,
    1, NOW(), 1, NOW()
);

-- 3. Model config: Claude 3.5 Sonnet
DELETE FROM ai_model_config WHERE id = 'LLM_BedrockClaude35Sonnet';
INSERT INTO ai_model_config (
    id, model_type, model_code, model_name,
    is_default, is_enabled,
    config_json,
    doc_link, remark, sort,
    creator, create_date, updater, update_date
) VALUES (
    'LLM_BedrockClaude35Sonnet', 'LLM', 'bedrock', 'Bedrock Claude 3.5 Sonnet',
    0, 1,
    '{"type":"bedrock","model_id":"anthropic.claude-3-5-sonnet-20241022-v2:0","region":"us-east-1","aws_access_key_id":"","aws_secret_access_key":"","max_tokens":"600","temperature":"0.3"}',
    'https://docs.aws.amazon.com/bedrock/latest/userguide/models-supported.html',
    'AWS Bedrock Claude 3.5 Sonnet v2. Chất lượng cao, hỗ trợ tiếng Việt tốt. Cần AWS credentials.',
    3,
    1, NOW(), 1, NOW()
);

-- 3. Model config: Claude 3.5 Haiku (fast, cheaper)
DELETE FROM ai_model_config WHERE id = 'LLM_BedrockClaude35Haiku';
INSERT INTO ai_model_config (
    id, model_type, model_code, model_name,
    is_default, is_enabled,
    config_json,
    doc_link, remark, sort,
    creator, create_date, updater, update_date
) VALUES (
    'LLM_BedrockClaude35Haiku', 'LLM', 'bedrock', 'Bedrock Claude 3.5 Haiku',
    0, 1,
    '{"type":"bedrock","model_id":"anthropic.claude-3-5-haiku-20241022-v1:0","region":"us-east-1","aws_access_key_id":"","aws_secret_access_key":"","max_tokens":"600","temperature":"0.3"}',
    'https://docs.aws.amazon.com/bedrock/latest/userguide/models-supported.html',
    'AWS Bedrock Claude 3.5 Haiku. Nhanh, rẻ hơn Sonnet, phù hợp chatbot realtime.',
    4,
    1, NOW(), 1, NOW()
);

-- 4. Model config: Amazon Nova Lite (cheapest)
DELETE FROM ai_model_config WHERE id = 'LLM_BedrockNovaLite';
INSERT INTO ai_model_config (
    id, model_type, model_code, model_name,
    is_default, is_enabled,
    config_json,
    doc_link, remark, sort,
    creator, create_date, updater, update_date
) VALUES (
    'LLM_BedrockNovaLite', 'LLM', 'bedrock', 'Bedrock Nova Lite',
    0, 1,
    '{"type":"bedrock","model_id":"amazon.nova-lite-v1:0","region":"us-east-1","aws_access_key_id":"","aws_secret_access_key":"","max_tokens":"600","temperature":"0.3"}',
    'https://docs.aws.amazon.com/bedrock/latest/userguide/models-supported.html',
    'Amazon Nova Lite. Rẻ nhất, nhanh nhất trên Bedrock. Phù hợp các tác vụ đơn giản.',
    5,
    1, NOW(), 1, NOW()
);
