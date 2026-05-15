-- Model provider registry
DROP TABLE IF EXISTS `ai_model_provider`;
CREATE TABLE `ai_model_provider` (
    `id` VARCHAR(32) NOT NULL COMMENT 'Primary key',
    `model_type` VARCHAR(20) COMMENT 'Model kind (Memory/ASR/VAD/LLM/TTS)',
    `provider_code` VARCHAR(50) COMMENT 'Provider implementation code',
    `name` VARCHAR(50) COMMENT 'Provider display name',
    `fields` JSON COMMENT 'Provider form fields (JSON)',
    `sort` INT UNSIGNED DEFAULT 0 COMMENT 'Sort order',
    `creator` BIGINT COMMENT 'Created by',
    `create_date` DATETIME COMMENT 'Created at',
    `updater` BIGINT COMMENT 'Updated by',
    `update_date` DATETIME COMMENT 'Updated at',
    PRIMARY KEY (`id`),
    INDEX `idx_ai_model_provider_model_type` (`model_type`) COMMENT 'Index on model_type for listing providers'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Model providers';

-- Model configuration rows
DROP TABLE IF EXISTS `ai_model_config`;
CREATE TABLE `ai_model_config` (
    `id` VARCHAR(32) NOT NULL COMMENT 'Primary key',
    `model_type` VARCHAR(20) COMMENT 'Model kind (Memory/ASR/VAD/LLM/TTS)',
    `model_code` VARCHAR(50) COMMENT 'Model code (e.g. AliLLM, DoubaoTTS)',
    `model_name` VARCHAR(50) COMMENT 'Display name',
    `is_default` TINYINT(1) DEFAULT 0 COMMENT 'Default for type: 0 no, 1 yes',
    `is_enabled` TINYINT(1) DEFAULT 0 COMMENT 'Enabled flag',
    `config_json` JSON COMMENT 'Model config JSON',
    `doc_link` VARCHAR(200) COMMENT 'Documentation URL',
    `remark` VARCHAR(255) COMMENT 'Notes',
    `sort` INT UNSIGNED DEFAULT 0 COMMENT 'Sort order',
    `creator` BIGINT COMMENT 'Created by',
    `create_date` DATETIME COMMENT 'Created at',
    `updater` BIGINT COMMENT 'Updated by',
    `update_date` DATETIME COMMENT 'Updated at',
    PRIMARY KEY (`id`),
    INDEX `idx_ai_model_config_model_type` (`model_type`) COMMENT 'Index on model_type for listing configs'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Model configurations';

-- TTS voice catalog
DROP TABLE IF EXISTS `ai_tts_voice`;
CREATE TABLE `ai_tts_voice` (
    `id` VARCHAR(32) NOT NULL COMMENT 'Primary key',
    `tts_model_id` VARCHAR(32) COMMENT 'Parent TTS model id',
    `name` VARCHAR(20) COMMENT 'Voice display name',
    `tts_voice` VARCHAR(50) COMMENT 'Provider voice id',
    `languages` VARCHAR(50) COMMENT 'Language tag',
    `voice_demo` VARCHAR(500) DEFAULT NULL COMMENT 'Demo URL or asset',
    `remark` VARCHAR(255) COMMENT 'Notes',
    `sort` INT UNSIGNED DEFAULT 0 COMMENT 'Sort order',
    `creator` BIGINT COMMENT 'Created by',
    `create_date` DATETIME COMMENT 'Created at',
    `updater` BIGINT COMMENT 'Updated by',
    `update_date` DATETIME COMMENT 'Updated at',
    PRIMARY KEY (`id`),
    INDEX `idx_ai_tts_voice_tts_model_id` (`tts_model_id`) COMMENT 'Index on TTS model for voice lookup'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='TTS voices';

-- Agent templates
DROP TABLE IF EXISTS `ai_agent_template`;
CREATE TABLE `ai_agent_template` (
    `id` VARCHAR(32) NOT NULL COMMENT 'Agent id',
    `agent_code` VARCHAR(36) COMMENT 'Agent code',
    `agent_name` VARCHAR(64) COMMENT 'Agent name',
    `asr_model_id` VARCHAR(32) COMMENT 'ASR model id',
    `vad_model_id` VARCHAR(64) COMMENT 'VAD model id',
    `llm_model_id` VARCHAR(32) COMMENT 'LLM model id',
    `vllm_model_id` VARCHAR(32) DEFAULT NULL COMMENT 'Vision LLM model id',
    `tts_model_id` VARCHAR(32) COMMENT 'TTS model id',
    `tts_voice_id` VARCHAR(32) COMMENT 'TTS voice id',
    `tts_language` VARCHAR(32) DEFAULT NULL COMMENT 'TTS voice language',
    `tts_volume` INT DEFAULT NULL COMMENT 'TTS volume',
    `tts_rate` INT DEFAULT NULL COMMENT 'TTS speech rate',
    `tts_pitch` INT DEFAULT NULL COMMENT 'TTS pitch',
    `mem_model_id` VARCHAR(32) COMMENT 'Memory model id',
    `intent_model_id` VARCHAR(32) COMMENT 'Intent model id',
    `chat_history_conf` TINYINT UNSIGNED DEFAULT 0 COMMENT 'Chat history: 0 off, 1 text, 2 text+audio',
    `system_prompt` TEXT COMMENT 'System / role prompt',
    `summary_memory` TEXT COMMENT 'Summary memory prompt',
    `lang_code` VARCHAR(10) COMMENT 'Language code',
    `language` VARCHAR(10) COMMENT 'Interaction language',
    `sort` INT UNSIGNED DEFAULT 0 COMMENT 'Sort weight',
    `creator` BIGINT COMMENT 'Created by user id',
    `created_at` DATETIME COMMENT 'Created at',
    `updater` BIGINT COMMENT 'Updated by user id',
    `updated_at` DATETIME COMMENT 'Updated at',
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Agent templates';

-- Agent instances
DROP TABLE IF EXISTS `ai_agent`;
CREATE TABLE `ai_agent` (
    `id` VARCHAR(32) NOT NULL COMMENT 'Agent id',
    `user_id` BIGINT COMMENT 'Owner user id',
    `agent_code` VARCHAR(36) COMMENT 'Agent code',
    `agent_name` VARCHAR(64) COMMENT 'Agent name',
    `asr_model_id` VARCHAR(32) COMMENT 'ASR model id',
    `vad_model_id` VARCHAR(64) COMMENT 'VAD model id',
    `llm_model_id` VARCHAR(32) COMMENT 'LLM model id',
    `vllm_model_id` VARCHAR(32) DEFAULT NULL COMMENT 'Vision LLM model id',
    `tts_model_id` VARCHAR(32) COMMENT 'TTS model id',
    `tts_voice_id` VARCHAR(32) COMMENT 'TTS voice id',
    `tts_language` VARCHAR(32) DEFAULT NULL COMMENT 'TTS voice language',
    `tts_volume` INT DEFAULT NULL COMMENT 'TTS volume',
    `tts_rate` INT DEFAULT NULL COMMENT 'TTS speech rate',
    `tts_pitch` INT DEFAULT NULL COMMENT 'TTS pitch',
    `mem_model_id` VARCHAR(32) COMMENT 'Memory model id',
    `intent_model_id` VARCHAR(32) COMMENT 'Intent model id',
    `chat_history_conf` TINYINT UNSIGNED DEFAULT 0 COMMENT 'Chat history: 0 off, 1 text, 2 text+audio',
    `system_prompt` TEXT COMMENT 'System / role prompt',
    `summary_memory` TEXT COMMENT 'Summary memory prompt',
    `lang_code` VARCHAR(10) COMMENT 'Language code',
    `language` VARCHAR(10) COMMENT 'Interaction language',
    `sort` INT UNSIGNED DEFAULT 0 COMMENT 'Sort weight',
    `creator` BIGINT COMMENT 'Created by user id',
    `created_at` DATETIME COMMENT 'Created at',
    `updater` BIGINT COMMENT 'Updated by user id',
    `updated_at` DATETIME COMMENT 'Updated at',
    PRIMARY KEY (`id`),
    INDEX `idx_ai_agent_user_id` (`user_id`) COMMENT 'Index on owner for listing agents'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Agents';

-- Devices
DROP TABLE IF EXISTS `ai_device`;
CREATE TABLE `ai_device` (
    `id` VARCHAR(32) NOT NULL COMMENT 'Device id',
    `user_id` BIGINT COMMENT 'Owner user id',
    `mac_address` VARCHAR(50) COMMENT 'MAC address',
    `last_connected_at` DATETIME COMMENT 'Last connected at',
    `auto_update` TINYINT UNSIGNED DEFAULT 0 COMMENT 'Auto update: 0 off, 1 on',
    `board` VARCHAR(50) COMMENT 'Board / hardware model',
    `alias` VARCHAR(64) DEFAULT NULL COMMENT 'Friendly name',
    `agent_id` VARCHAR(32) COMMENT 'Bound agent id',
    `app_version` VARCHAR(20) COMMENT 'Firmware version',
    `sort` INT UNSIGNED DEFAULT 0 COMMENT 'Sort order',
    `creator` BIGINT COMMENT 'Created by',
    `create_date` DATETIME COMMENT 'Created at',
    `updater` BIGINT COMMENT 'Updated by',
    `update_date` DATETIME COMMENT 'Updated at',
    PRIMARY KEY (`id`),
    INDEX `idx_ai_device_created_at` (`mac_address`) COMMENT 'Index on MAC for device lookup'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Devices';

-- Voiceprints (legacy table; may be dropped in later migrations)
DROP TABLE IF EXISTS `ai_voiceprint`;
CREATE TABLE `ai_voiceprint` (
    `id` VARCHAR(32) NOT NULL COMMENT 'Voiceprint id',
    `name` VARCHAR(64) COMMENT 'Name',
    `user_id` BIGINT COMMENT 'User id',
    `agent_id` VARCHAR(32) COMMENT 'Agent id',
    `agent_code` VARCHAR(36) COMMENT 'Agent code',
    `agent_name` VARCHAR(36) COMMENT 'Agent name',
    `description` VARCHAR(255) COMMENT 'Description',
    `embedding` LONGTEXT COMMENT 'Embedding JSON',
    `memory` TEXT COMMENT 'Linked memory text',
    `sort` INT UNSIGNED DEFAULT 0 COMMENT 'Sort weight',
    `creator` BIGINT COMMENT 'Created by user id',
    `created_at` DATETIME COMMENT 'Created at',
    `updater` BIGINT COMMENT 'Updated by user id',
    `updated_at` DATETIME COMMENT 'Updated at',
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Voiceprints';

-- Chat sessions (legacy; superseded by agent chat history in later migrations)
DROP TABLE IF EXISTS `ai_chat_history`;
CREATE TABLE `ai_chat_history` (
    `id` VARCHAR(32) NOT NULL COMMENT 'Chat id',
    `user_id` BIGINT COMMENT 'User id',
    `agent_id` VARCHAR(32) DEFAULT NULL COMMENT 'Agent id',
    `device_id` VARCHAR(32) DEFAULT NULL COMMENT 'Device id',
    `message_count` INT COMMENT 'Message count summary',
    `creator` BIGINT COMMENT 'Created by',
    `create_date` DATETIME COMMENT 'Created at',
    `updater` BIGINT COMMENT 'Updated by',
    `update_date` DATETIME COMMENT 'Updated at',
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Chat sessions';

-- Chat messages
DROP TABLE IF EXISTS `ai_chat_message`;
CREATE TABLE `ai_chat_message` (
    `id` VARCHAR(32) NOT NULL COMMENT 'Message id',
    `user_id` BIGINT COMMENT 'User id',
    `chat_id` VARCHAR(64) COMMENT 'Chat session id',
    `role` ENUM('user', 'assistant') COMMENT 'Speaker role',
    `content` TEXT COMMENT 'Message body',
    `prompt_tokens` INT UNSIGNED DEFAULT 0 COMMENT 'Prompt tokens',
    `total_tokens` INT UNSIGNED DEFAULT 0 COMMENT 'Total tokens',
    `completion_tokens` INT UNSIGNED DEFAULT 0 COMMENT 'Completion tokens',
    `prompt_ms` INT UNSIGNED DEFAULT 0 COMMENT 'Prompt latency ms',
    `total_ms` INT UNSIGNED DEFAULT 0 COMMENT 'Total latency ms',
    `completion_ms` INT UNSIGNED DEFAULT 0 COMMENT 'Completion latency ms',
    `creator` BIGINT COMMENT 'Created by',
    `create_date` DATETIME COMMENT 'Created at',
    `updater` BIGINT COMMENT 'Updated by',
    `update_date` DATETIME COMMENT 'Updated at',
    PRIMARY KEY (`id`),
    INDEX `idx_ai_chat_message_user_id_chat_id_role` (`user_id`, `chat_id`) COMMENT 'User and chat composite index',
    INDEX `idx_ai_chat_message_created_at` (`create_date`) COMMENT 'Created-at index for time queries'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Chat messages';
