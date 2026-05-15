package xiaozhi.modules.model.controller;

import java.util.List;

import org.apache.shiro.authz.annotation.RequiresPermissions;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.AllArgsConstructor;
import xiaozhi.common.page.PageData;
import xiaozhi.common.utils.ConvertUtils;
import xiaozhi.common.utils.Result;
import xiaozhi.modules.agent.service.AgentTemplateService;
import xiaozhi.modules.config.service.ConfigService;
import xiaozhi.modules.model.dto.LlmModelBasicInfoDTO;
import xiaozhi.modules.model.dto.ModelBasicInfoDTO;
import xiaozhi.modules.model.dto.ModelConfigBodyDTO;
import xiaozhi.modules.model.dto.ModelConfigDTO;
import xiaozhi.modules.model.dto.ModelProviderDTO;
import xiaozhi.modules.model.dto.VoiceDTO;
import xiaozhi.modules.model.entity.ModelConfigEntity;
import xiaozhi.modules.model.service.ModelConfigService;
import xiaozhi.modules.model.service.ModelProviderService;
import xiaozhi.modules.timbre.service.TimbreService;

@AllArgsConstructor
@RestController
@RequestMapping("/models")
@Tag(name = "Model configuration")
public class ModelController {

    private final ModelProviderService modelProviderService;
    private final TimbreService timbreService;
    private final ModelConfigService modelConfigService;
    private final ConfigService configService;
    private final AgentTemplateService agentTemplateService;

    @GetMapping("/names")
    @Operation(summary = "List model display names")
    @RequiresPermissions("sys:role:normal")
    public Result<List<ModelBasicInfoDTO>> getModelNames(@RequestParam String modelType,
            @RequestParam(required = false) String modelName) {
        List<ModelBasicInfoDTO> modelList = modelConfigService.getModelCodeList(modelType, modelName);
        return new Result<List<ModelBasicInfoDTO>>().ok(modelList);
    }

    @GetMapping("/llm/names")
    @Operation(summary = "List LLM model basics")
    @RequiresPermissions("sys:role:normal")
    public Result<List<LlmModelBasicInfoDTO>> getLlmModelCodeList(@RequestParam(required = false) String modelName) {
        List<LlmModelBasicInfoDTO> llmModelCodeList = modelConfigService.getLlmModelCodeList(modelName);
        return new Result<List<LlmModelBasicInfoDTO>>().ok(llmModelCodeList);
    }

    @GetMapping("/{modelType}/provideTypes")
    @Operation(summary = "List model providers for a model type")
    @RequiresPermissions("sys:role:superAdmin")
    public Result<List<ModelProviderDTO>> getModelProviderList(@PathVariable String modelType) {
        List<ModelProviderDTO> modelProviderDTOS = modelProviderService.getListByModelType(modelType);
        return new Result<List<ModelProviderDTO>>().ok(modelProviderDTOS);
    }

    @GetMapping("/list")
    @Operation(summary = "Paged model configurations")
    @RequiresPermissions("sys:role:superAdmin")
    public Result<PageData<ModelConfigDTO>> getModelConfigList(
            @RequestParam(required = true) String modelType,
            @RequestParam(required = false) String modelName,
            @RequestParam(required = true, defaultValue = "0") String page,
            @RequestParam(required = true, defaultValue = "10") String limit) {
        PageData<ModelConfigDTO> pageList = modelConfigService.getPageList(modelType, modelName, page, limit);
        return new Result<PageData<ModelConfigDTO>>().ok(pageList);
    }

    @PostMapping("/{modelType}/{provideCode}")
    @Operation(summary = "Add model configuration")
    @RequiresPermissions("sys:role:superAdmin")
    public Result<ModelConfigDTO> addModelConfig(@PathVariable String modelType,
            @PathVariable String provideCode,
            @RequestBody ModelConfigBodyDTO modelConfigBodyDTO) {
        ModelConfigDTO modelConfigDTO = modelConfigService.add(modelType, provideCode, modelConfigBodyDTO);
        configService.getConfig(false);
        return new Result<ModelConfigDTO>().ok(modelConfigDTO);
    }

