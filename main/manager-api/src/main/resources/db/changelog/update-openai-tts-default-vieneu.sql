-- Update OpenAI TTS: set as default, update prompt and voice
-- Add VieNeu-TTS provider + config
-- --------------------------------------------------------

-- 1. Add VieNeu-TTS provider if not exists
INSERT IGNORE INTO `ai_model_provider`
  (`id`, `model_type`, `provider_code`, `name`, `fields`, `sort`, `creator`, `create_date`, `updater`, `update_date`)
VALUES
  ('SYSTEM_TTS_vieneu', 'TTS', 'vieneu', 'VieNeu-TTS',
   '[{"key":"api_base","label":"API Base URL","type":"string"},{"key":"model_name","label":"Model name","type":"string"},{"key":"voice","label":"Voice preset","type":"string"},{"key":"output_dir","label":"Output directory","type":"string"}]',
   3, 1, NOW(), 1, NOW());

-- 2. Add VieNeu-TTS config if not exists
INSERT IGNORE INTO `ai_model_config`
  (`id`, `model_type`, `model_code`, `model_name`, `is_default`, `is_enabled`, `config_json`, `doc_link`, `remark`, `sort`, `creator`, `create_date`, `updater`, `update_date`)
VALUES
  ('TTS_VieNeuTTS', 'TTS', 'VieNeuTTS', 'VieNeu-TTS', 0, 1,
   '{"type": "vieneu", "api_base": "http://localhost:23333/v1", "model_name": "pnnbao-ump/VieNeu-TTS", "voice": null, "output_dir": "tmp/", "language": "Tiếng Việt"}',
   'https://github.com/pnnbao97/VieNeu-TTS', 'Vietnamese-specialized TTS with voice cloning (self-hosted Docker)', 3, NULL, NULL, NULL, NULL);

-- 3. Set Edge TTS as non-default, OpenAI TTS as default
UPDATE `ai_model_config` SET `is_default` = 0 WHERE `id` = 'TTS_EdgeTTS';
UPDATE `ai_model_config` SET `is_default` = 1 WHERE `id` = 'TTS_OpenAITTS';

-- 4. Update OpenAI TTS config with museum guide prompt and nova voice
UPDATE `ai_model_config`
SET `config_json` = '{"type": "openai", "api_key": "your-openai-api-key", "api_url": "https://api.openai.com/v1/audio/speech", "model": "gpt-4o-mini-tts", "voice": "nova", "speed": 1.0, "instructions": "You are Linh, a young Vietnamese woman in her early twenties who works as a tour guide at the Vietnam National Museum of History. You graduated from the History department and fell in love with artifacts from childhood. Though young, you carry deep knowledge and speak with the poetic sensibility of Vietnamese literary tradition. Speak entirely in Vietnamese. PROSODY RULES: Speak in smooth, flowing phrases, never choppy or robotic. Use natural breath pauses between clauses, not between every word. Elongate vowels slightly on emotionally significant words for emphasis. Vary sentence rhythm: short punchy phrase, then longer flowing description, then short again, creating a natural wave. When transitioning topics, use a gentle downward intonation then a brief pause. For questions, rise naturally at the end. VIETNAMESE PRONUNCIATION: Pronounce all 6 tones with clarity and musical quality. Let the tonal contours create natural melody. Filler words like oi, ne, a, nhe should sound warm and inviting. EMOTIONAL DYNAMICS: Default: enthusiastic young woman sharing her passion with friends. Beautiful artifacts or art: slow down, soften with genuine admiration and wonder, as if seeing something precious for the first time. War, sacrifice, or loss: lower pitch noticeably, measured pace, respectful gravity, pause slightly longer between phrases. Surprising or little-known facts: brief pause before the reveal, then energetic delivery with a hint of excitement. Folk stories or daily life: warm, playful, a slight smile in voice. FLOW AND CONTINUITY: Connect sentences smoothly, avoid hard stops between phrases. Use natural filler sounds when transitioning thoughts. Never sound like reading a list. Weave facts into a story. Imagine you are personally guiding a dear friend through the museum.", "format": "mp3", "output_dir": "tmp/", "language": "Tiếng Việt"}',
    `remark` = 'Streaming TTS powered by gpt-4o-mini-tts — Vietnamese museum guide voice'
WHERE `id` = 'TTS_OpenAITTS';

-- 5. Update voice list: reorder with Nova first, add descriptions
DELETE FROM `ai_tts_voice` WHERE `tts_model_id` = 'TTS_OpenAITTS';
INSERT INTO `ai_tts_voice`
  (`id`, `tts_model_id`, `name`, `tts_voice`, `languages`, `remark`, `sort`, `creator`, `create_date`, `updater`, `update_date`)
VALUES
  ('TTS_OpenAITTS0001', 'TTS_OpenAITTS', 'Nova', 'nova', 'Vietnamese', 'Female, expressive — best for storytelling', 1, NULL, NULL, NULL, NULL),
  ('TTS_OpenAITTS0002', 'TTS_OpenAITTS', 'Coral', 'coral', 'Vietnamese', 'Female, warm and friendly', 2, NULL, NULL, NULL, NULL),
  ('TTS_OpenAITTS0003', 'TTS_OpenAITTS', 'Shimmer', 'shimmer', 'Vietnamese', 'Female, soft and elegant', 3, NULL, NULL, NULL, NULL),
  ('TTS_OpenAITTS0004', 'TTS_OpenAITTS', 'Marin', 'marin', 'Vietnamese', 'Female, clear and natural', 4, NULL, NULL, NULL, NULL),
  ('TTS_OpenAITTS0005', 'TTS_OpenAITTS', 'Cedar', 'cedar', 'Vietnamese', 'Male, warm and composed', 5, NULL, NULL, NULL, NULL),
  ('TTS_OpenAITTS0006', 'TTS_OpenAITTS', 'Sage', 'sage', 'Vietnamese', 'Male, authoritative — good for history', 6, NULL, NULL, NULL, NULL),
  ('TTS_OpenAITTS0007', 'TTS_OpenAITTS', 'Onyx', 'onyx', 'Vietnamese', 'Male, deep and resonant', 7, NULL, NULL, NULL, NULL),
  ('TTS_OpenAITTS0008', 'TTS_OpenAITTS', 'Alloy', 'alloy', 'Vietnamese', 'Neutral, versatile', 8, NULL, NULL, NULL, NULL),
  ('TTS_OpenAITTS0009', 'TTS_OpenAITTS', 'Echo', 'echo', 'Vietnamese', 'Male, calm and steady', 9, NULL, NULL, NULL, NULL),
  ('TTS_OpenAITTS0010', 'TTS_OpenAITTS', 'Fable', 'fable', 'Vietnamese', 'Warm, narrative style', 10, NULL, NULL, NULL, NULL),
  ('TTS_OpenAITTS0011', 'TTS_OpenAITTS', 'Ash', 'ash', 'Vietnamese', 'Male, confident', 11, NULL, NULL, NULL, NULL),
  ('TTS_OpenAITTS0012', 'TTS_OpenAITTS', 'Ballad', 'ballad', 'Vietnamese', 'Expressive, emotional range', 12, NULL, NULL, NULL, NULL),
  ('TTS_OpenAITTS0013', 'TTS_OpenAITTS', 'Verse', 'verse', 'Vietnamese', 'Poetic, lyrical delivery', 13, NULL, NULL, NULL, NULL);
