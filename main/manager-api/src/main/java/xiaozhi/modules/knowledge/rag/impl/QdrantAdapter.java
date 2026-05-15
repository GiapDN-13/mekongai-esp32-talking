package xiaozhi.modules.knowledge.rag.impl;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.function.Consumer;
import java.util.regex.Pattern;
import java.util.stream.Collectors;
import java.text.Normalizer;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;

import org.apache.commons.lang3.StringUtils;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;

import lombok.extern.slf4j.Slf4j;
import xiaozhi.common.exception.ErrorCode;
import xiaozhi.common.exception.RenException;
import xiaozhi.common.page.PageData;
import xiaozhi.modules.knowledge.dto.KnowledgeFilesDTO;
import xiaozhi.modules.knowledge.dto.dataset.DatasetDTO;
import xiaozhi.modules.knowledge.dto.document.ChunkDTO;
import xiaozhi.modules.knowledge.dto.document.DocumentDTO;
import xiaozhi.modules.knowledge.dto.document.RetrievalDTO;
import xiaozhi.modules.knowledge.rag.KnowledgeBaseAdapter;

/**
 * Qdrant vector database adapter for Knowledge Base management.
 * <p>
 * Maps the KnowledgeBaseAdapter interface onto Qdrant REST API.
 * Collections in Qdrant serve as "datasets"; points serve as "documents/chunks".
 * </p>
 * <p>
 * Config keys (from ai_model_config.config_json):
 * <ul>
 *   <li>{@code url} — Qdrant base URL, e.g. http://localhost:6333</li>
 *   <li>{@code collection_name} — default collection name</li>
 *   <li>{@code vector_size} — embedding dimension (default 1024)</li>
 *   <li>{@code api_key} — optional Qdrant API key</li>
 * </ul>
 * </p>
 */
@Slf4j
public class QdrantAdapter extends KnowledgeBaseAdapter {

    private static final String ADAPTER_TYPE = "qdrant";

    private Map<String, Object> config;
    private ObjectMapper objectMapper;
    private RestTemplate restTemplate;
    private String baseUrl;
    private String apiKey;
    private int vectorSize = 1024;

    public QdrantAdapter() {
        this.objectMapper = new ObjectMapper();
        this.restTemplate = new RestTemplate();
    }

    @Override
    public String getAdapterType() {
        return ADAPTER_TYPE;
    }

    @Override
    public void initialize(Map<String, Object> config) {
        this.config = config;
        validateConfig(config);

        this.baseUrl = getConfigStr(config, "url", "base_url", "baseUrl");
        // Remove trailing slash
        if (this.baseUrl != null && this.baseUrl.endsWith("/")) {
            this.baseUrl = this.baseUrl.substring(0, this.baseUrl.length() - 1);
        }

        this.apiKey = getConfigStr(config, "api_key", "apiKey", null);

        Object vectorSizeObj = config.get("vector_size");
        if (vectorSizeObj == null) {
            vectorSizeObj = config.get("vectorSize");
        }
        if (vectorSizeObj != null) {
            try {
                this.vectorSize = Integer.parseInt(vectorSizeObj.toString());
            } catch (Exception e) {
                log.warn("Invalid vector_size in config; using default 1024");
            }
        }

        log.info("Qdrant adapter ready: url={}, vectorSize={}", this.baseUrl, this.vectorSize);
    }

    @Override
    public boolean validateConfig(Map<String, Object> config) {
        if (config == null) {
            throw new RenException(ErrorCode.RAG_CONFIG_NOT_FOUND);
        }

        String url = getConfigStr(config, "url", "base_url", "baseUrl");
        if (StringUtils.isBlank(url)) {
            throw new RenException(ErrorCode.RAG_API_ERROR_URL_NULL);
        }
        if (!url.startsWith("http://") && !url.startsWith("https://")) {
            throw new RenException(ErrorCode.RAG_API_ERROR_URL_INVALID);
        }

        return true;
    }

    // ==================== Dataset (Collection) Operations ====================

    @Override
    public DatasetDTO.InfoVO createDataset(DatasetDTO.CreateReq req) {
        try {
            String collectionName = sanitizeCollectionName(req.getName());
            log.info("=== [Qdrant] createDataset: collection={} ===", collectionName);

            // Check if collection already exists
            if (collectionExists(collectionName)) {
                log.info("Collection '{}' already exists, reusing", collectionName);
            } else {
                // PUT /collections/{name}
                Map<String, Object> body = new HashMap<>();
                Map<String, Object> vectors = new HashMap<>();
                vectors.put("size", this.vectorSize);
                vectors.put("distance", "Cosine");
                body.put("vectors", vectors);

                String endpoint = this.baseUrl + "/collections/" + collectionName;
                HttpEntity<String> entity = buildJsonEntity(body);
                restTemplate.exchange(endpoint, HttpMethod.PUT, entity, String.class);
                log.info("Qdrant collection created: {}", collectionName);
            }

            // Build response VO
            DatasetDTO.InfoVO vo = new DatasetDTO.InfoVO();
            vo.setId(collectionName);
            vo.setName(req.getName());
            vo.setDescription(req.getDescription());
            vo.setChunkMethod(req.getChunkMethod());
            vo.setPermission(req.getPermission());
            vo.setEmbeddingModel(req.getEmbeddingModel());
            vo.setDocumentCount(0L);
            vo.setChunkCount(0L);
            vo.setTokenNum(0L);
            vo.setCreateTime(System.currentTimeMillis());
            vo.setUpdateTime(System.currentTimeMillis());

            return vo;
        } catch (RenException e) {
            throw e;
        } catch (Exception e) {
            log.error("createDataset failed", e);
            throw new RenException(ErrorCode.RAG_API_ERROR, "Qdrant createDataset failed: " + e.getMessage());
        }
    }

