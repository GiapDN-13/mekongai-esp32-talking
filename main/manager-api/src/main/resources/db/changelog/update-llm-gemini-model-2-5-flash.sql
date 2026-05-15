-- Bump default Gemini model id for API quota / model availability (2.0 free tier may hit limit:0).
UPDATE `ai_model_config`
SET `config_json` = REPLACE(`config_json`, 'gemini-2.0-flash', 'gemini-2.5-flash')
WHERE `id` = 'LLM_GeminiLLM' AND `config_json` LIKE '%gemini-2.0-flash%';
