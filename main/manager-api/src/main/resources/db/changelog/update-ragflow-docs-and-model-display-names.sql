-- Intent display names only (slim seed: no RAG / extra TTS-ASR rows).
UPDATE `ai_model_config` SET `model_name` = 'External LLM intent' WHERE `id` = 'Intent_intent_llm';
UPDATE `ai_model_config` SET `model_name` = 'LLM function calling' WHERE `id` = 'Intent_function_call';

UPDATE `ai_model_provider` SET `name` = 'External LLM intent', `fields` = '[{"key":"llm","label":"Referenced LLM model","type":"string"}]' WHERE `id` = 'SYSTEM_Intent_intent_llm';
UPDATE `ai_model_provider` SET `name` = 'LLM function calling' WHERE `id` = 'SYSTEM_Intent_function_call';