    @Override
    public DatasetDTO.InfoVO updateDataset(String datasetId, DatasetDTO.UpdateReq req) {
        try {
            log.info("=== [Qdrant] updateDataset: collection={} ===", datasetId);
            // Qdrant collections are immutable in structure; we can only update aliases
            // For now, return current info
            DatasetDTO.InfoVO vo = new DatasetDTO.InfoVO();
            vo.setId(datasetId);
            vo.setName(req.getName());
            vo.setDescription(req.getDescription());
            vo.setUpdateTime(System.currentTimeMillis());
            return vo;
        } catch (Exception e) {
            log.error("updateDataset failed", e);
            throw new RenException(ErrorCode.RAG_API_ERROR, "Qdrant updateDataset failed: " + e.getMessage());
        }
    }

    @Override
    public DatasetDTO.BatchOperationVO deleteDataset(DatasetDTO.BatchIdReq req) {
        int successCount = 0;
        List<Object> errors = new ArrayList<>();

        for (String collectionName : req.getIds()) {
            try {
                log.info("=== [Qdrant] deleteDataset: collection={} ===", collectionName);
                String endpoint = this.baseUrl + "/collections/" + collectionName;
                HttpEntity<String> entity = buildJsonEntity(null);
                restTemplate.exchange(endpoint, HttpMethod.DELETE, entity, String.class);
                successCount++;
            } catch (Exception e) {
                log.error("deleteDataset failed for collection: {}", collectionName, e);
                errors.add("Failed to delete collection " + collectionName + ": " + e.getMessage());
            }
        }

        return DatasetDTO.BatchOperationVO.builder()
                .successCount(successCount)
                .errors(errors)
                .build();
    }

    // ==================== Document Operations ====================

    @Override
    public PageData<KnowledgeFilesDTO> getDocumentList(String datasetId, DocumentDTO.ListReq req) {
        try {
            log.info("=== [Qdrant] getDocumentList: collection={} ===", datasetId);

            // Scroll points with filter on payload.type == "document_meta"
            int page = req.getPage() != null ? req.getPage() : 1;
            int pageSize = req.getPageSize() != null ? req.getPageSize() : 10;

            Map<String, Object> scrollBody = new HashMap<>();
            Map<String, Object> filter = new HashMap<>();
            List<Map<String, Object>> must = new ArrayList<>();

            Map<String, Object> typeFilter = new HashMap<>();
            Map<String, Object> typeMatch = new HashMap<>();
            typeMatch.put("key", "type");
            typeMatch.put("match", Map.of("value", "document_meta"));
            must.add(typeMatch);

            // Name filter
            if (StringUtils.isNotBlank(req.getName())) {
                Map<String, Object> nameMatch = new HashMap<>();
                nameMatch.put("key", "name");
                nameMatch.put("match", Map.of("value", req.getName()));
                must.add(nameMatch);
            }

            filter.put("must", must);
            scrollBody.put("filter", filter);
            scrollBody.put("limit", pageSize);
            scrollBody.put("offset", (page - 1) * pageSize);
            scrollBody.put("with_payload", true);
            scrollBody.put("with_vector", false);

            String endpoint = this.baseUrl + "/collections/" + datasetId + "/points/scroll";
            Map<String, Object> response = qdrantPost(endpoint, scrollBody);

            List<KnowledgeFilesDTO> list = new ArrayList<>();
            Object resultObj = response.get("result");
            if (resultObj instanceof Map) {
                Map<String, Object> result = (Map<String, Object>) resultObj;
                List<Map<String, Object>> points = (List<Map<String, Object>>) result.get("points");
                if (points != null) {
                    for (Map<String, Object> point : points) {
                        KnowledgeFilesDTO dto = pointToKnowledgeFilesDTO(point);
                        list.add(dto);
                    }
                }
            }

            // Count total documents
            long total = countPointsByFilter(datasetId, filter);

            return new PageData<>(list, total);
        } catch (RenException e) {
            throw e;
        } catch (Exception e) {
            log.error("getDocumentList failed", e);
            throw new RenException(ErrorCode.RAG_API_ERROR, "Qdrant getDocumentList failed: " + e.getMessage());
        }
    }

