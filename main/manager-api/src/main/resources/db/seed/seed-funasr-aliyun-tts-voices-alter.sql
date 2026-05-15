-- Slim docs for models kept in seed-ai-model-config (no extra ASR/TTS rows).
-- -------------------------------------------------------
ALTER TABLE `ai_model_config` MODIFY COLUMN `remark` TEXT COMMENT 'Notes';

UPDATE `ai_model_config` SET
`doc_link` = 'https://github.com/modelscope/FunASR',
`remark` = 'FunASR local model:
1. Place weights under xiaozhi-server/models/SenseVoiceSmall
2. Chinese, Japanese, Korean, Cantonese
3. Offline inference
4. Audio under tmp/' WHERE `id` = 'ASR_FunASR';

UPDATE `ai_model_config` SET
`doc_link` = 'https://github.com/k2-fsa/sherpa-onnx',
`remark` = 'Sherpa ASR:
1. Downloads models to models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17 at runtime
2. Chinese, English, Japanese, Korean, Cantonese, etc.
3. Offline
4. Output under tmp/' WHERE `id` = 'ASR_SherpaASR';

UPDATE `ai_model_config` SET
`doc_link` = 'https://github.com/rany2/edge-tts',
`remark` = 'Edge TTS:
1. Microsoft Edge TTS endpoint
2. Many locales/voices
3. No signup for basic use
4. Network required
5. Output under tmp/' WHERE `id` = 'TTS_EdgeTTS';

UPDATE `ai_model_config` SET
`doc_link` = 'https://aistudio.google.com/apikey',
`remark` = 'Gemini:
1. Google Gemini API
2. Sample model gemini-2.0-flash
3. Network required
4. Optional HTTP proxy
Steps:
1. https://aistudio.google.com/apikey
2. Create key
3. Paste into config
Follow generative-AI rules in your jurisdiction' WHERE `id` = 'LLM_GeminiLLM';

UPDATE `ai_model_config` SET
`doc_link` = NULL,
`remark` = 'No memory:
1. No chat history stored
2. Each turn is independent
3. No extra setup
4. Stronger privacy' WHERE `id` = 'Memory_nomem';

UPDATE `ai_model_config` SET
`doc_link` = NULL,
`remark` = 'Local short-term memory:
1. History on disk
2. Summaries via selected LLM module
3. Data stays local
4. Privacy-friendly
5. No cloud keys needed' WHERE `id` = 'Memory_mem_local_short';

UPDATE `ai_model_config` SET
`doc_link` = 'https://app.mem0.ai/dashboard/api-keys',
`remark` = 'Mem0:
1. Cloud memory service
2. API key required
3. Network required
4. Free tier includes limited monthly calls
Steps:
1. https://app.mem0.ai/dashboard/api-keys
2. Paste key' WHERE `id` = 'Memory_mem0ai';

UPDATE `ai_model_config` SET
`doc_link` = NULL,
`remark` = 'No intent:
1. Skip intent routing
2. All text goes to LLM
3. No extra setup
4. Simple chat only' WHERE `id` = 'Intent_nointent';

UPDATE `ai_model_config` SET
`doc_link` = NULL,
`remark` = 'LLM intent:
1. Separate LLM classifies intent
2. Defaults to selected LLM module
3. Can point to another cheap/small LLM
4. Flexible but slower
5. No low-level IoT volume control
Set llm field or fall back to selected_module.LLM' WHERE `id` = 'Intent_intent_llm';

UPDATE `ai_model_config` SET
`doc_link` = NULL,
`remark` = 'Function-call intent:
1. Uses LLM tool/function calling
2. Requires a function-call capable LLM
3. Fast tool routing
4. Supports IoT-style commands
5. Built-ins include:
   - handle_exit_intent
   - play_music
   - change_role
   - get_weather
   - get_news
Configure extra tools in functions; base set is already loaded' WHERE `id` = 'Intent_function_call';

UPDATE `ai_model_config` SET
`doc_link` = 'https://github.com/snakers4/silero-vad',
`remark` = 'Silero VAD:
1. Voice activity detection
2. Offline
3. Models under models/snakers4_silero-vad
4. Tuning:
   - threshold: 0.5
   - min_silence_duration_ms: 700
5. Raise min_silence_duration_ms if users pause longer between phrases' WHERE `id` = 'VAD_SileroVAD';
