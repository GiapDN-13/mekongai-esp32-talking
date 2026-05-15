package xiaozhi.modules.llm.service.impl;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.apache.commons.lang3.StringUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import cn.hutool.json.JSONArray;
import cn.hutool.json.JSONObject;
import cn.hutool.json.JSONUtil;
import lombok.extern.slf4j.Slf4j;
import xiaozhi.modules.llm.service.LLMService;
import xiaozhi.modules.model.entity.ModelConfigEntity;
import xiaozhi.modules.model.service.ModelConfigService;

/**
 * LLM calls via OpenAI-compatible HTTP APIs (e.g. Alibaba, DeepSeek, ChatGLM-compatible endpoints).
 */
@Slf4j
@Service
public class OpenAIStyleLLMServiceImpl implements LLMService {

    @Autowired
    private ModelConfigService modelConfigService;

    private final RestTemplate restTemplate = new RestTemplate();

    private static final String DEFAULT_SUMMARY_PROMPT = "You are an experienced memory summarizer. Summarize the dialogue into durable user memory. Rules:\n"
            + "1) Capture important facts about the user for future personalization.\n"
            + "2) Do not repeat or drop prior memory unless it already exceeds ~1800 characters; do not compress useful history without cause.\n"
            + "3) Omit device control noise (volume, music playback, weather widgets, exit/stop chatting) unless it reflects a lasting user preference.\n"
            + "4) Omit ephemeral context (today's date/time, one-off weather) that would harm later turns if stored as memory.\n"
            + "5) Omit raw success/failure of device commands and filler chatter.\n"
            + "6) If the chat has no meaningful new facts, you may return the previous memory unchanged.\n"
            + "7) Output only the summary body, max ~1800 characters, no preamble.\n"
            + "8) No code, XML, or meta explanation; extract only from the dialogue, no fabricated examples.\n"
            + "9) If prior memory is provided, merge intelligently: keep valuable old facts and add new important ones.\n\n"
            + "Prior memory:\n{history_memory}\n\nNew dialogue:\n{conversation}";

    @Override
    public String generateSummary(String conversation) {
        return generateSummary(conversation, null, null);
    }

    @Override
    public String generateSummaryWithModel(String conversation, String modelId) {
        return generateSummary(conversation, null, modelId);
    }

    @Override
    public String generateSummary(String conversation, String promptTemplate, String modelId) {
        if (!isAvailable()) {
            log.warn("LLM service unavailable; cannot generate summary");
            return "LLM service unavailable; cannot generate summary";
        }

        try {
            ModelConfigEntity llmConfig;
            if (modelId != null && !modelId.trim().isEmpty()) {
                llmConfig = modelConfigService.getModelByIdFromCache(modelId);
            } else {
                llmConfig = getDefaultLLMConfig();
            }

            if (llmConfig == null || llmConfig.getConfigJson() == null) {
                log.error("No usable LLM model config, modelId: {}", modelId);
                return "No usable LLM model configuration";
            }

            JSONObject configJson = llmConfig.getConfigJson();
            String baseUrl = configJson.getStr("base_url");
            String model = configJson.getStr("model_name");
            String apiKey = configJson.getStr("api_key");
            Double temperature = configJson.getDouble("temperature");
            Integer maxTokens = configJson.getInt("max_tokens");

            if (StringUtils.isBlank(baseUrl) || StringUtils.isBlank(apiKey)) {
                log.error("Incomplete LLM config: base_url or api_key is blank");
                return "Incomplete LLM configuration; cannot generate summary";
            }

            String prompt = (promptTemplate != null ? promptTemplate : DEFAULT_SUMMARY_PROMPT)
                    .replace("{history_memory}", "None.")
                    .replace("{conversation}", conversation);

            Map<String, Object> requestBody = new HashMap<>();
            requestBody.put("model", model != null ? model : "gpt-3.5-turbo");

            Map<String, Object>[] messages = new Map[1];
            Map<String, Object> message = new HashMap<>();
            message.put("role", "user");
            message.put("content", prompt);
            messages[0] = message;

            requestBody.put("messages", messages);
            requestBody.put("temperature", temperature != null ? temperature : 0.7);
            requestBody.put("max_tokens", maxTokens != null ? maxTokens : 2000);

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            headers.set("Authorization", "Bearer " + apiKey);

            HttpEntity<Map<String, Object>> entity = new HttpEntity<>(requestBody, headers);

            String apiUrl = baseUrl;
            if (!apiUrl.endsWith("/chat/completions")) {
                if (!apiUrl.endsWith("/")) {
                    apiUrl += "/";
                }
                apiUrl += "chat/completions";
            }

            ResponseEntity<String> response = restTemplate.exchange(
                    apiUrl, HttpMethod.POST, entity, String.class);

            if (response.getStatusCode().is2xxSuccessful()) {
                JSONObject responseJson = JSONUtil.parseObj(response.getBody());
                JSONArray choices = responseJson.getJSONArray("choices");
                if (choices != null && choices.size() > 0) {
                    JSONObject choice = choices.getJSONObject(0);
                    JSONObject messageObj = choice.getJSONObject("message");
                    return messageObj.getStr("content");
                }
            } else {
                log.error("LLM API call failed, status: {}, body: {}", response.getStatusCode(), response.getBody());
            }
        } catch (Exception e) {
            log.error("Error calling LLM for summary, modelId: {}", modelId, e);
        }

        return "Summary generation failed; try again later";
    }