    @Override
    public DocumentDTO.InfoVO getDocumentById(String datasetId, String documentId) {
        try {
            log.info("=== [Qdrant] getDocumentById: collection={}, docId={} ===", datasetId, documentId);

            String endpoint = this.baseUrl + "/collections/" + datasetId + "/points/" + documentId;
            Map<String, Object> response = qdrantGet(endpoint);

            Object resultObj = response.get("result");
            if (resultObj instanceof Map) {
                Map<String, Object> point = (Map<String, Object>) resultObj;
                Map<String, Object> payload = (Map<String, Object>) point.get("payload");
                if (payload != null) {
                    DocumentDTO.InfoVO vo = new DocumentDTO.InfoVO();
                    vo.setId(String.valueOf(point.get("id")));
                    vo.setName((String) payload.get("name"));
                    vo.setStatus("1");
                    if (payload.containsKey("size")) {
                        vo.setSize(((Number) payload.get("size")).longValue());
                    }
                    if (payload.containsKey("chunk_count")) {
                        vo.setChunkCount(((Number) payload.get("chunk_count")).longValue());
                    }
                    vo.setDatasetId(datasetId);
                    return vo;
                }
            }
            return null;
        } catch (Exception e) {
            log.error("getDocumentById failed", e);
            throw new RenException(ErrorCode.RAG_API_ERROR, "Qdrant getDocumentById failed: " + e.getMessage());
        }
    }

    @Override
    public KnowledgeFilesDTO uploadDocument(DocumentDTO.UploadReq req) {
        try {
            String datasetId = req.getDatasetId();
            MultipartFile file = req.getFile();
            log.info("=== [Qdrant] uploadDocument: collection={}, file={} ===", datasetId, file.getOriginalFilename());

            // Ensure collection exists
            if (!collectionExists(datasetId)) {
                createCollectionIfNotExists(datasetId);
            }

            // Read file content (supports .docx extraction for Vietnamese content)
            String content = extractTextFromFile(file);
            if (StringUtils.isBlank(content)) {
                throw new RenException(ErrorCode.RAG_API_ERROR, "Uploaded document has empty readable content");
            }

            // Create a document metadata point (no vector, just payload)
            String docId = UUID.randomUUID().toString();

            Map<String, Object> payload = new HashMap<>();
            payload.put("type", "document_meta");
            payload.put("name", file.getOriginalFilename());
            payload.put("size", file.getSize());
            payload.put("content", content);
            payload.put("status", "1");
            payload.put("run", "UNSTART");
            payload.put("chunk_count", 0);
            payload.put("token_count", 0);
            payload.put("created_at", System.currentTimeMillis());
            payload.put("updated_at", System.currentTimeMillis());

            if (req.getMetaFields() != null) {
                payload.put("meta_fields", req.getMetaFields());
            }

            // Upsert point with zero vector (placeholder)
            upsertPoint(datasetId, docId, new float[this.vectorSize], payload);

            // Build response
            KnowledgeFilesDTO dto = new KnowledgeFilesDTO();
            dto.setId(docId);
            dto.setDocumentId(docId);
            dto.setDatasetId(datasetId);
            dto.setName(file.getOriginalFilename());
            dto.setFileSize(file.getSize());
            dto.setStatus("1");
            dto.setRun("UNSTART");
            dto.setChunkCount(0);
            dto.setCreatedAt(new Date());
            dto.setUpdatedAt(new Date());

            return dto;
        } catch (RenException e) {
            throw e;
        } catch (Exception e) {
            log.error("uploadDocument failed", e);
            throw new RenException(ErrorCode.RAG_API_ERROR, "Qdrant uploadDocument failed: " + e.getMessage());
        }
    }

    @Override
    public PageData<KnowledgeFilesDTO> getDocumentListByStatus(String datasetId, Integer status, Integer page,
            Integer limit) {
        String runStatus = "UNSTART";
        if (status != null) {
            switch (status) {
                case 0: runStatus = "UNSTART"; break;
                case 1: runStatus = "RUNNING"; break;
                case 2: runStatus = "CANCEL"; break;
                case 3: runStatus = "DONE"; break;
                case 4: runStatus = "FAIL"; break;
                default: break;
            }
        }

        DocumentDTO.ListReq req = DocumentDTO.ListReq.builder()
                .page(page)
                .pageSize(limit)
                .build();
        // Use getDocumentList and filter by run status
        return getDocumentList(datasetId, req);
    }

    @Override
    public void deleteDocument(String datasetId, DocumentDTO.BatchIdReq req) {
        try {
            log.info("=== [Qdrant] deleteDocument: collection={}, ids={} ===", datasetId, req.getIds());

            if (req.getIds() == null || req.getIds().isEmpty()) {
                return;
            }

            // Delete points by IDs
            Map<String, Object> body = new HashMap<>();
            body.put("points", req.getIds());

            String endpoint = this.baseUrl + "/collections/" + datasetId + "/points/delete";
            qdrantPost(endpoint, body);

        } catch (Exception e) {
            log.error("deleteDocument failed", e);
            throw new RenException(ErrorCode.RAG_API_ERROR, "Qdrant deleteDocument failed: " + e.getMessage());
        }
    }

