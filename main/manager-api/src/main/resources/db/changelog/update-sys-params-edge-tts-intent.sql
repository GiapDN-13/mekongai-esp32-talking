-- Pre-0.3.0 param fixes
update `sys_params` set param_value = '.mp3;.wav;.p3' where  param_code = 'plugins.play_music.music_ext';
update `ai_model_config` set config_json =  '{\"type\": \"intent_llm\", \"llm\": \"LLM_GeminiLLM\"}' where  id = 'Intent_intent_llm';

-- Edge TTS sample voices
delete from `ai_tts_voice` where tts_model_id = 'TTS_EdgeTTS';
INSERT INTO `ai_tts_voice` VALUES 
('TTS_EdgeTTS0001', 'TTS_EdgeTTS', 'Edge TTS female Xiaoxiao', 'zh-CN-XiaoxiaoNeural', 'Mandarin', NULL, NULL, 1, NULL, NULL, NULL, NULL),
('TTS_EdgeTTS0002', 'TTS_EdgeTTS', 'Edge TTS male Yunyang', 'zh-CN-YunyangNeural', 'Mandarin', NULL, NULL, 1, NULL, NULL, NULL, NULL),
('TTS_EdgeTTS0003', 'TTS_EdgeTTS', 'Edge TTS female Xiaoyi', 'zh-CN-XiaoyiNeural', 'Mandarin', NULL, NULL, 1, NULL, NULL, NULL, NULL),
('TTS_EdgeTTS0004', 'TTS_EdgeTTS', 'Edge TTS male Yunjian', 'zh-CN-YunjianNeural', 'Mandarin', NULL, NULL, 1, NULL, NULL, NULL, NULL),
('TTS_EdgeTTS0005', 'TTS_EdgeTTS', 'Edge TTS male Yunxi', 'zh-CN-YunxiNeural', 'Mandarin', NULL, NULL, 1, NULL, NULL, NULL, NULL),
('TTS_EdgeTTS0006', 'TTS_EdgeTTS', 'Edge TTS male Yunxia', 'zh-CN-YunxiaNeural', 'Mandarin', NULL, NULL, 1, NULL, NULL, NULL, NULL),
('TTS_EdgeTTS0007', 'TTS_EdgeTTS', 'Edge TTS female Liaoning Xiaobei', 'zh-CN-liaoning-XiaobeiNeural', 'Liaoning', NULL, NULL, 1, NULL, NULL, NULL, NULL),
('TTS_EdgeTTS0008', 'TTS_EdgeTTS', 'Edge TTS female Shaanxi Xiaoni', 'zh-CN-shaanxi-XiaoniNeural', 'Shaanxi', NULL, NULL, 1, NULL, NULL, NULL, NULL),
('TTS_EdgeTTS0009', 'TTS_EdgeTTS', 'Edge TTS female HK HiuGaai', 'zh-HK-HiuGaaiNeural', 'Cantonese', 'General', 'Friendly, Positive', 1, NULL, NULL, NULL, NULL),
('TTS_EdgeTTS0010', 'TTS_EdgeTTS', 'Edge TTS female HK HiuMaan', 'zh-HK-HiuMaanNeural', 'Cantonese', 'General', 'Friendly, Positive', 1, NULL, NULL, NULL, NULL),
('TTS_EdgeTTS0011', 'TTS_EdgeTTS', 'Edge TTS male HK WanLung', 'zh-HK-WanLungNeural', 'Cantonese', 'General', 'Friendly, Positive', 1, NULL, NULL, NULL, NULL);

-- Registration and frontend URL
delete from `sys_params` where  id in (103,104);
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (103, 'server.allow_user_register', 'false', 'boolean', 1, 'Allow non-admin user registration');
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (104, 'server.fronted_url', 'http://xiaozhi.server.com', 'string', 1, 'Control panel URL shown with 6-digit verification codes');