    @PutMapping("/{modelType}/{provideCode}/{id}")
    @Operation(summary = "Update model configuration")
    @RequiresPermissions("sys:role:superAdmin")
    public Result<ModelConfigDTO> editModelConfig(@PathVariable String modelType,
            @PathVariable String provideCode,
            @PathVariable String id,
            @RequestBody ModelConfigBodyDTO modelConfigBodyDTO) {
        ModelConfigDTO modelConfigDTO = modelConfigService.edit(modelType, provideCode, id, modelConfigBodyDTO);
        configService.getConfig(false);
        return new Result<ModelConfigDTO>().ok(modelConfigDTO);
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "Delete model configuration")
    @RequiresPermissions("sys:role:superAdmin")
    public Result<Void> deleteModelConfig(@PathVariable String id) {
        modelConfigService.delete(id);
        return new Result<>();
    }

    @GetMapping("/{id}")
    @Operation(summary = "Get model configuration by id")
    @RequiresPermissions("sys:role:superAdmin")
    public Result<ModelConfigDTO> getModelConfig(@PathVariable String id) {
        ModelConfigEntity item = modelConfigService.selectById(id);
        ModelConfigDTO modelConfigDTO = ConvertUtils.sourceToTarget(item, ModelConfigDTO.class);
        return new Result<ModelConfigDTO>().ok(modelConfigDTO);
    }

    @PostMapping("/test")
    @Operation(summary = "Test model connection (Qdrant, embedding API, etc.)")
    @RequiresPermissions("sys:role:superAdmin")
    public Result<Object> testModelConfig(@RequestBody java.util.Map<String, Object> configJson) {
        java.util.Map<String, Object> result = new java.util.HashMap<>();
        String type = (String) configJson.getOrDefault("type", "");

        // Test Qdrant connection
        String url = (String) configJson.getOrDefault("url", "");
        if (url != null && !url.isEmpty()) {
            try {
                var restTemplate = new org.springframework.web.client.RestTemplate();
                var headers = new org.springframework.http.HttpHeaders();
                String apiKey = (String) configJson.getOrDefault("api_key", "");
                if (apiKey != null && !apiKey.isEmpty()) {
                    headers.set("api-key", apiKey);
                }
                var entity = new org.springframework.http.HttpEntity<>(null, headers);
                restTemplate.exchange(url + "/healthz", org.springframework.http.HttpMethod.GET, entity, String.class);
                result.put("qdrant", "OK");
            } catch (Exception e) {
                result.put("qdrant", "FAIL: " + e.getMessage());
            }
        }

        // Test embedding API
        String embeddingProvider = (String) configJson.getOrDefault("embedding_provider", "");
        if ("gemini".equals(embeddingProvider)) {
            String geminiKey = (String) configJson.getOrDefault("gemini_api_key", "");
            String model = (String) configJson.getOrDefault("embedding_model", "gemini-embedding-001");
            if (geminiKey != null && !geminiKey.isEmpty()) {
                try {
                    var restTemplate = new org.springframework.web.client.RestTemplate();
                    var headers = new org.springframework.http.HttpHeaders();
                    headers.setContentType(org.springframework.http.MediaType.APPLICATION_JSON);
                    String apiUrl = "https://generativelanguage.googleapis.com/v1beta/models/" + model
                            + ":embedContent?key=" + geminiKey;
                    String body = "{\"model\":\"models/" + model + "\",\"content\":{\"parts\":[{\"text\":\"test\"}]}}";
                    var entity = new org.springframework.http.HttpEntity<>(body, headers);
                    restTemplate.exchange(apiUrl, org.springframework.http.HttpMethod.POST, entity, String.class);
                    result.put("embedding", "OK");
                } catch (Exception e) {
                    result.put("embedding", "FAIL: " + e.getMessage());
                }
            } else {
                result.put("embedding", "SKIP: no gemini_api_key");
            }
        } else if ("openai".equals(embeddingProvider)) {
            String openaiKey = (String) configJson.getOrDefault("openai_api_key", "");
            if (openaiKey != null && !openaiKey.isEmpty()) {
                try {
                    var restTemplate = new org.springframework.web.client.RestTemplate();
                    var headers = new org.springframework.http.HttpHeaders();
                    headers.setContentType(org.springframework.http.MediaType.APPLICATION_JSON);
                    headers.setBearerAuth(openaiKey);
                    String baseUrl = (String) configJson.getOrDefault("openai_base_url", "https://api.openai.com/v1");
                    String model = (String) configJson.getOrDefault("embedding_model", "text-embedding-3-small");
                    String body = "{\"model\":\"" + model + "\",\"input\":\"test\"}";
                    var entity = new org.springframework.http.HttpEntity<>(body, headers);
                    restTemplate.exchange(baseUrl + "/embeddings", org.springframework.http.HttpMethod.POST, entity, String.class);
                    result.put("embedding", "OK");
                } catch (Exception e) {
                    result.put("embedding", "FAIL: " + e.getMessage());
                }
            } else {
                result.put("embedding", "SKIP: no openai_api_key");
            }
        } else if ("bedrock".equals(embeddingProvider)) {
            String accessKey = (String) configJson.getOrDefault("bedrock_access_key", "");
            String secretKey = (String) configJson.getOrDefault("bedrock_secret_key", "");
            String region = (String) configJson.getOrDefault("bedrock_region", "us-east-1");
            if (accessKey != null && !accessKey.isEmpty() && secretKey != null && !secretKey.isEmpty()) {
                result.put("embedding", "OK (credentials provided, runtime validation by Python server)");
            } else {
                result.put("embedding", "SKIP: no bedrock_access_key or bedrock_secret_key");
            }
        } else if ("local".equals(embeddingProvider) || "fastembed".equals(embeddingProvider)) {
            String model = (String) configJson.getOrDefault("embedding_model", "BAAI/bge-m3");
            result.put("embedding", "OK (local model: " + model + ", validated at runtime by Python server)");
        }

        return new Result<Object>().ok(result);
    }

