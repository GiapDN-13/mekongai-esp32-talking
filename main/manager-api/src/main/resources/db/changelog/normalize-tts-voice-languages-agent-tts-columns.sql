-- Normalize ai_tts_voice.languages to English canonical labels (legacy rows may use Chinese variants; source strings encoded as UTF-8 hex to keep this file ASCII-only).
UPDATE ai_tts_voice
SET languages = CASE
    WHEN languages = CONVERT(UNHEX('e88bb1e8afad') USING utf8mb4) THEN 'English'
    WHEN languages = CONVERT(UNHEX('e699aee9809ae8af9de38081e88bb1e8afad') USING utf8mb4) THEN 'Mandarin, English'
    WHEN languages = CONVERT(UNHEX('e697a5e8afade38081e8a5bfe78fade78999e8afad') USING utf8mb4) THEN 'Japanese, Spanish'
    WHEN languages = CONVERT(UNHEX('e7b2a4e8afade38081e88bb1e8afad') USING utf8mb4) THEN 'Cantonese, English'
    WHEN languages IN (
      CONVERT(UNHEX('e4b8ade69687') USING utf8mb4), CONVERT(UNHEX('e699aee9809ae8af9d') USING utf8mb4), CONVERT(UNHEX('e4b89ce58c97e8af9d') USING utf8mb4),
      CONVERT(UNHEX('e5a4a9e6b4a5e8af9d') USING utf8mb4), CONVERT(UNHEX('e4b8ade696872de58c97e4baace58fa3e99fb3') USING utf8mb4), CONVERT(UNHEX('e4b8ade696872de99d92e5b29be58fa3e99fb3') USING utf8mb4),
      CONVERT(UNHEX('e4b8ade696872de6b2b3e58d97e58fa3e99fb3') USING utf8mb4), CONVERT(UNHEX('e4b8ade696872de5b9bfe8a5bfe58fa3e99fb3') USING utf8mb4), CONVERT(UNHEX('e8bebde5ae81') USING utf8mb4),
      CONVERT(UNHEX('e99995e8a5bf') USING utf8mb4), CONVERT(UNHEX('e4b8ade696872de59b9be5b79de58fa3e99fb3') USING utf8mb4), CONVERT(UNHEX('e4b8ade696872de58fb0e6b9bee58fa3e99fb3') USING utf8mb4),
      CONVERT(UNHEX('e4b8ade696872de995bfe6b299e58fa3e99fb3') USING utf8mb4)
    ) THEN 'Mandarin'
    WHEN languages IN (
      CONVERT(UNHEX('e4b8ade69687e58f8ae4b8ade88bb1e69687e6b7b7e59088') USING utf8mb4), CONVERT(UNHEX('e4b8ade69687e38081e88bb1e69687') USING utf8mb4),
      CONVERT(UNHEX('e4b8ade69687e38081e7be8ee5bc8fe88bb1e8afad') USING utf8mb4), CONVERT(UNHEX('e4b8ade696872de58c97e4baace58fa3e99fb3e38081e88bb1e69687') USING utf8mb4),
      CONVERT(UNHEX('e4b8ade6968728e4b89ce58c9729e58f8ae4b8ade88bb1e69687e6b7b7e59088') USING utf8mb4)
    ) THEN 'Mandarin, English'
    WHEN languages IN (
      CONVERT(UNHEX('e88bb1e5bc8fe88bb1e69687') USING utf8mb4), CONVERT(UNHEX('e88bb1e5bc8fe88bb1e8afad') USING utf8mb4), CONVERT(UNHEX('e7be8ee5bc8fe88bb1e8afad') USING utf8mb4),
      CONVERT(UNHEX('e6beb3e6b4b2e88bb1e8afad') USING utf8mb4), CONVERT(UNHEX('e88bb1e69687') USING utf8mb4)
    ) THEN 'English'
    WHEN languages IN (CONVERT(UNHEX('e697a5e8afad') USING utf8mb4)) THEN 'Japanese'
    WHEN languages IN (
      CONVERT(UNHEX('e697a5e8afade38081e8a5bfe8afad') USING utf8mb4), CONVERT(UNHEX('e697a5e8afade38081e8a5bfe78fade78999e8afad') USING utf8mb4)
    ) THEN 'Japanese, Spanish'
    WHEN languages IN (CONVERT(UNHEX('e99fa9e8afad') USING utf8mb4)) THEN 'Korean'
    WHEN languages IN (
      CONVERT(UNHEX('e7b2a4e8afad') USING utf8mb4), CONVERT(UNHEX('e4b8ade696872de5b9bfe4b89ce58fa3e99fb3') USING utf8mb4)
    ) THEN 'Cantonese'
    WHEN languages IN (CONVERT(UNHEX('e4b8ade6968728e7b2a4e8afad29e58f8ae4b8ade88bb1e69687e6b7b7e59088') USING utf8mb4)) THEN 'Cantonese, English'
    WHEN languages IN (CONVERT(UNHEX('e7b2a4e8afade58f8ae7b2a4e88bb1e6b7b7e59088') USING utf8mb4)) THEN 'Cantonese, English'
    ELSE languages