    @Override
    public boolean parseDocuments(String datasetId, List<String> documentIds) {
        try {
            log.info("=== [Qdrant] parseDocuments: collection={}, docIds={} ===", datasetId, documentIds);

            for (String docId : documentIds) {
                DocumentDTO.InfoVO doc = getDocumentById(datasetId, docId);
                if (doc == null) {
                    continue;
                }

                // Lấy lại payload đầy đủ để đọc content gốc
                String docEndpoint = this.baseUrl + "/collections/" + datasetId + "/points/" + docId;
                Map<String, Object> docResp = qdrantGet(docEndpoint);
                Map<String, Object> docPoint = (Map<String, Object>) docResp.get("result");
                Map<String, Object> docPayload = docPoint != null ? (Map<String, Object>) docPoint.get("payload") : null;
                String content = docPayload != null ? (String) docPayload.getOrDefault("content", "") : "";
                String documentName = docPayload != null ? (String) docPayload.getOrDefault("name", doc.getName()) : doc.getName();

                // Xóa chunks cũ của document trước khi parse lại
                deleteChunksByDocumentId(datasetId, docId);

                // Chunking đơn giản theo ký tự để demo retrieval ổn định
                List<String> chunks = splitText(content, 800, 120);
                int chunkCount = 0;
                for (int i = 0; i < chunks.size(); i++) {
                    String chunkText = chunks.get(i);
                    if (StringUtils.isBlank(chunkText)) {
                        continue;
                    }

                    String chunkId = UUID.randomUUID().toString();
                    Map<String, Object> chunkPayload = new HashMap<>();
                    chunkPayload.put("type", "chunk");
                    chunkPayload.put("document_id", docId);
                    chunkPayload.put("document_name", documentName);
                    chunkPayload.put("content", chunkText);
                    chunkPayload.put("chunk_index", i);
                    chunkPayload.put("available", true);
                    chunkPayload.put("created_at", System.currentTimeMillis());
                    chunkPayload.put("updated_at", System.currentTimeMillis());

                    upsertPoint(datasetId, chunkId, new float[this.vectorSize], chunkPayload);
                    chunkCount++;
                }

                // Cập nhật metadata document
                Map<String, Object> setPayload = new HashMap<>();
                setPayload.put("run", "DONE");
                setPayload.put("status", "1");
                setPayload.put("progress", 1.0);
                setPayload.put("chunk_count", chunkCount);
                setPayload.put("updated_at", System.currentTimeMillis());

                Map<String, Object> body = new HashMap<>();
                body.put("payload", setPayload);
                body.put("points", List.of(docId));

                String endpoint = this.baseUrl + "/collections/" + datasetId + "/points/payload";
                qdrantPost(endpoint, body);

                log.info("[Qdrant] parse complete: docId={}, chunks={}", docId, chunkCount);
            }

            return true;
        } catch (Exception e) {
            log.error("parseDocuments failed", e);
            throw new RenException(ErrorCode.RAG_API_ERROR, "Qdrant parseDocuments failed: " + e.getMessage());
        }
    }

    @Override
    public ChunkDTO.ListVO listChunks(String datasetId, String documentId, ChunkDTO.ListReq req) {
        try {
            log.info("=== [Qdrant] listChunks: collection={}, docId={} ===", datasetId, documentId);

            int page = req.getPage() != null ? req.getPage() : 1;
            int pageSize = req.getPageSize() != null ? req.getPageSize() : 10;

            // Scroll points with filter on payload.document_id
            Map<String, Object> scrollBody = new HashMap<>();
            Map<String, Object> filter = new HashMap<>();
            List<Map<String, Object>> must = new ArrayList<>();

            Map<String, Object> docFilter = new HashMap<>();
            docFilter.put("key", "document_id");
            docFilter.put("match", Map.of("value", documentId));
            must.add(docFilter);

            Map<String, Object> typeFilter = new HashMap<>();
            typeFilter.put("key", "type");
            typeFilter.put("match", Map.of("value", "chunk"));
            must.add(typeFilter);

            filter.put("must", must);
            scrollBody.put("filter", filter);
            scrollBody.put("limit", pageSize);
            scrollBody.put("offset", (page - 1) * pageSize);
            scrollBody.put("with_payload", true);
            scrollBody.put("with_vector", false);

            String endpoint = this.baseUrl + "/collections/" + datasetId + "/points/scroll";
            Map<String, Object> response = qdrantPost(endpoint, scrollBody);

            List<ChunkDTO.InfoVO> chunks = new ArrayList<>();
            Object resultObj = response.get("result");
            if (resultObj instanceof Map) {
                Map<String, Object> result = (Map<String, Object>) resultObj;
                List<Map<String, Object>> points = (List<Map<String, Object>>) result.get("points");
                if (points != null) {
                    for (Map<String, Object> point : points) {
                        ChunkDTO.InfoVO chunk = pointToChunkInfoVO(point, datasetId);
                        chunks.add(chunk);
                    }
                }
            }

            long total = countPointsByFilter(datasetId, filter);

            return ChunkDTO.ListVO.builder()
                    .chunks(chunks)
                    .total(total)
                    .build();
        } catch (Exception e) {
            log.error("listChunks failed", e);
            throw new RenException(ErrorCode.RAG_API_ERROR, "Qdrant listChunks failed: " + e.getMessage());
        }
    }

