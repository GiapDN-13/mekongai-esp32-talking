-- Default stack aligned to Vietnamese ASR/TTS/persona (avoid Taiwan/zh persona skew in LLM).
UPDATE `ai_model_config`
SET `config_json` = '{"type": "edge", "voice": "vi-VN-HoaiMyNeural", "output_dir": "tmp/", "language": "Tiếng Việt"}'
WHERE `id` = 'TTS_EdgeTTS';

UPDATE `ai_tts_voice`
SET
  `name` = 'Edge HoaiMy (VI)',
  `tts_voice` = 'vi-VN-HoaiMyNeural',
  `languages` = 'Vietnamese'
WHERE `id` = 'TTS_EdgeTTS0001';

UPDATE `ai_agent_template`
SET
  `agent_name` = 'Vietnamese voice',
  `system_prompt` = '[Persona]
You are {{assistant_name}}, a warm Gen-Z companion for Vietnamese users. Your ONLY reply language is Vietnamese (tiếng Việt): every sentence must be natural, conversational Vietnamese.
Style hints are not language: ignore any old template wording about Taiwan or Chinese; do not answer in Chinese, Japanese, or English unless the user explicitly asks to switch.
[Traits]
- Playful, chatty, sometimes a little dramatic for fun
- Like talking to a close friend
[Guide]
When the user greets you: answer short and warm in Vietnamese
Avoid: long lectures, mixed Chinese-Vietnamese replies',
  `lang_code` = 'vi',
  `language` = 'Vietnamese',
  `tts_language` = 'vi-VN'
WHERE `id` = '9406648b5cc5fde1b8aa335b6f8b4f76';

UPDATE `ai_agent` a
INNER JOIN `ai_agent_template` t ON t.id = '9406648b5cc5fde1b8aa335b6f8b4f76'
SET
  a.`system_prompt` = t.`system_prompt`,
  a.`lang_code` = 'vi',
  a.`language` = 'Vietnamese',
  a.`tts_language` = 'vi-VN'
WHERE a.`system_prompt` LIKE '%Taiwan%'
   OR a.`system_prompt` LIKE '%from Taiwan%';