    @PutMapping("/enable/{id}/{status}")
    @Operation(summary = "Enable or disable model configuration")
    @RequiresPermissions("sys:role:superAdmin")
    public Result<Void> enableModelConfig(@PathVariable String id, @PathVariable Integer status) {
        ModelConfigEntity entity = modelConfigService.selectById(id);
        if (entity == null) {
            return new Result<Void>().error("Model configuration not found");
        }
        if (status == 0 && entity.getIsDefault() > 0) {
            return new Result<Void>().error("Cannot disable the default model configuration");
        }
        entity.setConfigJson(null);
        entity.setIsEnabled(status);
        modelConfigService.updateById(entity);
        return new Result<Void>();
    }

    @PutMapping("/default/{id}")
    @Operation(summary = "Set default model for type")
    @RequiresPermissions("sys:role:superAdmin")
    public Result<Void> setDefaultModel(@PathVariable String id) {
        ModelConfigEntity entity = modelConfigService.selectById(id);
        if (entity == null) {
            return new Result<Void>().error("Model configuration not found");
        }
        modelConfigService.setDefaultModel(entity.getModelType(), 0);
        entity.setIsEnabled(1);
        entity.setIsDefault(1);
        entity.setConfigJson(null);
        modelConfigService.updateById(entity);

        agentTemplateService.updateDefaultTemplateModelId(entity.getModelType(), entity.getId());

        configService.getConfig(false);
        return new Result<Void>();
    }

    @GetMapping("/{modelId}/voices")
    @Operation(summary = "List voices for a TTS model")
    @RequiresPermissions("sys:role:normal")
    public Result<List<VoiceDTO>> getVoiceList(@PathVariable String modelId,
            @RequestParam(required = false) String voiceName) {
        List<VoiceDTO> voiceList = timbreService.getVoiceNames(modelId, voiceName);
        return new Result<List<VoiceDTO>>().ok(voiceList);
    }
}