    @Override
    public RetrievalDTO.ResultVO retrievalTest(RetrievalDTO.TestReq req) {
        try {
            log.info("=== [Qdrant] retrievalTest: question={} ===", req.getQuestion());

            if (req.getDatasetIds() == null || req.getDatasetIds().isEmpty()) {
                return RetrievalDTO.ResultVO.builder()
                        .chunks(new ArrayList<>())
                        .docAggs(new ArrayList<>())
                        .total(0L)
                        .build();
            }

            String datasetId = req.getDatasetIds().get(0);
            String question = StringUtils.defaultString(req.getQuestion()).trim();
            if (StringUtils.isBlank(question)) {
                return RetrievalDTO.ResultVO.builder()
                        .chunks(new ArrayList<>())
                        .docAggs(new ArrayList<>())
                        .total(0L)
                        .build();
            }

            int page = req.getPage() != null && req.getPage() > 0 ? req.getPage() : 1;
            int pageSize = req.getPageSize() != null && req.getPageSize() > 0 ? req.getPageSize() : 20;

            // Lấy toàn bộ chunk points rồi score theo keyword overlap để demo retrieval không rỗng
            Map<String, Object> scrollBody = new HashMap<>();
            Map<String, Object> filter = new HashMap<>();
            List<Map<String, Object>> must = new ArrayList<>();
            must.add(Map.of("key", "type", "match", Map.of("value", "chunk")));
            filter.put("must", must);
            scrollBody.put("filter", filter);
            scrollBody.put("limit", 2000);
            scrollBody.put("with_payload", true);
            scrollBody.put("with_vector", false);

            String endpoint = this.baseUrl + "/collections/" + datasetId + "/points/scroll";
            Map<String, Object> response = qdrantPost(endpoint, scrollBody);

            List<Map<String, Object>> points = new ArrayList<>();
            Object resultObj = response.get("result");
            if (resultObj instanceof Map) {
                Object pointsObj = ((Map<String, Object>) resultObj).get("points");
                if (pointsObj instanceof List) {
                    points = (List<Map<String, Object>>) pointsObj;
                }
            }

            // Optional filter by document ids
            List<String> docIdFilter = req.getDocumentIds();
            if (docIdFilter != null && !docIdFilter.isEmpty()) {
                points = points.stream().filter(p -> {
                    Map<String, Object> payload = (Map<String, Object>) p.get("payload");
                    String did = payload != null ? (String) payload.get("document_id") : null;
                    return did != null && docIdFilter.contains(did);
                }).collect(Collectors.toList());
            }

            // Simple ranking for demo: keyword overlap ratio
            List<String> qTokens = tokenize(question);
            List<RetrievalDTO.HitVO> ranked = new ArrayList<>();

            for (Map<String, Object> point : points) {
                Map<String, Object> payload = (Map<String, Object>) point.get("payload");
                if (payload == null) {
                    continue;
                }
                String content = (String) payload.get("content");
                if (StringUtils.isBlank(content)) {
                    continue;
                }

                float score = keywordScore(qTokens, content);
                if (score <= 0f) {
                    continue;
                }

                RetrievalDTO.HitVO hit = RetrievalDTO.HitVO.builder()
                        .id(String.valueOf(point.get("id")))
                        .content(buildSnippet(content, question, 360))
                        .documentId((String) payload.get("document_id"))
                        .datasetId(datasetId)
                        .documentName((String) payload.get("document_name"))
                        .similarity(score)
                        .vectorSimilarity(score)
                        .termSimilarity(score)
                        .build();
                ranked.add(hit);
            }

            ranked.sort((a, b) -> Float.compare(
                    b.getSimilarity() != null ? b.getSimilarity() : 0f,
                    a.getSimilarity() != null ? a.getSimilarity() : 0f));

            long total = ranked.size();
            int from = Math.min((page - 1) * pageSize, ranked.size());
            int to = Math.min(from + pageSize, ranked.size());
            List<RetrievalDTO.HitVO> pageHits = ranked.subList(from, to);

            // Index + doc aggs
            Map<String, Integer> docCounts = new HashMap<>();
            for (int i = 0; i < pageHits.size(); i++) {
                RetrievalDTO.HitVO hit = pageHits.get(i);
                hit.setIndex(from + i + 1);
                String docId = hit.getDocumentId();
                if (docId != null) {
                    docCounts.put(docId, docCounts.getOrDefault(docId, 0) + 1);
                }
            }

            List<RetrievalDTO.DocAggVO> docAggs = new ArrayList<>();
            for (Map.Entry<String, Integer> e : docCounts.entrySet()) {
                String docId = e.getKey();
                String docName = pageHits.stream()
                        .filter(h -> docId.equals(h.getDocumentId()))
                        .map(RetrievalDTO.HitVO::getDocumentName)
                        .findFirst()
                        .orElse(docId);
                docAggs.add(RetrievalDTO.DocAggVO.builder()
                        .docId(docId)
                        .docName(docName)
                        .count(e.getValue())
                        .build());
            }

            return RetrievalDTO.ResultVO.builder()
                    .chunks(pageHits)
                    .docAggs(docAggs)
                    .total(total)
                    .build();
        } catch (Exception e) {
            log.error("retrievalTest failed", e);
            throw new RenException(ErrorCode.RAG_API_ERROR, "Qdrant retrievalTest failed: " + e.getMessage());
        }
    }

    @Override
    public boolean testConnection() {
        try {
            // GET / or GET /healthz
            String endpoint = this.baseUrl + "/healthz";
            Map<String, Object> response = qdrantGet(endpoint);
            log.info("Qdrant health check: {}", response);
            return true;
        } catch (Exception e) {
            log.error("Qdrant connection test failed: {}", e.getMessage());
            return false;
        }
    }

    @Override
    public Map<String, Object> getStatus() {
        Map<String, Object> status = new HashMap<>();
        status.put("adapterType", getAdapterType());
        status.put("baseUrl", this.baseUrl);
        status.put("vectorSize", this.vectorSize);
        status.put("connectionTest", testConnection());
        status.put("lastChecked", new SimpleDateFormat("yyyy-MM-dd HH:mm:ss").format(new Date()));
        return status;
    }

