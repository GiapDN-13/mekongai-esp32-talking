package xiaozhi.modules.knowledge.service;

import java.util.List;
import java.util.Map;

import xiaozhi.common.page.PageData;
import xiaozhi.common.service.BaseService;
import xiaozhi.modules.knowledge.dto.KnowledgeBaseDTO;
import xiaozhi.modules.knowledge.entity.KnowledgeBaseEntity;
import xiaozhi.modules.model.entity.ModelConfigEntity;

/**
 * Knowledge base (dataset) service.
 */
public interface KnowledgeBaseService extends BaseService<KnowledgeBaseEntity> {

    /**
     * Paged list with filters.
     */
    PageData<KnowledgeBaseDTO> getPageList(KnowledgeBaseDTO knowledgeBaseDTO, Integer page, Integer limit);

    /**
     * Detail by primary key {@code id}.
     */
    KnowledgeBaseDTO getById(String id);

    /**
     * Create dataset in RAG and persist shadow row.
     */
    KnowledgeBaseDTO save(KnowledgeBaseDTO knowledgeBaseDTO);

    /**
     * Update local row and sync to RAG when applicable.
     */
    KnowledgeBaseDTO update(KnowledgeBaseDTO knowledgeBaseDTO);

    /**
     * Lookup by RAG dataset id (also accepts local row id for compatibility).
     */
    KnowledgeBaseDTO getByDatasetId(String datasetId);

    /**
     * Batch lookup by dataset ids (or local ids).
     */
    List<KnowledgeBaseDTO> getByDatasetIdList(List<String> datasetIdList);

    /**
     * Delete by dataset id (RAG + local, transactional).
     */
    void deleteByDatasetId(String datasetId);

    /**
     * Resolved RAG adapter config for a model config id.
     */
    Map<String, Object> getRAGConfig(String ragModelId);

    /**
     * RAG config for the model bound to the given dataset.
     */
    Map<String, Object> getRAGConfigByDatasetId(String datasetId);

    /**
     * Enabled RAG model definitions.
     */
    List<ModelConfigEntity> getRAGModels();

    /**
     * Apply counter deltas after document changes (callbacks from file service).
     */
    void updateStatistics(String datasetId, Integer docDelta, Long chunkDelta, Long tokenDelta);
}