    @Override
    public String generateSummary(String conversation, String promptTemplate) {
        return generateSummary(conversation, promptTemplate, null);
    }

    @Override
    public String generateSummaryWithHistory(String conversation, String historyMemory, String promptTemplate,
            String modelId) {
        if (!isAvailable()) {
            log.warn("LLM service unavailable; cannot generate summary");
            return "LLM service unavailable; cannot generate summary";
        }

        try {
            ModelConfigEntity llmConfig;
            if (modelId != null && !modelId.trim().isEmpty()) {
                llmConfig = modelConfigService.getModelByIdFromCache(modelId);
            } else {
                llmConfig = getDefaultLLMConfig();
            }

            if (llmConfig == null || llmConfig.getConfigJson() == null) {
                log.error("No usable LLM model config, modelId: {}", modelId);
                return "No usable LLM model configuration";
            }

            JSONObject configJson = llmConfig.getConfigJson();
            String baseUrl = configJson.getStr("base_url");
            String model = configJson.getStr("model_name");
            String apiKey = configJson.getStr("api_key");

            if (StringUtils.isBlank(baseUrl) || StringUtils.isBlank(apiKey)) {
                log.error("Incomplete LLM config: base_url or api_key is blank");
                return "Incomplete LLM configuration; cannot generate summary";
            }

            String prompt = (promptTemplate != null ? promptTemplate : DEFAULT_SUMMARY_PROMPT)
                    .replace("{history_memory}", historyMemory != null ? historyMemory : "No prior memory")
                    .replace("{conversation}", conversation);

            Map<String, Object> requestBody = new HashMap<>();
            requestBody.put("model", model != null ? model : "gpt-3.5-turbo");

            Map<String, Object>[] messages = new Map[1];
            Map<String, Object> message = new HashMap<>();
            message.put("role", "user");
            message.put("content", prompt);
            messages[0] = message;

            requestBody.put("messages", messages);
            requestBody.put("temperature", 0.2);
            requestBody.put("max_tokens", 2000);

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            headers.set("Authorization", "Bearer " + apiKey);

            HttpEntity<Map<String, Object>> entity = new HttpEntity<>(requestBody, headers);

            String apiUrl = baseUrl;
            if (!apiUrl.endsWith("/chat/completions")) {
                if (!apiUrl.endsWith("/")) {
                    apiUrl += "/";
                }
                apiUrl += "chat/completions";
            }

            ResponseEntity<String> response = restTemplate.exchange(
                    apiUrl, HttpMethod.POST, entity, String.class);

            if (response.getStatusCode().is2xxSuccessful()) {
                JSONObject responseJson = JSONUtil.parseObj(response.getBody());
                JSONArray choices = responseJson.getJSONArray("choices");
                if (choices != null && choices.size() > 0) {
                    JSONObject choice = choices.getJSONObject(0);
                    JSONObject messageObj = choice.getJSONObject("message");
                    return messageObj.getStr("content");
                }
            } else {
                log.error("LLM API call failed, status: {}, body: {}", response.getStatusCode(), response.getBody());
            }
        } catch (Exception e) {
            log.error("Error calling LLM for summary, modelId: {}", modelId, e);
        }

        return "Summary generation failed; try again later";
    }

    @Override
    public boolean isAvailable() {
        try {
            ModelConfigEntity defaultLLMConfig = getDefaultLLMConfig();
            if (defaultLLMConfig == null || defaultLLMConfig.getConfigJson() == null) {
                return false;
            }

            JSONObject configJson = defaultLLMConfig.getConfigJson();
            String baseUrl = configJson.getStr("base_url");
            String apiKey = configJson.getStr("api_key");

            return baseUrl != null && !baseUrl.trim().isEmpty() &&
                    apiKey != null && !apiKey.trim().isEmpty();
        } catch (Exception e) {
            log.error("Error checking LLM availability", e);
            return false;
        }
    }

    @Override
    public boolean isAvailable(String modelId) {
        try {
            if (modelId == null || modelId.trim().isEmpty()) {
                return isAvailable();
            }

            ModelConfigEntity modelConfig = modelConfigService.getModelByIdFromCache(modelId);
            if (modelConfig == null || modelConfig.getConfigJson() == null) {
                log.warn("No LLM model config for modelId: {}", modelId);
                return false;
            }

            JSONObject configJson = modelConfig.getConfigJson();
            String baseUrl = configJson.getStr("base_url");
            String apiKey = configJson.getStr("api_key");

            return baseUrl != null && !baseUrl.trim().isEmpty() &&
                    apiKey != null && !apiKey.trim().isEmpty();
        } catch (Exception e) {
            log.error("Error checking LLM availability, modelId: {}", modelId, e);
            return false;
        }
    }

    /** Resolve default LLM config from admin (marked default, else first enabled LLM). */
    private ModelConfigEntity getDefaultLLMConfig() {
        try {
            List<ModelConfigEntity> llmConfigs = modelConfigService.getEnabledModelsByType("LLM");
            if (llmConfigs == null || llmConfigs.isEmpty()) {
                return null;
            }

            for (ModelConfigEntity config : llmConfigs) {
                if (config.getIsDefault() != null && config.getIsDefault() == 1) {
                    return config;
                }
            }

            return llmConfigs.get(0);
        } catch (Exception e) {
            log.error("Error loading default LLM config", e);
            return null;
        }
    }
}