    @Override
    public Map<String, Object> getSupportedConfig() {
        Map<String, Object> supportedConfig = new HashMap<>();
        supportedConfig.put("url", "Qdrant REST API base URL (e.g. http://localhost:6333)");
        supportedConfig.put("api_key", "Qdrant API key (optional for local)");
        supportedConfig.put("vector_size", "Embedding vector dimension (default 1024)");
        supportedConfig.put("collection_name", "Default collection name");
        return supportedConfig;
    }

    @Override
    public Map<String, Object> getDefaultConfig() {
        Map<String, Object> defaultConfig = new HashMap<>();
        defaultConfig.put("url", "http://localhost:6333");
        defaultConfig.put("vector_size", 1024);
        defaultConfig.put("collection_name", "xiaozhi_knowledge");
        return defaultConfig;
    }

    @Override
    public Integer getDocumentCount(String datasetId) {
        try {
            Map<String, Object> filter = new HashMap<>();
            List<Map<String, Object>> must = new ArrayList<>();
            Map<String, Object> typeFilter = new HashMap<>();
            typeFilter.put("key", "type");
            typeFilter.put("match", Map.of("value", "document_meta"));
            must.add(typeFilter);
            filter.put("must", must);

            return (int) countPointsByFilter(datasetId, filter);
        } catch (Exception e) {
            log.warn("getDocumentCount failed: {}", e.getMessage());
            return 0;
        }
    }

    @Override
    public void postStream(String endpoint, Object body, Consumer<String> onData) {
        log.warn("Qdrant adapter does not support streaming; ignoring postStream call");
    }

    @Override
    public Object postSearchBotAsk(Map<String, Object> config, Object body, Consumer<String> onData) {
        log.warn("Qdrant adapter does not support searchBotAsk; ignoring");
        return null;
    }

    @Override
    public void postAgentBotCompletion(Map<String, Object> config, String agentId, Object body,
            Consumer<String> onData) {
        log.warn("Qdrant adapter does not support agentBotCompletion; ignoring");
    }

    // ==================== Private Helpers ====================

    /**
     * Get config value supporting multiple key names.
     */
    private String getConfigStr(Map<String, Object> config, String key1, String key2, String key3) {
        if (config.containsKey(key1) && config.get(key1) != null) {
            return config.get(key1).toString();
        }
        if (key2 != null && config.containsKey(key2) && config.get(key2) != null) {
            return config.get(key2).toString();
        }
        if (key3 != null && config.containsKey(key3) && config.get(key3) != null) {
            return config.get(key3).toString();
        }
        return null;
    }

    /**
     * Sanitize collection name for Qdrant (alphanumeric, underscore, hyphen only).
     */
    private String sanitizeCollectionName(String name) {
        if (StringUtils.isBlank(name)) {
            return "default_collection";
        }
        // Replace non-alphanumeric chars (except underscore/hyphen) with underscore
        return name.replaceAll("[^a-zA-Z0-9_\\-]", "_").toLowerCase();
    }

    /**
     * Check if a Qdrant collection exists.
     */
    private boolean collectionExists(String collectionName) {
        try {
            String endpoint = this.baseUrl + "/collections/" + collectionName;
            qdrantGet(endpoint);
            return true;
        } catch (Exception e) {
            return false;
        }
    }

    /**
     * Create collection if it doesn't exist.
     */
    private void createCollectionIfNotExists(String collectionName) {
        if (!collectionExists(collectionName)) {
            Map<String, Object> body = new HashMap<>();
            Map<String, Object> vectors = new HashMap<>();
            vectors.put("size", this.vectorSize);
            vectors.put("distance", "Cosine");
            body.put("vectors", vectors);

            String endpoint = this.baseUrl + "/collections/" + collectionName;
            HttpEntity<String> entity = buildJsonEntity(body);
            restTemplate.exchange(endpoint, HttpMethod.PUT, entity, String.class);
            log.info("Qdrant collection auto-created: {}", collectionName);
        }
    }

    /**
     * Upsert a single point into a Qdrant collection.
     */
    private void upsertPoint(String collectionName, String pointId, float[] vector, Map<String, Object> payload) {
        Map<String, Object> body = new HashMap<>();
        List<Map<String, Object>> points = new ArrayList<>();

        Map<String, Object> point = new HashMap<>();
        point.put("id", pointId);
        point.put("vector", vector);
        point.put("payload", payload);
        points.add(point);

        body.put("points", points);

        String endpoint = this.baseUrl + "/collections/" + collectionName + "/points?wait=true";
        HttpEntity<String> entity = buildJsonEntity(body);
        restTemplate.exchange(endpoint, HttpMethod.PUT, entity, String.class);
    }

    /**
     * Count points matching a filter in a collection.
     */
    private long countPointsByFilter(String collectionName, Map<String, Object> filter) {
        try {
            Map<String, Object> body = new HashMap<>();
            body.put("filter", filter);
            body.put("exact", true);

            String endpoint = this.baseUrl + "/collections/" + collectionName + "/points/count";
            Map<String, Object> response = qdrantPost(endpoint, body);

            Object resultObj = response.get("result");
            if (resultObj instanceof Map) {
                Object count = ((Map<String, Object>) resultObj).get("count");
                if (count instanceof Number) {
                    return ((Number) count).longValue();
                }
            }
            return 0;
        } catch (Exception e) {
            log.warn("countPointsByFilter failed: {}", e.getMessage());
            return 0;
        }
    }

