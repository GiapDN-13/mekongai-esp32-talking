-- Add sort column to agent-tag relation
SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'ai_agent_tag_relation' AND COLUMN_NAME = 'sort');
SET @sql = IF(@col_exists = 0, 'ALTER TABLE `ai_agent_tag_relation` ADD COLUMN `sort` INT UNSIGNED DEFAULT 0 COMMENT ''Sort order''', 'SELECT ''Column sort already exists'' AS msg');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Backfill sort = row order where still default 0 (idempotent for customized sorts)
