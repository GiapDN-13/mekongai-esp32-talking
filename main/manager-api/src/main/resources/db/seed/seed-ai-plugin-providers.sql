-- ===============================
-- I. Insert plugin rows into ai_model_provider
-- ===============================
START TRANSACTION;


-- intent_llm and function_call: no function list on provider
update `ai_model_provider` set fields =  '[{"key":"llm","label":"LLM model","type":"string"}]' where  id = 'SYSTEM_Intent_intent_llm';
update `ai_model_provider` set fields =  '[]' where  id = 'SYSTEM_Intent_function_call';
update `ai_model_config` set config_json =  '{\"type\": \"intent_llm\", \"llm\": \"LLM_GeminiLLM\"}' where  id = 'Intent_intent_llm';
UPDATE `ai_model_config` SET config_json = '{\"type\": \"function_call\"}' WHERE id = 'Intent_function_call';


delete from ai_model_provider where model_type = 'Plugin';
-- 1. Weather
INSERT INTO ai_model_provider (id, model_type, provider_code, name, fields,
                               sort, creator, create_date, updater, update_date)
VALUES ('SYSTEM_PLUGIN_WEATHER',
        'Plugin',
        'get_weather',
        'Weather lookup',
        JSON_ARRAY(
                JSON_OBJECT(
                        'key', 'api_key',
                        'type', 'string',
                        'label', 'Weather plugin API key',
                        'default', (SELECT param_value FROM sys_params WHERE param_code = 'plugins.get_weather.api_key')
                ),
                JSON_OBJECT(
                        'key', 'default_location',
                        'type', 'string',
                        'label', 'Default city',
                        'default',
                        (SELECT param_value FROM sys_params WHERE param_code = 'plugins.get_weather.default_location')
                ),
                JSON_OBJECT(
                        'key', 'api_host',
                        'type', 'string',
                        'label', 'Developer API host',
                        'default',
                        (SELECT param_value FROM sys_params WHERE param_code = 'plugins.get_weather.api_host')
                )
        ),
        10, 0, NOW(), 0, NOW());

-- Server-side music playback
INSERT INTO ai_model_provider (id, model_type, provider_code, name, fields,
                               sort, creator, create_date, updater, update_date)
VALUES ('SYSTEM_PLUGIN_MUSIC',
        'Plugin',
        'play_music',
        'Server music playback',
        JSON_ARRAY(),
        20, 0, NOW(), 0, NOW());

-- China News RSS
INSERT INTO ai_model_provider (id, model_type, provider_code, name, fields,
                               sort, creator, create_date, updater, update_date)
VALUES ('SYSTEM_PLUGIN_NEWS_CHINANEWS',
        'Plugin',
        'get_news_from_chinanews',
        'China News (RSS)',
        JSON_ARRAY(
                JSON_OBJECT(
                        'key', 'default_rss_url',
                        'type', 'string',
                        'label', 'Default RSS URL',
                        'default',
                        (SELECT param_value FROM sys_params WHERE param_code = 'plugins.get_news.default_rss_url')
                ),
                JSON_OBJECT(
                        'key', 'society_rss_url',
                        'type', 'string',
                        'label', 'Society news RSS URL',
                        'default',
                        'https://www.chinanews.com.cn/rss/society.xml'
                ),
                JSON_OBJECT(
                        'key', 'world_rss_url',
                        'type', 'string',
                        'label', 'World news RSS URL',
                        'default',
                        'https://www.chinanews.com.cn/rss/world.xml'
                ),
                JSON_OBJECT(
                        'key', 'finance_rss_url',
                        'type', 'string',
                        'label', 'Finance news RSS URL',
                        'default',
                        'https://www.chinanews.com.cn/rss/finance.xml'
                )
        ),
        30, 0, NOW(), 0, NOW());

-- NewsNow aggregate
INSERT INTO ai_model_provider (id, model_type, provider_code, name, fields,
                               sort, creator, create_date, updater, update_date)
VALUES ('SYSTEM_PLUGIN_NEWS_NEWSNOW',
        'Plugin',
        'get_news_from_newsnow',
        'NewsNow aggregate',
        JSON_ARRAY(
                JSON_OBJECT(
                        'key', 'url',
                        'type', 'string',
                        'label', 'API base URL',
                        'default',
                        'https://newsnow.busiyi.world/api/s?id='
                )
        ),
        40, 0, NOW(), 0, NOW());


-- Home Assistant: read state
INSERT INTO ai_model_provider (id, model_type, provider_code, name, fields,
                               sort, creator, create_date, updater, update_date)
VALUES ('SYSTEM_PLUGIN_HA_GET_STATE',
        'Plugin',
        'hass_get_state',
        'Home Assistant device state',
        JSON_ARRAY(
                JSON_OBJECT(
                        'key', 'base_url',
                        'type', 'string',
                        'label', 'Home Assistant base URL',
                        'default',
                        (SELECT param_value FROM sys_params WHERE param_code = 'plugins.home_assistant.base_url')
                ),
                JSON_OBJECT(
                        'key', 'api_key',
                        'type', 'string',
                        'label', 'HA long-lived access token',
                        'default',
                        (SELECT param_value FROM sys_params WHERE param_code = 'plugins.home_assistant.api_key')
                ),
                JSON_OBJECT(
                        'key', 'devices',
                        'type', 'array',
                        'label', 'Device list (name,entity_id;...)',
                        'default',
                        (SELECT param_value FROM sys_params WHERE param_code = 'plugins.home_assistant.devices')
                )
        ),
        50, 0, NOW(), 0, NOW());

-- Home Assistant: write state
INSERT INTO ai_model_provider (id, model_type, provider_code, name, fields,
                               sort, creator, create_date, updater, update_date)
VALUES ('SYSTEM_PLUGIN_HA_SET_STATE',
        'Plugin',
        'hass_set_state',
        'Home Assistant set state',
        JSON_ARRAY(),
        60, 0, NOW(), 0, NOW());

-- Home Assistant: play music
INSERT INTO ai_model_provider (id, model_type, provider_code, name, fields,
                               sort, creator, create_date, updater, update_date)
VALUES ('SYSTEM_PLUGIN_HA_PLAY_MUSIC',
        'Plugin',
        'hass_play_music',
        'Home Assistant music playback',
        JSON_ARRAY(),
        70, 0, NOW(), 0, NOW());


-- ===============================
-- II. Remove legacy plugins.* sys_params
-- ===============================
DELETE
FROM sys_params
WHERE param_code LIKE 'plugins.%';


-- ===============================
-- III. Agent-plugin mapping table
-- ===============================
CREATE TABLE IF NOT EXISTS ai_agent_plugin_mapping
(
    id         BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT 'Primary key',
    agent_id   VARCHAR(32) NOT NULL COMMENT 'Agent id',
    plugin_id  VARCHAR(32) NOT NULL COMMENT 'Plugin id',
    param_info JSON        NOT NULL COMMENT 'Parameter payload',
    UNIQUE KEY uk_agent_provider (agent_id, plugin_id)
) COMMENT 'Maps agents to plugins';


COMMIT;