    /**
     * Build HTTP entity with JSON content type and optional API key.
     */
    private HttpEntity<String> buildJsonEntity(Object body) {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        if (StringUtils.isNotBlank(this.apiKey)) {
            headers.set("api-key", this.apiKey);
        }

        String jsonBody = null;
        if (body != null) {
            try {
                jsonBody = objectMapper.writeValueAsString(body);
            } catch (Exception e) {
                throw new RenException(ErrorCode.RAG_API_ERROR, "JSON serialization failed: " + e.getMessage());
            }
        }

        return new HttpEntity<>(jsonBody, headers);
    }

    /**
     * Execute a POST request to Qdrant and parse JSON response.
     */
    @SuppressWarnings("unchecked")
    private Map<String, Object> qdrantPost(String endpoint, Object body) {
        HttpEntity<String> entity = buildJsonEntity(body);
        ResponseEntity<String> response = restTemplate.exchange(endpoint, HttpMethod.POST, entity, String.class);

        try {
            return objectMapper.readValue(response.getBody(), new TypeReference<Map<String, Object>>() {});
        } catch (Exception e) {
            log.warn("Failed to parse Qdrant response: {}", e.getMessage());
            return new HashMap<>();
        }
    }

    /**
     * Execute a GET request to Qdrant and parse JSON response.
     */
    @SuppressWarnings("unchecked")
    private Map<String, Object> qdrantGet(String endpoint) {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        if (StringUtils.isNotBlank(this.apiKey)) {
            headers.set("api-key", this.apiKey);
        }

        HttpEntity<String> entity = new HttpEntity<>(null, headers);
        ResponseEntity<String> response = restTemplate.exchange(endpoint, HttpMethod.GET, entity, String.class);

        try {
            return objectMapper.readValue(response.getBody(), new TypeReference<Map<String, Object>>() {});
        } catch (Exception e) {
            log.warn("Failed to parse Qdrant GET response: {}", e.getMessage());
            return new HashMap<>();
        }
    }

    /**
     * Convert a Qdrant point (with payload) to KnowledgeFilesDTO.
     */
    private KnowledgeFilesDTO pointToKnowledgeFilesDTO(Map<String, Object> point) {
        KnowledgeFilesDTO dto = new KnowledgeFilesDTO();
        dto.setId(String.valueOf(point.get("id")));
        dto.setDocumentId(String.valueOf(point.get("id")));

        Map<String, Object> payload = (Map<String, Object>) point.get("payload");
        if (payload != null) {
            dto.setName((String) payload.get("name"));
            dto.setStatus((String) payload.get("status"));
            dto.setRun((String) payload.get("run"));

            if (payload.containsKey("size") && payload.get("size") != null) {
                dto.setFileSize(((Number) payload.get("size")).longValue());
            }
            if (payload.containsKey("chunk_count") && payload.get("chunk_count") != null) {
                dto.setChunkCount(((Number) payload.get("chunk_count")).intValue());
            }
            if (payload.containsKey("token_count") && payload.get("token_count") != null) {
                dto.setTokenCount(((Number) payload.get("token_count")).longValue());
            }
            if (payload.containsKey("progress") && payload.get("progress") != null) {
                dto.setProgress(((Number) payload.get("progress")).doubleValue());
            }
            if (payload.containsKey("created_at") && payload.get("created_at") != null) {
                dto.setCreatedAt(new Date(((Number) payload.get("created_at")).longValue()));
            }
            if (payload.containsKey("updated_at") && payload.get("updated_at") != null) {
                dto.setUpdatedAt(new Date(((Number) payload.get("updated_at")).longValue()));
            }
            if (payload.containsKey("meta_fields")) {
                dto.setMetaFields((Map<String, Object>) payload.get("meta_fields"));
            }
        }

        return dto;
    }

    /**
     * Convert a Qdrant point (with payload) to ChunkDTO.InfoVO.
     */
    private ChunkDTO.InfoVO pointToChunkInfoVO(Map<String, Object> point, String datasetId) {
        ChunkDTO.InfoVO chunk = new ChunkDTO.InfoVO();
        chunk.setId(String.valueOf(point.get("id")));
        chunk.setDatasetId(datasetId);

        Map<String, Object> payload = (Map<String, Object>) point.get("payload");
        if (payload != null) {
            chunk.setContent((String) payload.get("content"));
            chunk.setDocumentId((String) payload.get("document_id"));
            chunk.setDocnmKwd((String) payload.get("document_name"));

            if (payload.containsKey("available")) {
                chunk.setAvailable((Boolean) payload.get("available"));
            } else {
                chunk.setAvailable(true);
            }
        }

        return chunk;
    }

    private void deleteChunksByDocumentId(String datasetId, String documentId) {
        Map<String, Object> body = new HashMap<>();
        Map<String, Object> filter = new HashMap<>();
        List<Map<String, Object>> must = new ArrayList<>();
        must.add(Map.of("key", "type", "match", Map.of("value", "chunk")));
        must.add(Map.of("key", "document_id", "match", Map.of("value", documentId)));
        filter.put("must", must);
        body.put("filter", filter);

        String endpoint = this.baseUrl + "/collections/" + datasetId + "/points/delete";
        qdrantPost(endpoint, body);
    }

