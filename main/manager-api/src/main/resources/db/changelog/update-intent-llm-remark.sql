-- Intent: LLM-based intent
UPDATE `ai_model_config` SET 
`doc_link` = NULL,
`remark` = 'LLM intent recognition:
1. Uses a dedicated LLM for intent
2. Defaults to selected_module.LLM
3. You may point to another LLM (e.g. Gemini)
4. Flexible but adds latency
Config:
1. Set llm to the model id to use
2. Leave empty to use selected_module.LLM' WHERE `id` = 'Intent_intent_llm';

-- Intent: function calling
UPDATE `ai_model_config` SET 
`doc_link` = NULL,
`remark` = 'Function-call intent:
1. Uses the LLM function_call capability
2. The chosen LLM must support function_call
3. Tools run on demand; lower latency' WHERE `id` = 'Intent_function_call';
