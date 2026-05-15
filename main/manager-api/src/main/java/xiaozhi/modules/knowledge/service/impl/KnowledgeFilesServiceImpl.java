package xiaozhi.modules.knowledge.service.impl;

import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Map;

import org.apache.commons.lang3.StringUtils;
import org.springframework.beans.BeanUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Lazy;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.UpdateWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;

import lombok.extern.slf4j.Slf4j;
import xiaozhi.common.exception.ErrorCode;
import org.springframework.util.CollectionUtils;
import xiaozhi.common.exception.RenException;
import xiaozhi.modules.knowledge.dto.KnowledgeFilesDTO;
import xiaozhi.modules.knowledge.dto.document.ChunkDTO;
import xiaozhi.modules.knowledge.dto.document.RetrievalDTO;
import xiaozhi.modules.knowledge.dto.document.DocumentDTO;
import xiaozhi.common.page.PageData;
import xiaozhi.common.redis.RedisKeys;
import xiaozhi.common.redis.RedisUtils;
import xiaozhi.common.service.impl.BaseServiceImpl;
import xiaozhi.modules.knowledge.dao.DocumentDao;
import xiaozhi.modules.knowledge.entity.DocumentEntity;
import xiaozhi.modules.knowledge.rag.KnowledgeBaseAdapter;
import xiaozhi.modules.knowledge.rag.KnowledgeBaseAdapterFactory;
import xiaozhi.modules.knowledge.service.KnowledgeBaseService;
import xiaozhi.modules.knowledge.service.KnowledgeFilesService;