END;

-- ai_agent: TTS language / volume / rate / pitch
SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'ai_agent' AND COLUMN_NAME = 'tts_language');
SET @sql = IF(@col_exists = 0, 'ALTER TABLE `ai_agent` ADD COLUMN `tts_language` VARCHAR(50) NULL COMMENT ''TTS voice language'' AFTER `tts_voice_id`', 'SELECT ''Column tts_language already exists'' AS msg');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'ai_agent' AND COLUMN_NAME = 'tts_volume');
SET @sql = IF(@col_exists = 0, 'ALTER TABLE `ai_agent` ADD COLUMN `tts_volume` INT NULL COMMENT ''TTS volume'' AFTER `tts_language`', 'SELECT ''Column tts_volume already exists'' AS msg');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'ai_agent' AND COLUMN_NAME = 'tts_rate');
SET @sql = IF(@col_exists = 0, 'ALTER TABLE `ai_agent` ADD COLUMN `tts_rate` INT NULL COMMENT ''TTS speech rate'' AFTER `tts_volume`', 'SELECT ''Column tts_rate already exists'' AS msg');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'ai_agent' AND COLUMN_NAME = 'tts_pitch');
SET @sql = IF(@col_exists = 0, 'ALTER TABLE `ai_agent` ADD COLUMN `tts_pitch` INT NULL COMMENT ''TTS pitch'' AFTER `tts_rate`', 'SELECT ''Column tts_pitch already exists'' AS msg');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- ai_agent_template: same columns
SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'ai_agent_template' AND COLUMN_NAME = 'tts_language');
SET @sql = IF(@col_exists = 0, 'ALTER TABLE `ai_agent_template` ADD COLUMN `tts_language` VARCHAR(50) NULL COMMENT ''TTS voice language'' AFTER `tts_voice_id`', 'SELECT ''Column tts_language already exists'' AS msg');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'ai_agent_template' AND COLUMN_NAME = 'tts_volume');
SET @sql = IF(@col_exists = 0, 'ALTER TABLE `ai_agent_template` ADD COLUMN `tts_volume` INT NULL COMMENT ''TTS volume'' AFTER `tts_language`', 'SELECT ''Column tts_volume already exists'' AS msg');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'ai_agent_template' AND COLUMN_NAME = 'tts_rate');
SET @sql = IF(@col_exists = 0, 'ALTER TABLE `ai_agent_template` ADD COLUMN `tts_rate` INT NULL COMMENT ''TTS speech rate'' AFTER `tts_volume`', 'SELECT ''Column tts_rate already exists'' AS msg');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'ai_agent_template' AND COLUMN_NAME = 'tts_pitch');
SET @sql = IF(@col_exists = 0, 'ALTER TABLE `ai_agent_template` ADD COLUMN `tts_pitch` INT NULL COMMENT ''TTS pitch'' AFTER `tts_rate`', 'SELECT ''Column tts_pitch already exists'' AS msg');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;