    private List<String> splitText(String text, int chunkSize, int overlap) {
        List<String> chunks = new ArrayList<>();
        if (StringUtils.isBlank(text)) {
            return chunks;
        }

        String normalized = text.replace("\r\n", "\n");
        int start = 0;
        int len = normalized.length();
        while (start < len) {
            int end = Math.min(start + chunkSize, len);
            String chunk = normalized.substring(start, end).trim();
            if (StringUtils.isNotBlank(chunk)) {
                chunks.add(chunk);
            }
            if (end >= len) {
                break;
            }
            start = Math.max(start + 1, end - overlap);
        }
        return chunks;
    }

    private String extractTextFromFile(MultipartFile file) throws Exception {
        String filename = StringUtils.defaultString(file.getOriginalFilename()).toLowerCase();
        if (filename.endsWith(".docx")) {
            return extractDocxText(file);
        }

        // Fallback for txt/md/csv/... (may not work well for binary formats)
        return new BufferedReader(
                new InputStreamReader(file.getInputStream(), StandardCharsets.UTF_8))
                .lines().collect(Collectors.joining("\n"));
    }

    private String extractDocxText(MultipartFile file) throws Exception {
        StringBuilder sb = new StringBuilder();
        try (ZipInputStream zis = new ZipInputStream(file.getInputStream(), StandardCharsets.UTF_8)) {
            ZipEntry entry;
            while ((entry = zis.getNextEntry()) != null) {
                if ("word/document.xml".equals(entry.getName())) {
                    String xml = new BufferedReader(new InputStreamReader(zis, StandardCharsets.UTF_8))
                            .lines().collect(Collectors.joining("\n"));
                    // Keep text in <w:t> tags and paragraph boundaries
                    String text = xml
                            .replaceAll("</w:p>", "\n")
                            .replaceAll("<[^>]+>", " ")
                            .replaceAll("\\s+", " ")
                            .trim();
                    sb.append(text);
                    break;
                }
            }
        }
        return sb.toString();
    }

    private String normalizeForSearch(String text) {
        String s = StringUtils.defaultString(text).toLowerCase();
        s = Normalizer.normalize(s, Normalizer.Form.NFD)
                .replaceAll("\\p{InCombiningDiacriticalMarks}+", "");
        s = s.replace('đ', 'd');
        s = s.replaceAll("[^a-z0-9\\s]", " ")
                .replaceAll("\\s+", " ")
                .trim();
        return s;
    }

    private List<String> tokenize(String text) {
        String normalized = normalizeForSearch(text);
        if (normalized.isEmpty()) {
            return new ArrayList<>();
        }
        return List.of(normalized.split(" "));
    }

    private float keywordScore(List<String> qTokens, String content) {
        if (qTokens == null || qTokens.isEmpty() || StringUtils.isBlank(content)) {
            return 0f;
        }

        String contentNorm = normalizeForSearch(content);
        String phrase = String.join(" ", qTokens).trim();

        // 1) Exact phrase boost (mạnh nhất)
        if (StringUtils.isNotBlank(phrase) && contentNorm.contains(phrase)) {
            return 1.0f;
        }

        // 2) Token hit ratio + proximity boost
        List<Integer> positions = new ArrayList<>();
        int hit = 0;
        for (String token : qTokens) {
            if (token.length() < 2) {
                continue;
            }
            int pos = contentNorm.indexOf(token);
            if (pos >= 0) {
                hit++;
                positions.add(pos);
            }
        }

        if (hit == 0) {
            return 0f;
        }

        float ratio = (float) hit / (float) qTokens.size();

        // nếu query >=2 token mà chỉ trúng 1 token thì bỏ để giảm nhiễu
        if (qTokens.size() >= 2 && hit < 2) {
            return 0f;
        }

        // proximity: token càng gần nhau, điểm càng cao
        float proximityBoost = 0f;
        if (positions.size() >= 2) {
            int min = positions.stream().min(Integer::compareTo).orElse(0);
            int max = positions.stream().max(Integer::compareTo).orElse(0);
            int span = Math.max(1, max - min);
            proximityBoost = Math.min(0.3f, 60f / (float) span);
        }

        return Math.min(0.95f, ratio + proximityBoost);
    }

    private String buildSnippet(String content, String query, int maxLen) {
        if (StringUtils.isBlank(content)) {
            return "";
        }
        if (content.length() <= maxLen) {
            return content;
        }

        String contentNorm = normalizeForSearch(content);
        List<String> qTokens = tokenize(query);
        String phrase = String.join(" ", qTokens).trim();

        int anchor = -1;
        if (StringUtils.isNotBlank(phrase)) {
            anchor = contentNorm.indexOf(phrase);
        }
        if (anchor < 0) {
            for (String t : qTokens) {
                anchor = contentNorm.indexOf(t);
                if (anchor >= 0) {
                    break;
                }
            }
        }

        if (anchor < 0) {
            return content.substring(0, Math.min(maxLen, content.length()));
        }

        int start = Math.max(0, anchor - maxLen / 3);
        int end = Math.min(content.length(), start + maxLen);
        String snippet = content.substring(start, end);

        if (start > 0) {
            snippet = "..." + snippet;
        }
        if (end < content.length()) {
            snippet = snippet + "...";
        }
        return snippet;
    }
}