@Service
@Slf4j
public class KnowledgeFilesServiceImpl extends BaseServiceImpl<DocumentDao, DocumentEntity>
        implements KnowledgeFilesService {

    private final KnowledgeBaseService knowledgeBaseService;
    private final DocumentDao documentDao;
    private final ObjectMapper objectMapper;
    private final RedisUtils redisUtils;

    public KnowledgeFilesServiceImpl(KnowledgeBaseService knowledgeBaseService,
            DocumentDao documentDao,
            ObjectMapper objectMapper,
            RedisUtils redisUtils) {
        this.knowledgeBaseService = knowledgeBaseService;
        this.documentDao = documentDao;
        this.objectMapper = objectMapper;
        this.redisUtils = redisUtils;
    }

    @Lazy
    @Autowired
    private KnowledgeFilesService self;

    @Override
    public Map<String, Object> getRAGConfig(String ragModelId) {
        return knowledgeBaseService.getRAGConfig(ragModelId);
    }

    @Override
    public PageData<KnowledgeFilesDTO> getPageList(KnowledgeFilesDTO knowledgeFilesDTO, Integer page, Integer limit) {
        log.info("=== Fetch document list (local-first) ===");
        String datasetId = knowledgeFilesDTO.getDatasetId();
        if (StringUtils.isBlank(datasetId)) {
            throw new RenException(ErrorCode.RAG_DATASET_ID_AND_MODEL_ID_NOT_NULL);
        }

        // Local shadow table (paged)
        Page<DocumentEntity> pageParams = new Page<>(page, limit);
        QueryWrapper<DocumentEntity> queryWrapper = new QueryWrapper<>();
        queryWrapper.eq("dataset_id", datasetId);
        if (StringUtils.isNotBlank(knowledgeFilesDTO.getName())) {
            queryWrapper.like("name", knowledgeFilesDTO.getName());
        }
        if (StringUtils.isNotBlank(knowledgeFilesDTO.getRun())) {
            queryWrapper.eq("run", knowledgeFilesDTO.getRun());
        }
        if (StringUtils.isNotBlank(knowledgeFilesDTO.getStatus())) {
            queryWrapper.eq("status", knowledgeFilesDTO.getStatus());
        }
        queryWrapper.orderByDesc("created_at");

        // Query DB
        Page<DocumentEntity> iPage = documentDao.selectPage(pageParams, queryWrapper);

        // Map to DTOs
        List<KnowledgeFilesDTO> dtoList = new ArrayList<>();
        for (DocumentEntity entity : iPage.getRecords()) {
            dtoList.add(convertEntityToDTO(entity));
        }
        PageData<KnowledgeFilesDTO> pageData = new PageData<>(dtoList, iPage.getTotal());

        // Opportunistic RAG sync (rate-limited); CANCEL/FAIL get slow-path recovery sync
        if (pageData.getList() != null && !pageData.getList().isEmpty()) {
            KnowledgeBaseAdapter adapter = null;
            for (KnowledgeFilesDTO dto : pageData.getList()) {
                String runStatus = dto.getRun();
                // Hot path: RUNNING/UNSTART (5s cooldown)
                boolean isActiveSync = "RUNNING".equals(runStatus) || "UNSTART".equals(runStatus);
                // Recovery: CANCEL/FAIL (60s cooldown)
                boolean isRecoverySync = "CANCEL".equals(runStatus) || "FAIL".equals(runStatus);
                boolean needSync = isActiveSync || isRecoverySync;

                if (needSync) {
                    // Cooldown: 5s active / 60s recovery
                    long cooldownMs = isActiveSync ? 5000 : 60000;
                    DocumentEntity localEntity = documentDao.selectOne(new QueryWrapper<DocumentEntity>()
                            .eq("document_id", dto.getDocumentId()));
                    if (localEntity != null && localEntity.getLastSyncAt() != null) {
                        long diff = System.currentTimeMillis() - localEntity.getLastSyncAt().getTime();
                        if (diff < cooldownMs) {
                            continue;
                        }
                    }

                    // Lazy-init adapter once per page batch
                    if (adapter == null) {
                        try {
                            Map<String, Object> ragConfig = knowledgeBaseService.getRAGConfigByDatasetId(datasetId);
                            adapter = KnowledgeBaseAdapterFactory.getAdapter(extractAdapterType(ragConfig), ragConfig);
                        } catch (Exception e) {
                            log.warn("Sync aborted: adapter init failed: {}", e.getMessage());
                            break;
                        }
                    }
                    // Token delta vs pre-sync DTO
                    Long oldTokenCount = dto.getTokenCount() != null ? dto.getTokenCount() : 0L;

                    syncDocumentStatusWithRAG(dto, adapter);

                    // Reconcile dataset token stats (same as scheduled job)
                    Long newTokenCount = dto.getTokenCount() != null ? dto.getTokenCount() : 0L;
                    Long tokenDelta = newTokenCount - oldTokenCount;
                    if (tokenDelta != 0) {
                        knowledgeBaseService.updateStatistics(datasetId, 0, 0L, tokenDelta);
                        log.info("Lazy sync: adjust dataset stats, docId={}, tokenDelta={}", dto.getDocumentId(),
                                tokenDelta);
                    }
                }
            }
        }

        log.info("Document list loaded, total={}", pageData.getTotal());
        return pageData;
    }

    /** Map entity to API DTO (size→fileSize, type→fileType). */
    private KnowledgeFilesDTO convertEntityToDTO(DocumentEntity entity) {
        if (entity == null) {
            return null;
        }
        KnowledgeFilesDTO dto = new KnowledgeFilesDTO();
        // Base fields
        BeanUtils.copyProperties(entity, dto);

        // Expose remote documentId as DTO id for UI operations
        dto.setId(entity.getDocumentId());

        // Aliases
        dto.setFileSize(entity.getSize());
        dto.setFileType(entity.getType());
        dto.setRun(entity.getRun());
        dto.setChunkCount(entity.getChunkCount());
        dto.setTokenCount(entity.getTokenCount());
        dto.setError(entity.getError());

        // meta_fields JSON
        if (StringUtils.isNotBlank(entity.getMetaFields())) {
            try {
                dto.setMetaFields(objectMapper.readValue(entity.getMetaFields(),
                        new TypeReference<Map<String, Object>>() {
                        }));
            } catch (Exception e) {
                log.warn("meta_fields deserialize failed, entityId: {}, error: {}", entity.getId(), e.getMessage());
            }
        }

        // parser_config JSON
        if (StringUtils.isNotBlank(entity.getParserConfig())) {
            try {
                dto.setParserConfig(objectMapper.readValue(entity.getParserConfig(),
                        new com.fasterxml.jackson.core.type.TypeReference<Map<String, Object>>() {
                        }));
            } catch (Exception e) {
                log.warn("parser_config deserialize failed, entityId: {}, error: {}", entity.getId(), e.getMessage());
            }
        }
        return dto;

    }

    /** Pull remote document row into shadow DB; optional pre-built adapter. */
    private void syncDocumentStatusWithRAG(KnowledgeFilesDTO dto, KnowledgeBaseAdapter adapter) {
        if (dto == null || StringUtils.isBlank(dto.getDocumentId()) || adapter == null) {
            return;
        }

        String documentId = dto.getDocumentId();
        String datasetId = dto.getDatasetId();

        try {
            // Single-doc filter via ListReq
            DocumentDTO.ListReq listReq = DocumentDTO.ListReq.builder()
                    .id(documentId)
                    .page(1)
                    .pageSize(1)
                    .build();

            PageData<KnowledgeFilesDTO> remoteList = adapter.getDocumentList(datasetId, listReq);

            if (remoteList != null && remoteList.getList() != null && !remoteList.getList().isEmpty()) {
                KnowledgeFilesDTO remoteDto = remoteList.getList().get(0);
                String remoteStatus = remoteDto.getStatus();

                // Diff detection
                boolean statusChanged = remoteStatus != null && !remoteStatus.equals(dto.getStatus());
                boolean runChanged = remoteDto.getRun() != null && !remoteDto.getRun().equals(dto.getRun());
                boolean isProcessing = "RUNNING".equals(remoteDto.getRun()) || "UNSTART".equals(remoteDto.getRun());

                if (statusChanged || runChanged || isProcessing) {
                    log.info("Shadow sync: statusChanged={}, processing={}, doc={}, remoteStatus={}, progress={}",
                            statusChanged, isProcessing, documentId, remoteStatus, remoteDto.getProgress());

                    dto.setStatus(remoteStatus);
                    dto.setRun(remoteDto.getRun());
                    dto.setProgress(remoteDto.getProgress());
                    dto.setChunkCount(remoteDto.getChunkCount());
                    dto.setTokenCount(remoteDto.getTokenCount());
                    dto.setError(remoteDto.getError());
                    dto.setProcessDuration(remoteDto.getProcessDuration());
                    dto.setThumbnail(remoteDto.getThumbnail());

                    // Persist shadow row
                    UpdateWrapper<DocumentEntity> updateWrapper = new UpdateWrapper<DocumentEntity>()
                            .set("status", remoteStatus)
                            .set("run", remoteDto.getRun())
                            .set("progress", remoteDto.getProgress())
                            .set("chunk_count", remoteDto.getChunkCount())
                            .set("token_count", remoteDto.getTokenCount())
                            .set("error", remoteDto.getError())
                            .set("process_duration", remoteDto.getProcessDuration())
                            .set("thumbnail", remoteDto.getThumbnail())
                            .eq("document_id", documentId)
                            .eq("dataset_id", datasetId);

                    // meta_fields column
                    if (remoteDto.getMetaFields() != null) {
                        try {
                            updateWrapper.set("meta_fields",
                                    objectMapper.writeValueAsString(remoteDto.getMetaFields()));
                        } catch (Exception e) {
                            log.warn("meta_fields serialize failed: {}", e.getMessage());
                        }
                    }

                    // Prefer RAG updated_at
                    Date lastUpdate = remoteDto.getUpdatedAt() != null ? remoteDto.getUpdatedAt() : new Date();
                    updateWrapper.set("updated_at", lastUpdate);
                    updateWrapper.set("last_sync_at", new Date());

                    documentDao.update(null, updateWrapper);
                }
            } else {
                log.warn("RAG returned empty document list; marking CANCEL, docId={}, localRun={}",
                        documentId, dto.getRun());
                dto.setRun("CANCEL");
                dto.setError("Document was removed on RAG service");

                documentDao.update(null, new UpdateWrapper<DocumentEntity>()
                        .set("run", "CANCEL")
                        .set("error", "Document was removed on RAG service")
                        .set("updated_at", new Date())
                        .set("last_sync_at", new Date())
                        .eq("document_id", documentId));
            }
        } catch (Exception e) {
            log.warn("Adapter error during status sync (not marking CANCEL), documentId: {}, error: {}",
                    documentId, e.getMessage());
        }
    }

    @Override
    public DocumentDTO.InfoVO getByDocumentId(String documentId, String datasetId) {
        if (StringUtils.isBlank(documentId) || StringUtils.isBlank(datasetId)) {
            throw new RenException(ErrorCode.RAG_DATASET_ID_AND_MODEL_ID_NOT_NULL);
        }

        log.info("=== getDocumentById start ===");
        log.info("documentId: {}, datasetId: {}", documentId, datasetId);

        try {
            // RAG config
            Map<String, Object> ragConfig = knowledgeBaseService.getRAGConfigByDatasetId(datasetId);

            // Adapter type
            String adapterType = extractAdapterType(ragConfig);

            // Factory
            KnowledgeBaseAdapter adapter = KnowledgeBaseAdapterFactory.getAdapter(adapterType, ragConfig);

            // Remote detail
            DocumentDTO.InfoVO info = adapter.getDocumentById(datasetId, documentId);

            if (info != null) {
                log.info("Document detail OK, documentId: {}", documentId);
                return info;
            } else {
                throw new RenException(ErrorCode.Knowledge_Base_RECORD_NOT_EXISTS);
            }

        } catch (Exception e) {
            log.error("getDocumentById failed: {}", e.getMessage(), e);
            String errorMessage = e.getMessage() != null ? e.getMessage() : "null";
            if (e instanceof RenException) {
                throw (RenException) e;
            }
            throw new RenException(ErrorCode.RAG_API_ERROR, errorMessage);
        } finally {
            log.info("=== getDocumentById end ===");
        }
    }

    @Override
    public KnowledgeFilesDTO uploadDocument(String datasetId, MultipartFile file, String name,
            Map<String, Object> metaFields, String chunkMethod,
            Map<String, Object> parserConfig) {
        if (StringUtils.isBlank(datasetId) || file == null || file.isEmpty()) {
            throw new RenException(ErrorCode.PARAMS_GET_ERROR);
        }

        log.info("=== uploadDocument (strong consistency) ===");

        String fileName = StringUtils.isNotBlank(name) ? name : file.getOriginalFilename();
        if (StringUtils.isBlank(fileName)) {
            throw new RenException(ErrorCode.RAG_FILE_NAME_NOT_NULL);
        }

        log.info("1. Remote upload: datasetId={}, fileName={}", datasetId, fileName);

        Map<String, Object> ragConfig = knowledgeBaseService.getRAGConfigByDatasetId(datasetId);
        KnowledgeBaseAdapter adapter = KnowledgeBaseAdapterFactory.getAdapter(extractAdapterType(ragConfig), ragConfig);

        // Typed upload request
        DocumentDTO.UploadReq uploadReq = DocumentDTO.UploadReq.builder()
                .datasetId(datasetId)
                .file(file)
                .name(fileName)
                .metaFields(metaFields)
                .build();

        // chunk_method enum
        if (StringUtils.isNotBlank(chunkMethod)) {
            try {
                uploadReq.setChunkMethod(DocumentDTO.InfoVO.ChunkMethod.valueOf(chunkMethod.toUpperCase()));
            } catch (Exception e) {
                log.warn("Invalid chunk_method: {}, using default", chunkMethod);
            }
        }

        // parser_config map → DTO
        if (parserConfig != null && !parserConfig.isEmpty()) {
            uploadReq.setParserConfig(objectMapper.convertValue(parserConfig, DocumentDTO.InfoVO.ParserConfig.class));
        }

        // Remote IO outside transaction
        KnowledgeFilesDTO result = adapter.uploadDocument(uploadReq);

        if (result == null || StringUtils.isBlank(result.getDocumentId())) {
            throw new RenException(ErrorCode.RAG_API_ERROR, "Upload succeeded but document id is missing");
        }

        // 2) Local shadow insert (self-invoke for @Transactional)
        log.info("2. Save shadow row: documentId={}", result.getDocumentId());
        self.saveDocumentShadow(datasetId, result, fileName, chunkMethod, parserConfig);

        log.info("=== upload + shadow save OK ===");
        return result;
    }

    /**
     * Transactional shadow insert for upload result.
     */
    @Transactional(rollbackFor = Exception.class)
    public void saveDocumentShadow(String datasetId, KnowledgeFilesDTO result, String originalName, String chunkMethod,
            Map<String, Object> parserConfig) {
        DocumentEntity entity = new DocumentEntity();
        entity.setDatasetId(datasetId);
        entity.setDocumentId(result.getDocumentId());
        entity.setName(StringUtils.isNotBlank(result.getName()) ? result.getName() : originalName);
        entity.setSize(result.getFileSize());
        entity.setType(getFileType(entity.getName()));
        entity.setChunkMethod(chunkMethod);

        if (parserConfig != null) {
            try {
                entity.setParserConfig(objectMapper.writeValueAsString(parserConfig));
            } catch (Exception e) {
                log.warn("parser_config serialize failed: {}", e.getMessage());
            }
        }

        entity.setStatus(result.getStatus() != null ? result.getStatus() : "1");
        entity.setRun(result.getRun());
        entity.setProgress(result.getProgress());
        entity.setThumbnail(result.getThumbnail());
        entity.setProcessDuration(result.getProcessDuration());
        entity.setSourceType(result.getSourceType());
        entity.setError(result.getError());
        entity.setChunkCount(result.getChunkCount());
        entity.setTokenCount(result.getTokenCount());
        entity.setEnabled(1);

        // meta_fields column
        if (result.getMetaFields() != null) {
            try {
                entity.setMetaFields(objectMapper.writeValueAsString(result.getMetaFields()));
            } catch (Exception e) {
                log.warn("Shadow meta_fields persist failed: {}", e.getMessage());
            }
        }

        // Timestamps: prefer RAG
        entity.setCreatedAt(result.getCreatedAt() != null ? result.getCreatedAt() : new Date());
        entity.setUpdatedAt(result.getUpdatedAt() != null ? result.getUpdatedAt() : new Date());

        // Insert shadow (fail fast for local-first UX)
        documentDao.insert(entity);

        // Bump dataset document_count
        knowledgeBaseService.updateStatistics(datasetId, 1, 0L, 0L);
        log.info("Dataset doc count incremented: datasetId={}", datasetId);
    }

    @Override
    @Transactional(propagation = Propagation.NOT_SUPPORTED)
    public void deleteDocuments(String datasetId, DocumentDTO.BatchIdReq req) {
        if (StringUtils.isBlank(datasetId) || req == null || req.getIds() == null || req.getIds().isEmpty()) {
            throw new RenException(ErrorCode.RAG_DATASET_ID_AND_MODEL_ID_NOT_NULL);
        }

        List<String> documentIds = req.getIds();
        log.info("=== batch delete documents: datasetId={}, count={} ===", datasetId, documentIds.size());

        // Preflight: ownership + run state
        List<DocumentEntity> entities = documentDao.selectList(
                new QueryWrapper<DocumentEntity>()
                        .eq("dataset_id", datasetId)
                        .in("document_id", documentIds));

        if (entities.size() != documentIds.size()) {
            log.warn("Some documents missing or wrong dataset: expected={}, actual={}", documentIds.size(),
                    entities.size());
            throw new RenException(ErrorCode.NO_PERMISSION);
        }

        long totalChunkDelta = 0;
        long totalTokenDelta = 0;

        for (DocumentEntity entity : entities) {
            // Block delete while parsing (use run=RUNNING, not status=1)
            if ("RUNNING".equals(entity.getRun())) {
                log.warn("Reject delete while parsing: docId={}", entity.getDocumentId());
                throw new RenException(ErrorCode.RAG_DOCUMENT_PARSING_DELETE_ERROR);
            }
            totalChunkDelta += entity.getChunkCount() != null ? entity.getChunkCount() : 0L;
            totalTokenDelta += entity.getTokenCount() != null ? entity.getTokenCount() : 0L;
        }

        // Adapter (outside TX)
        Map<String, Object> ragConfig = knowledgeBaseService.getRAGConfigByDatasetId(datasetId);
        KnowledgeBaseAdapter adapter = KnowledgeBaseAdapterFactory.getAdapter(extractAdapterType(ragConfig), ragConfig);

        // Remote delete
        try {
            adapter.deleteDocument(datasetId, req);
            log.info("Remote batch delete OK");
        } catch (Exception e) {
            log.warn("Remote batch delete partial/full failure: {}", e.getMessage());
        }

        // Shadow delete + stats
        self.deleteDocumentShadows(documentIds, datasetId, totalChunkDelta, totalTokenDelta);

        // Cache eviction
        try {
            String cacheKey = RedisKeys.getKnowledgeBaseCacheKey(datasetId);
            redisUtils.delete(cacheKey);
            log.info("Evicted dataset cache: {}", cacheKey);
        } catch (Exception e) {
            log.warn("Redis cache eviction failed: {}", e.getMessage());
        }

        log.info("=== batch document cleanup done ===");
    }

    /**
     * Delete shadow rows and decrement dataset counters.
     */
    @Transactional(rollbackFor = Exception.class)
    public void deleteDocumentShadows(List<String> documentIds, String datasetId, Long chunkDelta, Long tokenDelta) {
        // Physical delete
        int deleted = documentDao.delete(
                new QueryWrapper<DocumentEntity>()
                        .eq("dataset_id", datasetId)
                        .in("document_id", documentIds));

        if (deleted > 0) {
            // Dataset stats
            knowledgeBaseService.updateStatistics(datasetId, -documentIds.size(), -chunkDelta, -tokenDelta);
            log.info("Dataset stats decremented: datasetId={}, chunks={}, tokens={}", datasetId, chunkDelta,
                    tokenDelta);
        }
    }

    /**
     * Infer RAG document category from filename.
     */
    private String getFileType(String fileName) {
        if (StringUtils.isBlank(fileName)) {
            log.warn("Empty filename; type=unknown");
            return "unknown";
        }

        try {
            int lastDotIndex = fileName.lastIndexOf('.');
            if (lastDotIndex > 0 && lastDotIndex < fileName.length() - 1) {
                String extension = fileName.substring(lastDotIndex + 1).toLowerCase();

                // doc
                String[] documentTypes = { "pdf", "doc", "docx", "txt", "md", "mdx" };
                String[] spreadsheetTypes = { "csv", "xls", "xlsx" };
                String[] presentationTypes = { "ppt", "pptx" };

                // word processor
                for (String type : documentTypes) {
                    if (type.equals(extension)) {
                        return "document";
                    }
                }

                // spreadsheet
                for (String type : spreadsheetTypes) {
                    if (type.equals(extension)) {
                        return "spreadsheet";
                    }
                }
                // slides
                for (String type : presentationTypes) {
                    if (type.equals(extension)) {
                        return "presentation";
                    }
                }
                // fallback: extension
                return extension;
            }
            return "unknown";
        } catch (Exception e) {
            log.error("resolveFileType failed: ", e);
            return "unknown";
        }
    }

    /**
     * Read adapter type key from RAG config map.
     */
    private String extractAdapterType(Map<String, Object> config) {
        if (config == null) {
            throw new RenException(ErrorCode.RAG_CONFIG_NOT_FOUND);
        }

        // config.type
        String adapterType = (String) config.get("type");
        if (StringUtils.isBlank(adapterType)) {
            throw new RenException(ErrorCode.RAG_ADAPTER_TYPE_NOT_FOUND);
        }

        // Must be registered in factory
        if (!KnowledgeBaseAdapterFactory.isAdapterTypeRegistered(adapterType)) {
            throw new RenException(ErrorCode.RAG_ADAPTER_TYPE_NOT_SUPPORTED,
                    "Adapter type not registered: " + adapterType);
        }

        return adapterType;
    }

    @Override
    public boolean parseDocuments(String datasetId, List<String> documentIds) {
        if (StringUtils.isBlank(datasetId) || documentIds == null || documentIds.isEmpty()) {
            throw new RenException(ErrorCode.RAG_DATASET_ID_AND_MODEL_ID_NOT_NULL);
        }

        log.info("=== parseDocuments (chunk) start ===");
        log.info("datasetId: {}, documentIds: {}", datasetId, documentIds);

        try {
            // RAG config
            Map<String, Object> ragConfig = knowledgeBaseService.getRAGConfigByDatasetId(datasetId);

            // Adapter type
            String adapterType = extractAdapterType(ragConfig);

            // Adapter
            KnowledgeBaseAdapter adapter = KnowledgeBaseAdapterFactory.getAdapter(adapterType, ragConfig);

            log.debug("parseDocuments documentIds: {}", documentIds);

            // Remote parse
            boolean result = adapter.parseDocuments(datasetId, documentIds);

            if (result) {
                log.info("Parse command accepted; updating shadow to RUNNING, datasetId: {}, documentIds: {}",
                        datasetId, documentIds);
                documentDao.update(null, new UpdateWrapper<DocumentEntity>()
                        .set("run", "RUNNING")
                        .set("status", "1")
                        .set("updated_at", new Date())
                        .eq("dataset_id", datasetId)
                        .in("document_id", documentIds));

                log.info("Shadow run status set to RUNNING");
            } else {
                log.error("parseDocuments failed, datasetId: {}, documentIds: {}", datasetId, documentIds);
                throw new RenException(ErrorCode.RAG_API_ERROR, "Document parse failed");
            }

            return result;

        } catch (Exception e) {
            log.error("parseDocuments error: {}", e.getMessage(), e);
            String errorMessage = e.getMessage() != null ? e.getMessage() : "null";
            if (e instanceof RenException) {
                throw (RenException) e;
            }
            throw new RenException(ErrorCode.RAG_API_ERROR, errorMessage);
        } finally {
            log.info("=== parseDocuments end ===");
        }
    }

    @Override
    public ChunkDTO.ListVO listChunks(String datasetId, String documentId, ChunkDTO.ListReq req) {
        if (StringUtils.isBlank(datasetId) || StringUtils.isBlank(documentId)) {
            throw new RenException(ErrorCode.RAG_DATASET_ID_AND_MODEL_ID_NOT_NULL);
        }

        log.info("=== listChunks: datasetId={}, documentId={}, req={} ===", datasetId, documentId, req);

        try {
            Map<String, Object> ragConfig = knowledgeBaseService.getRAGConfigByDatasetId(datasetId);
            KnowledgeBaseAdapter adapter = KnowledgeBaseAdapterFactory.getAdapter(extractAdapterType(ragConfig),
                    ragConfig);

            ChunkDTO.ListVO result = adapter.listChunks(datasetId, documentId, req);
            log.info("listChunks OK: datasetId={}, total={}", datasetId, result.getTotal());
            return result;
        } catch (Exception e) {
            log.error("listChunks failed: {}", e.getMessage(), e);
            String errorMessage = e.getMessage() != null ? e.getMessage() : "null";
            if (e instanceof RenException) {
                throw (RenException) e;
            }
            throw new RenException(ErrorCode.RAG_API_ERROR, errorMessage);
        } finally {
            log.info("=== listChunks end ===");
        }
    }

    @Override
    public RetrievalDTO.ResultVO retrievalTest(RetrievalDTO.TestReq req) {
        if (CollectionUtils.isEmpty(req.getDatasetIds())) {
            throw new RenException("Retrieval test requires at least one dataset id");
        }

        log.info("=== retrievalTest: req={} ===", req);

        try {
            Map<String, Object> ragConfig = knowledgeBaseService.getRAGConfigByDatasetId(req.getDatasetIds().get(0));
            KnowledgeBaseAdapter adapter = KnowledgeBaseAdapterFactory.getAdapter(extractAdapterType(ragConfig),
                    ragConfig);

            RetrievalDTO.ResultVO result = adapter.retrievalTest(req);
            log.info("retrievalTest OK: total={}", result != null ? result.getTotal() : 0);
            return result;
        } catch (Exception e) {
            log.error("retrievalTest failed: {}", e.getMessage(), e);
            String errorMessage = e.getMessage() != null ? e.getMessage() : "null";
            if (e instanceof RenException) {
                throw (RenException) e;
            }
            throw new RenException(ErrorCode.RAG_API_ERROR, errorMessage);
        } finally {
            log.info("=== retrievalTest end ===");
        }
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void deleteDocumentsByDatasetId(String datasetId) {
        log.info("Cascade purge documents for datasetId={}", datasetId);
        List<DocumentEntity> list = documentDao
                .selectList(new QueryWrapper<DocumentEntity>().eq("dataset_id", datasetId));
        if (list == null || list.isEmpty())
            return;

        List<String> docIds = list.stream().map(DocumentEntity::getDocumentId).toList();

        // Reuse batch delete (RAG + shadow)
        DocumentDTO.BatchIdReq req = DocumentDTO.BatchIdReq.builder().ids(docIds).build();
        this.deleteDocuments(datasetId, req);
    }

    @Override
    public void syncRunningDocuments() {
        // RUNNING shadow rows
        List<DocumentEntity> runningDocs = documentDao.selectList(
                new QueryWrapper<DocumentEntity>()
                        .eq("run", "RUNNING")
                        .eq("status", "1") // enabled rows only
        );

        if (runningDocs == null || runningDocs.isEmpty()) {
            return;
        }

        log.info("Scheduled sync: {} document(s) in RUNNING", runningDocs.size());

        // Group by dataset, one adapter each
        Map<String, List<DocumentEntity>> groupedDocs = runningDocs.stream()
                .collect(java.util.stream.Collectors.groupingBy(DocumentEntity::getDatasetId));

        groupedDocs.forEach((datasetId, docs) -> {
            KnowledgeBaseAdapter adapter = null;
            try {
                // Lazy adapter per dataset
                Map<String, Object> ragConfig = knowledgeBaseService.getRAGConfigByDatasetId(datasetId);
                adapter = KnowledgeBaseAdapterFactory.getAdapter(extractAdapterType(ragConfig), ragConfig);
            } catch (Exception e) {
                log.warn("Adapter init failed for dataset {}, skip sync: {}", datasetId, e.getMessage());
                return;
            }

            for (DocumentEntity doc : docs) {
                try {
                    // Temp DTO for sync
                    KnowledgeFilesDTO dto = convertEntityToDTO(doc);
                    // Token before sync
                    Long oldTokenCount = dto.getTokenCount() != null ? dto.getTokenCount() : 0L;

                    syncDocumentStatusWithRAG(dto, adapter);

                    // Token delta → dataset stats
                    Long newTokenCount = dto.getTokenCount() != null ? dto.getTokenCount() : 0L;
                    Long tokenDelta = newTokenCount - oldTokenCount;

                    // Only when DONE/SUCCESS and token count moved
                    if (tokenDelta != 0) {
                        knowledgeBaseService.updateStatistics(datasetId, 0, 0L, tokenDelta);
                        log.info("Scheduled job: adjust dataset stats, docId={}, tokenDelta={}", dto.getDocumentId(),
                                tokenDelta);
                    }
                } catch (Exception e) {
                    log.error("sync document {} failed: {}", doc.getDocumentId(), e.getMessage());
                }
            }
        });
    }
}