-- FunASR server provider fields
UPDATE `ai_model_provider` SET fields = '[{"key": "host", "type": "string", "label": "Service host"}, {"key": "port", "type": "number", "label": "Port"}, {"key": "type", "type": "string", "label": "Service type"}, {"key": "is_ssl", "type": "boolean", "label": "Use SSL"}, {"key": "api_key", "type": "string", "label": "API key"}, {"key": "output_dir", "type": "string", "label": "Output directory"}]' WHERE id = 'SYSTEM_ASR_FunASRServer';

UPDATE `ai_model_config` SET 
config_json = '{"host": "127.0.0.1", "port": 10096, "type": "fun_server", "is_ssl": true, "api_key": "none", "output_dir": "tmp/"}',
`doc_link` = 'https://github.com/modelscope/FunASR/blob/main/runtime/docs/SDK_advanced_guide_online_zh.md',
`remark` = 'Self-hosted FunASR HTTP API (five steps):
1) mkdir -p ./funasr-runtime-resources/models
2) sudo docker run -p 10096:10095 -it --privileged=true -v $PWD/funasr-runtime-resources/models:/workspace/models registry.cn-hangzhou.aliyuncs.com/funasr_repo/funasr:funasr-runtime-sdk-online-cpu-0.1.12
3) In the container: cd FunASR/runtime
4) nohup bash run_server_2pass.sh --download-model-dir /workspace/models --vad-dir damo/speech_fsmn_vad_zh-cn-16k-common-onnx --model-dir damo/speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-onnx  --online-model-dir damo/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-online-onnx  --punc-dir damo/punc_ct-transformer_zh-cn-common-vad_realtime-vocab272727-onnx --lm-dir damo/speech_ngram_lm_zh-cn-ai-wesp-fst --itn-dir thuduj12/fst_itn_zh --hotword /workspace/models/hotwords.txt > log.txt 2>&1 &
5) tail -f log.txt until models are ready.
GPU: https://github.com/modelscope/FunASR/blob/main/runtime/docs/SDK_advanced_guide_online_zh.md' WHERE `id` = 'ASR_FunASRServer';

UPDATE `ai_model_config` SET 
`doc_link` = 'https://github.com/xinnan-tech/xiaozhi-esp32-server/blob/main/docs/fish-speech-integration.md',
`remark` = 'FishSpeech:
1. Run FishSpeech locally
2. Custom voices supported
3. Local inference, no cloud required
4. Output under tmp/
5. Guide: https://github.com/xinnan-tech/xiaozhi-esp32-server/blob/main/docs/fish-speech-integration.md' WHERE `id` = 'TTS_FishSpeech';
