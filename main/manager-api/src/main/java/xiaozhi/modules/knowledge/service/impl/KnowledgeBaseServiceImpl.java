package xiaozhi.modules.knowledge.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import lombok.AllArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.lang3.StringUtils;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.beans.BeanUtils;
import xiaozhi.common.constant.Constant;
import xiaozhi.common.exception.ErrorCode;
import xiaozhi.common.exception.RenException;
import xiaozhi.common.page.PageData;
import xiaozhi.common.redis.RedisKeys;
import xiaozhi.common.redis.RedisUtils;
import xiaozhi.common.service.impl.BaseServiceImpl;
import xiaozhi.common.utils.ConvertUtils;
import xiaozhi.common.utils.JsonUtils;
import xiaozhi.modules.knowledge.dao.KnowledgeBaseDao;
import xiaozhi.modules.knowledge.dto.KnowledgeBaseDTO;
import xiaozhi.modules.knowledge.dto.dataset.DatasetDTO;
import xiaozhi.modules.knowledge.entity.KnowledgeBaseEntity;
import xiaozhi.modules.knowledge.rag.KnowledgeBaseAdapter;
import xiaozhi.modules.knowledge.rag.KnowledgeBaseAdapterFactory;
import xiaozhi.modules.knowledge.service.KnowledgeBaseService;
import xiaozhi.modules.model.dao.ModelConfigDao;
import xiaozhi.modules.model.entity.ModelConfigEntity;
import xiaozhi.modules.model.service.ModelConfigService;
import xiaozhi.modules.security.user.SecurityUser;

import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import cn.hutool.json.JSONObject;

/**
 * Knowledge base service: RAGFlow adapter + shadow DB.
 */
