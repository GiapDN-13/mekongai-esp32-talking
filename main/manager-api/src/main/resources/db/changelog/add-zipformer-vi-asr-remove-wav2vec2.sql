-- Add ZipformerViASR provider + config; remove Wav2Vec2Vi
-- --------------------------------------------------------

-- 1. Add provider (IGNORE in case partial run from previous attempt)
INSERT IGNORE INTO `ai_model_provider` (`id`, `model_type`, `provider_code`, `name`, `fields`, `sort`, `creator`, `create_date`, `updater`, `update_date`) VALUES
('SYSTEM_ASR_ZipformerVi', 'ASR', 'zipformer_vi', 'Zipformer Vietnamese (6000h)', '[{"key":"model_dir","label":"Model directory","type":"string"},{"key":"output_dir","label":"Output directory","type":"string"},{"key":"num_threads","label":"Inference threads","type":"number"}]', 4, 1, NOW(), 1, NOW());

-- 2. Add model config
INSERT IGNORE INTO `ai_model_config` (`id`, `model_type`, `model_code`, `model_name`, `is_default`, `is_enabled`, `config_json`, `doc_link`, `remark`, `sort`, `creator`, `create_date`, `updater`, `update_date`) VALUES
('ASR_ZipformerVi', 'ASR', 'ZipformerViASR', 'Zipformer Vietnamese (6000h)', 0, 1, '{"type": "zipformer_vi", "model_dir": "models/Zipformer-30M-RNNT-6000h", "output_dir": "tmp/"}', 'https://huggingface.co/hynt/Zipformer-30M-RNNT-6000h', 'Zipformer-30M-RNNT Vietnamese ASR: 30M params, fast on CPU, Vietnamese only', 4, 1, NOW(), 1, NOW());

-- 3. Migrate any agents using Wav2Vec2Vi to ZipformerVi
UPDATE `ai_agent` SET `asr_model_id` = 'ASR_ZipformerVi' WHERE `asr_model_id` = 'ASR_Wav2Vec2Vi';
UPDATE `ai_agent_template` SET `asr_model_id` = 'ASR_ZipformerVi' WHERE `asr_model_id` = 'ASR_Wav2Vec2Vi';

-- 4. Remove old Wav2Vec2Vi
DELETE FROM `ai_model_config` WHERE `id` = 'ASR_Wav2Vec2Vi';
DELETE FROM `ai_model_provider` WHERE `id` = 'SYSTEM_ASR_Wav2Vec2Vi';
