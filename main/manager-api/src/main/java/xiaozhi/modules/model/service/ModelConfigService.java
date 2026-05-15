package xiaozhi.modules.model.service;

import java.util.List;
import java.util.Map;

import xiaozhi.common.page.PageData;
import xiaozhi.common.service.BaseService;
import xiaozhi.modules.model.dto.LlmModelBasicInfoDTO;
import xiaozhi.modules.model.dto.ModelBasicInfoDTO;
import xiaozhi.modules.model.dto.ModelConfigBodyDTO;
import xiaozhi.modules.model.dto.ModelConfigDTO;
import xiaozhi.modules.model.entity.ModelConfigEntity;

public interface ModelConfigService extends BaseService<ModelConfigEntity> {

    List<ModelBasicInfoDTO> getModelCodeList(String modelType, String modelName);

    List<LlmModelBasicInfoDTO> getLlmModelCodeList(String modelName);

    PageData<ModelConfigDTO> getPageList(String modelType, String modelName, String page, String limit);

    ModelConfigDTO add(String modelType, String provideCode, ModelConfigBodyDTO modelConfigBodyDTO);

    ModelConfigDTO edit(String modelType, String provideCode, String id, ModelConfigBodyDTO modelConfigBodyDTO);

    void delete(String id);

    /**
     * Resolve display name by configuration id.
     */
    String getModelNameById(String id);

    /**
     * Cached model configuration by id.
     */
    ModelConfigEntity getModelByIdFromCache(String id);

    /**
     * Mark default model for a type (isDefault 1 = default, 0 = not).
     */
    void setDefaultModel(String modelType, int isDefault);

    /**
     * TTS providers with id and modelName for pickers.
     */
    List<Map<String, Object>> getTtsPlatformList();

    /**
     * Enabled configurations for a model type (LLM, TTS, ASR, ...).
     */
    List<ModelConfigEntity> getEnabledModelsByType(String modelType);
}