@Service
@AllArgsConstructor
@Slf4j
public class KnowledgeBaseServiceImpl extends BaseServiceImpl<KnowledgeBaseDao, KnowledgeBaseEntity>
        implements KnowledgeBaseService {

    private final KnowledgeBaseDao knowledgeBaseDao;
    private final ModelConfigService modelConfigService;
    private final ModelConfigDao modelConfigDao;
    private final RedisUtils redisUtils;

    @Override
    public PageData<KnowledgeBaseDTO> getPageList(KnowledgeBaseDTO knowledgeBaseDTO, Integer page, Integer limit) {
        Page<KnowledgeBaseEntity> pageInfo = new Page<>(page, limit);
        QueryWrapper<KnowledgeBaseEntity> queryWrapper = new QueryWrapper<>();

        if (knowledgeBaseDTO != null) {
            queryWrapper.like(StringUtils.isNotBlank(knowledgeBaseDTO.getName()), "name", knowledgeBaseDTO.getName());
            queryWrapper.eq(knowledgeBaseDTO.getStatus() != null, "status", knowledgeBaseDTO.getStatus());
            queryWrapper.eq("creator", knowledgeBaseDTO.getCreator());
        }
        queryWrapper.orderByDesc("created_at");

        IPage<KnowledgeBaseEntity> iPage = knowledgeBaseDao.selectPage(pageInfo, queryWrapper);
        PageData<KnowledgeBaseDTO> pageData = getPageData(iPage, KnowledgeBaseDTO.class);

        // Enrich with Document Count from RAG (Optional / Lazy)
        if (pageData != null && pageData.getList() != null) {
            for (KnowledgeBaseDTO dto : pageData.getList()) {
                enrichDocumentCount(dto);
            }
        }
        return pageData;
    }

    private void enrichDocumentCount(KnowledgeBaseDTO dto) {
        try {
            if (StringUtils.isNotBlank(dto.getDatasetId()) && StringUtils.isNotBlank(dto.getRagModelId())) {
                KnowledgeBaseAdapter adapter = getAdapterByModelId(dto.getRagModelId());
                if (adapter != null) {
                    dto.setDocumentCount(adapter.getDocumentCount(dto.getDatasetId()));
                }
            }
        } catch (Exception e) {
            log.warn("Could not load document count for knowledge base {}: {}", dto.getName(), e.getMessage());
            dto.setDocumentCount(0);
        }
    }

    @Override
    public KnowledgeBaseDTO getById(String id) {
        KnowledgeBaseEntity entity = knowledgeBaseDao.selectById(id);
        if (entity == null) {
            throw new RenException(ErrorCode.Knowledge_Base_RECORD_NOT_EXISTS);
        }
        return ConvertUtils.sourceToTarget(entity, KnowledgeBaseDTO.class);
    }

    @Override
    public KnowledgeBaseDTO getByDatasetId(String datasetId) {
        if (StringUtils.isBlank(datasetId)) {
            throw new RenException(ErrorCode.PARAMS_GET_ERROR);
        }
        // Resolve by dataset_id first, then by primary key id (frontend may send either UUID)
        KnowledgeBaseEntity entity = knowledgeBaseDao
                .selectOne(new QueryWrapper<KnowledgeBaseEntity>()
                        .eq("dataset_id", datasetId)
                        .or()
                        .eq("id", datasetId));
        if (entity == null) {
            throw new RenException(ErrorCode.Knowledge_Base_RECORD_NOT_EXISTS);
        }
        return ConvertUtils.sourceToTarget(entity, KnowledgeBaseDTO.class);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public KnowledgeBaseDTO save(KnowledgeBaseDTO dto) {
        // 1. Validation
        checkDuplicateName(dto.getName(), null);
        KnowledgeBaseAdapter adapter = null;

        // 2. RAG Creation
        String datasetId = null;
        try {
            // Default RAG model when omitted
            if (StringUtils.isBlank(dto.getRagModelId())) {
                List<ModelConfigEntity> models = getRAGModels();
                if (models != null && !models.isEmpty()) {
                    dto.setRagModelId(models.get(0).getId());
                } else {
                    throw new RenException(ErrorCode.RAG_CONFIG_NOT_FOUND,
                            "No RAG model specified and no default RAG model is available");
                }
            }

            Map<String, Object> ragConfig = getValidatedRAGConfig(dto.getRagModelId());
            adapter = KnowledgeBaseAdapterFactory.getAdapter((String) ragConfig.get("type"),
                    ragConfig);

            DatasetDTO.CreateReq createReq = ConvertUtils.sourceToTarget(dto, DatasetDTO.CreateReq.class);
            createReq.setName(SecurityUser.getUser().getUsername() + "_" + dto.getName());

            DatasetDTO.InfoVO ragResponse = adapter.createDataset(createReq);
            if (ragResponse == null || StringUtils.isBlank(ragResponse.getId())) {
                throw new RenException(ErrorCode.RAG_API_ERROR, "RAG create response invalid: missing id");
            }
            datasetId = ragResponse.getId();

            // 3. Local Save (Shadow)
            KnowledgeBaseEntity entity = ConvertUtils.sourceToTarget(dto, KnowledgeBaseEntity.class);

            // Use same id locally as RAGFlow dataset id to avoid 10163 on delete/update
            entity.setId(datasetId);
            entity.setDatasetId(datasetId);
            entity.setStatus(1); // Default Enabled

            // Persist full RAG response via typed fields
            entity.setTenantId(ragResponse.getTenantId());
            entity.setChunkMethod(ragResponse.getChunkMethod());
            entity.setEmbeddingModel(ragResponse.getEmbeddingModel());
            entity.setPermission(ragResponse.getPermission());

            if (StringUtils.isBlank(entity.getAvatar())) {
                entity.setAvatar(ragResponse.getAvatar());
            }

            // Parse Config (JSON)
            if (ragResponse.getParserConfig() != null) {
                entity.setParserConfig(JsonUtils.toJsonString(ragResponse.getParserConfig()));
            }

            // Numeric fields
            entity.setChunkCount(ragResponse.getChunkCount() != null ? ragResponse.getChunkCount() : 0L);
            entity.setDocumentCount(ragResponse.getDocumentCount() != null ? ragResponse.getDocumentCount() : 0L);
            entity.setTokenNum(ragResponse.getTokenNum() != null ? ragResponse.getTokenNum() : 0L);

            // Clear so MyBatis meta handler fills creator/updater from SecurityUser
            entity.setCreator(null);
            entity.setUpdater(null);

            knowledgeBaseDao.insert(entity);
            return ConvertUtils.sourceToTarget(entity, KnowledgeBaseDTO.class);
        } catch (Exception e) {
            log.error("RAG create or local save failed", e);
            // Best-effort RAG rollback if dataset was created
            if (StringUtils.isNotBlank(datasetId)) {
                try {
                    if (adapter != null)
                        adapter.deleteDataset(
                                DatasetDTO.BatchIdReq.builder().ids(Collections.singletonList(datasetId)).build());
                } catch (Exception rollbackEx) {
                    log.error("RAG rollback failed for datasetId={}", datasetId, rollbackEx);
                }
            }
            if (e instanceof RenException) {
                throw (RenException) e;
            }
            throw new RenException(ErrorCode.RAG_API_ERROR, "Failed to create knowledge base: " + e.getMessage());
        }
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    @SuppressWarnings("deprecation")
    public KnowledgeBaseDTO update(KnowledgeBaseDTO dto) {
        log.info("Update Service Called: ID={}, DatasetID={}", dto.getId(), dto.getDatasetId());
        KnowledgeBaseEntity entity = knowledgeBaseDao.selectById(dto.getId());
        if (entity == null) {
            log.error("Update failed: Entity not found for ID={}", dto.getId());
            throw new RenException(ErrorCode.Knowledge_Base_RECORD_NOT_EXISTS);
        }

        checkDuplicateName(dto.getName(), dto.getId());

        // dataset_id must stay unique
        if (StringUtils.isNotBlank(dto.getDatasetId())) {
            KnowledgeBaseEntity conflictEntity = knowledgeBaseDao.selectOne(
                    new QueryWrapper<KnowledgeBaseEntity>()
                            .eq("dataset_id", dto.getDatasetId())
                            .ne("id", dto.getId()));
            if (conflictEntity != null) {
                throw new RenException(ErrorCode.DB_RECORD_EXISTS);
            }
        }

        // RAG Update if needed
        if (StringUtils.isNotBlank(entity.getDatasetId()) && StringUtils.isNotBlank(dto.getRagModelId())) {
            try {
                // Backfill ragModelId from entity if missing on DTO
                if (StringUtils.isBlank(dto.getRagModelId())) {
                    dto.setRagModelId(entity.getRagModelId());
                }

                // Merge missing fields from stored entity for partial updates to RAGFlow
                if (StringUtils.isBlank(dto.getPermission())) {
                    dto.setPermission(entity.getPermission());
                }
                if (StringUtils.isBlank(dto.getChunkMethod())) {
                    dto.setChunkMethod(entity.getChunkMethod());
                }

                KnowledgeBaseAdapter adapter = getAdapterByModelId(dto.getRagModelId());
                if (adapter != null) {
                    DatasetDTO.UpdateReq updateReq = ConvertUtils.sourceToTarget(dto, DatasetDTO.UpdateReq.class);

                    // Prefix dataset name with username (product rule)
                    if (StringUtils.isNotBlank(dto.getName())) {
                        updateReq.setName(SecurityUser.getUser().getUsername() + "_" + dto.getName());
                    }

                    // Optional parser_config JSON string on DTO
                    if (StringUtils.isNotBlank(dto.getParserConfig())) {
                        try {
                            DatasetDTO.ParserConfig parserConfig = JsonUtils.parseObject(dto.getParserConfig(),
                                    DatasetDTO.ParserConfig.class);
                            updateReq.setParserConfig(parserConfig);
                        } catch (Exception e) {
                            log.warn("parser_config parse failed; skipping RAG parser_config sync", e);
                        }
                    }

                    adapter.updateDataset(entity.getDatasetId(), updateReq);
                    log.info("RAG dataset updated: {}", entity.getDatasetId());
                }
            } catch (Exception e) {
                log.error("RAG dataset update failed", e);
                // Transaction rolls back on failure
                if (e instanceof RenException) {
                    throw (RenException) e;
                }
                throw new RenException(ErrorCode.RAG_API_ERROR, "RAG update failed: " + e.getMessage());
            }
        }

        BeanUtils.copyProperties(dto, entity);
        knowledgeBaseDao.updateById(entity);

        // Clean cache
        redisUtils.delete(RedisKeys.getKnowledgeBaseCacheKey(entity.getId()));

        return ConvertUtils.sourceToTarget(entity, KnowledgeBaseDTO.class);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void deleteByDatasetId(String datasetId) {
        if (StringUtils.isBlank(datasetId)) {
            throw new RenException(ErrorCode.PARAMS_GET_ERROR);
        }

        KnowledgeBaseEntity entity = knowledgeBaseDao
                .selectOne(new QueryWrapper<KnowledgeBaseEntity>().eq("dataset_id", datasetId));

        if (entity == null) {
            log.warn("No knowledge base row for datasetId: {}", datasetId);
            throw new RenException(ErrorCode.Knowledge_Base_RECORD_NOT_EXISTS);
        }
        log.info("Resolved row: id={}, datasetId={}, ragModelId={}",
                entity.getId(), entity.getDatasetId(), entity.getRagModelId());

        // RAG delete must succeed before local delete (strict consistency)
        boolean apiDeleteSuccess = false;
        if (StringUtils.isNotBlank(entity.getRagModelId()) && StringUtils.isNotBlank(entity.getDatasetId())) {
            try {
                KnowledgeBaseAdapter adapter = getAdapterByModelId(entity.getRagModelId());
                if (adapter != null) {
                    adapter.deleteDataset(
                            DatasetDTO.BatchIdReq.builder().ids(Collections.singletonList(datasetId)).build());
                }
                apiDeleteSuccess = true;
            } catch (Exception e) {
                log.error("RAG delete failed; rolling back", e);
                if (e instanceof RenException) {
                    throw (RenException) e;
                }
                throw new RenException(ErrorCode.RAG_API_ERROR, "RAG delete failed: " + e.getMessage());
            }
        } else {
            log.warn("datasetId or ragModelId empty; skipping RAG delete");
            apiDeleteSuccess = true;
        }

        if (apiDeleteSuccess) {
            log.info("Deleting ai_agent_plugin_mapping rows for knowledgeBaseId={}", entity.getId());
            log.info("Deleting related rows, entityId={}", entity.getId());
            knowledgeBaseDao.deletePluginMappingByKnowledgeBaseId(entity.getId());
            log.info("Plugin mapping rows removed");
            int deleteCount = knowledgeBaseDao.deleteById(entity.getId());
            log.info("Local knowledge base row deleted: {}", deleteCount > 0);
            redisUtils.delete(RedisKeys.getKnowledgeBaseCacheKey(entity.getId()));
        }
    }

    @Override
    public List<KnowledgeBaseDTO> getByDatasetIdList(List<String> datasetIdList) {
        if (datasetIdList == null || datasetIdList.isEmpty()) {
            return Collections.emptyList();
        }
        // Match either dataset_id or local id column
        QueryWrapper<KnowledgeBaseEntity> queryWrapper = new QueryWrapper<>();
        queryWrapper.in("dataset_id", datasetIdList).or().in("id", datasetIdList);
        List<KnowledgeBaseEntity> list = knowledgeBaseDao.selectList(queryWrapper);
        return ConvertUtils.sourceToTarget(list, KnowledgeBaseDTO.class);
    }

    @Override
    public Map<String, Object> getRAGConfig(String ragModelId) {
        return getValidatedRAGConfig(ragModelId);
    }

    @Override
    public Map<String, Object> getRAGConfigByDatasetId(String datasetId) {
        KnowledgeBaseEntity entity = knowledgeBaseDao
                .selectOne(new QueryWrapper<KnowledgeBaseEntity>().eq("dataset_id", datasetId));
        if (entity == null || StringUtils.isBlank(entity.getRagModelId())) {
            throw new RenException(ErrorCode.RAG_CONFIG_NOT_FOUND);
        }
        return getRAGConfig(entity.getRagModelId());
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void updateStatistics(String datasetId, Integer docDelta, Long chunkDelta, Long tokenDelta) {
        log.info("Adjust knowledge base stats: datasetId={}, docs={}, chunks={}, tokens={}", datasetId, docDelta,
                chunkDelta, tokenDelta);
        knowledgeBaseDao.updateStatsAfterChange(datasetId, docDelta, chunkDelta, tokenDelta);
    }

    @Override
    public List<ModelConfigEntity> getRAGModels() {
        List<ModelConfigEntity> models = modelConfigDao.selectList(new QueryWrapper<ModelConfigEntity>()
                .select("id", "model_name", "config_json") // Explicitly select needed fields
                .eq("model_type", Constant.RAG_CONFIG_TYPE)
                .eq("is_enabled", 1)
                .orderByDesc("is_default")
                .orderByDesc("create_date"));
        for (ModelConfigEntity model : models) {
            if (model.getConfigJson() != null) {
                fillEmbeddingCredential(model.getConfigJson());
            }
        }
        return models;
    }

    // --- Helpers ---

    private void checkDuplicateName(String name, String excludeId) {
        if (StringUtils.isBlank(name))
            return;
        QueryWrapper<KnowledgeBaseEntity> qw = new QueryWrapper<>();
        qw.eq("name", name).eq("creator", SecurityUser.getUserId());
        if (excludeId != null)
            qw.ne("id", excludeId);
        if (knowledgeBaseDao.selectCount(qw) > 0) {
            throw new RenException(ErrorCode.KNOWLEDGE_BASE_NAME_EXISTS);
        }
    }

    private KnowledgeBaseAdapter getAdapterByModelId(String modelId) {
        Map<String, Object> config = getValidatedRAGConfig(modelId);
        return KnowledgeBaseAdapterFactory.getAdapter((String) config.get("type"), config);
    }

    private Map<String, Object> getValidatedRAGConfig(String modelId) {
        ModelConfigEntity configEntity = modelConfigService.getModelByIdFromCache(modelId);
        if (configEntity == null || configEntity.getConfigJson() == null) {
            throw new RenException(ErrorCode.RAG_CONFIG_NOT_FOUND);
        }
        Map<String, Object> config = new HashMap<>(configEntity.getConfigJson());
        fillEmbeddingCredential(config);

        // Infer adapter type safely when legacy records do not have explicit "type"
        if (!config.containsKey("type") || StringUtils.isBlank((String) config.get("type"))) {
            // Qdrant-like config: has url + collection_name (+ optional embedding_model/vector_size)
            if (config.containsKey("url") && config.containsKey("collection_name")) {
                config.put("type", "qdrant");
            } else {
                // Keep backward compatibility for old RAGFlow configs
                config.put("type", "ragflow");
            }
        }

        return config;
    }

    /**
     * Auto-fill embedding API key from enabled LLM configs when missing.
     * Priority:
     * - embedding_provider=gemini -> key from enabled Gemini LLM model
     * - embedding_provider=openai -> key from enabled OpenAI LLM model
     */
    private void fillEmbeddingCredential(Map<String, Object> ragConfig) {
        if (ragConfig == null) {
            return;
        }
        String provider = String.valueOf(ragConfig.getOrDefault("embedding_provider", "")).toLowerCase();
        if ("gemini".equals(provider)) {
            String existing = String.valueOf(ragConfig.getOrDefault("gemini_api_key", ""));
            if (StringUtils.isBlank(existing)) {
                String key = resolveApiKeyFromEnabledLlm("gemini");
                if (StringUtils.isNotBlank(key)) {
                    ragConfig.put("gemini_api_key", key);
                }
            }
        } else if ("openai".equals(provider)) {
            String existing = String.valueOf(ragConfig.getOrDefault("openai_api_key", ""));
            if (StringUtils.isBlank(existing)) {
                String key = resolveApiKeyFromEnabledLlm("openai");
                if (StringUtils.isNotBlank(key)) {
                    ragConfig.put("openai_api_key", key);
                }
            }
        }
    }

    private String resolveApiKeyFromEnabledLlm(String llmType) {
        List<ModelConfigEntity> llmModels = modelConfigDao.selectList(
                new QueryWrapper<ModelConfigEntity>()
                        .select("id", "config_json", "is_default", "create_date")
                        .eq("model_type", "LLM")
                        .eq("is_enabled", 1)
                        .orderByDesc("is_default")
                        .orderByDesc("create_date"));
        for (ModelConfigEntity llm : llmModels) {
            JSONObject cfg = llm.getConfigJson();
            if (cfg == null) {
                continue;
            }
            String type = String.valueOf(cfg.getOrDefault("type", "")).toLowerCase();
            if (!llmType.equals(type)) {
                continue;
            }
            String apiKey = String.valueOf(cfg.getOrDefault("api_key", ""));
            if (StringUtils.isNotBlank(apiKey)) {
                return apiKey;
            }
        }
        return "";
    }
}