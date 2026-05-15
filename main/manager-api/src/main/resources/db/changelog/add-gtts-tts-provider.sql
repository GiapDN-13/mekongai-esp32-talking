-- Add gTTS (Google Text-to-Speech) provider and model config

-- 1. Provider definition
DELETE FROM ai_model_provider WHERE id = 'SYSTEM_TTS_gtts';
INSERT INTO ai_model_provider (
    id, model_type, provider_code, name, fields, sort,
    creator, create_date, updater, update_date
) VALUES (
    'SYSTEM_TTS_gtts', 'TTS', 'gtts', 'Google TTS (gTTS)',
    JSON_ARRAY(
        JSON_OBJECT(
            'key', 'language',
            'type', 'select',
            'label', 'Language',
            'required', true,
            'default', 'vi',
            'options', JSON_ARRAY(
                JSON_OBJECT('label', 'Tiếng Việt', 'value', 'vi'),
                JSON_OBJECT('label', 'English', 'value', 'en'),
                JSON_OBJECT('label', '中文', 'value', 'zh-CN'),
                JSON_OBJECT('label', '日本語', 'value', 'ja'),
                JSON_OBJECT('label', '한국어', 'value', 'ko')
            )
        ),
        JSON_OBJECT(
            'key', 'tld',
            'type', 'select',
            'label', 'TLD (accent region)',
            'required', false,
            'default', 'com.vn',
            'options', JSON_ARRAY(
                JSON_OBJECT('label', 'Vietnam (.com.vn)', 'value', 'com.vn'),
                JSON_OBJECT('label', 'US (.com)', 'value', 'com'),
                JSON_OBJECT('label', 'UK (.co.uk)', 'value', 'co.uk'),
                JSON_OBJECT('label', 'Australia (.com.au)', 'value', 'com.au'),
                JSON_OBJECT('label', 'India (.co.in)', 'value', 'co.in')
            )
        ),
        JSON_OBJECT(
            'key', 'slow',
            'type', 'select',
            'label', 'Slow speech',
            'required', false,
            'default', 'false',
            'options', JSON_ARRAY(
                JSON_OBJECT('label', 'Normal speed', 'value', 'false'),
                JSON_OBJECT('label', 'Slow speed', 'value', 'true')
            )
        ),
        JSON_OBJECT('key', 'output_dir', 'type', 'string', 'label', 'Output directory', 'default', 'tmp/')
    ),
    3,
    1, NOW(), 1, NOW()
);

-- 2. Model config: gTTS Vietnamese
DELETE FROM ai_model_config WHERE id = 'TTS_gTTS';
INSERT INTO ai_model_config (
    id, model_type, model_code, model_name,
    is_default, is_enabled,
    config_json,
    doc_link, remark, sort,
    creator, create_date, updater, update_date
) VALUES (
    'TTS_gTTS', 'TTS', 'gtts', 'Google TTS (gTTS)',
    0, 1,
    '{"type":"gtts","language":"vi","tld":"com.vn","slow":false,"output_dir":"tmp/"}',
    'https://gtts.readthedocs.io/',
    'Google TTS miễn phí, không cần API key. Chất lượng cơ bản, hỗ trợ nhiều ngôn ngữ.',
    4,
    1, NOW(), 1, NOW()
);
