-- Model provider seed data (Liquibase; do not run manually)
-- Aligned with slim seed-ai-model-config: VAD/ASR/LLM Gemini/TTS Edge + Memory + Intent.
-- --------------------------------------------------------
DELETE FROM `ai_model_provider`;
INSERT INTO `ai_model_provider` (`id`, `model_type`, `provider_code`, `name`, `fields`, `sort`, `creator`, `create_date`, `updater`, `update_date`) VALUES
('SYSTEM_VAD_SileroVAD', 'VAD', 'silero', 'Silero VAD', '[{"key":"threshold","label":"Detection threshold","type":"number"},{"key":"model_dir","label":"Model directory","type":"string"},{"key":"min_silence_duration_ms","label":"Min silence (ms)","type":"number"}]', 1, 1, NOW(), 1, NOW()),

('SYSTEM_ASR_FunASR', 'ASR', 'fun_local', 'FunASR', '[{"key":"model_dir","label":"Model directory","type":"string"},{"key":"output_dir","label":"Output directory","type":"string"}]', 1, 1, NOW(), 1, NOW()),
('SYSTEM_ASR_SherpaASR', 'ASR', 'sherpa_onnx_local', 'Sherpa ASR', '[{"key":"model_dir","label":"Model directory","type":"string"},{"key":"output_dir","label":"Output directory","type":"string"}]', 2, 1, NOW(), 1, NOW()),
('SYSTEM_ASR_ZipformerVi', 'ASR', 'zipformer_vi', 'Zipformer Vietnamese (6000h)', '[{"key":"model_dir","label":"Model directory","type":"string"},{"key":"output_dir","label":"Output directory","type":"string"},{"key":"num_threads","label":"Inference threads","type":"number"}]', 3, 1, NOW(), 1, NOW()),

('SYSTEM_LLM_gemini', 'LLM', 'gemini', 'Gemini', '[{"key":"api_key","label":"API key","type":"string"},{"key":"model_name","label":"Model name","type":"string"},{"key":"http_proxy","label":"HTTP proxy","type":"string"},{"key":"https_proxy","label":"HTTPS proxy","type":"string"}]', 1, 1, NOW(), 1, NOW()),
('SYSTEM_LLM_openai', 'LLM', 'openai', 'OpenAI', '[{"key":"api_key","label":"API key","type":"password"},{"key":"base_url","label":"Base URL","type":"string"},{"key":"model_name","label":"Model name","type":"string"},{"key":"temperature","label":"Temperature","type":"string"},{"key":"max_tokens","label":"Max tokens","type":"string"},{"key":"top_p","label":"Top P","type":"string"},{"key":"frequency_penalty","label":"Frequency penalty","type":"string"}]', 2, 1, NOW(), 1, NOW()),

('SYSTEM_TTS_edge', 'TTS', 'edge', 'Edge TTS', '[{"key":"voice","label":"Voice","type":"string"},{"key":"output_dir","label":"Output directory","type":"string"}]', 1, 1, NOW(), 1, NOW()),

('SYSTEM_Memory_mem0ai', 'Memory', 'mem0ai', 'Mem0AI', '[{"key":"api_key","label":"API key","type":"string"}]', 1, 1, NOW(), 1, NOW()),
('SYSTEM_Memory_nomem', 'Memory', 'nomem', 'No memory', '[]', 2, 1, NOW(), 1, NOW()),
('SYSTEM_Memory_mem_local_short', 'Memory', 'mem_local_short', 'Local short memory', '[]', 3, 1, NOW(), 1, NOW()),

('SYSTEM_Intent_nointent', 'Intent', 'nointent', 'No intent', '[]', 1, 1, NOW(), 1, NOW()),
('SYSTEM_Intent_intent_llm', 'Intent', 'intent_llm', 'LLM intent', '[{"key":"llm","label":"LLM model","type":"string"}]', 2, 1, NOW(), 1, NOW()),
('SYSTEM_Intent_function_call', 'Intent', 'function_call', 'Function-call intent', '[{"key":"functions","label":"Functions","type":"dict","dict_name":"functions"}]', 3, 1, NOW(), 1, NOW());
