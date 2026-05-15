-- Widen display name for translated / longer voice labels
ALTER TABLE `ai_tts_voice` MODIFY COLUMN `name` VARCHAR(128) NULL COMMENT 'Voice display name';
