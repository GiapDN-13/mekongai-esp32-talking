package xiaozhi.modules.knowledge.service;

import java.util.List;
import java.util.Map;

import org.springframework.web.multipart.MultipartFile;

import xiaozhi.common.page.PageData;
import xiaozhi.modules.knowledge.dto.KnowledgeFilesDTO;
import xiaozhi.modules.knowledge.dto.document.ChunkDTO;
import xiaozhi.modules.knowledge.dto.document.RetrievalDTO;
import xiaozhi.modules.knowledge.dto.document.DocumentDTO;

/**
 * Knowledge-base document (shadow + RAG) operations.
 */
public interface KnowledgeFilesService {

    PageData<KnowledgeFilesDTO> getPageList(KnowledgeFilesDTO knowledgeFilesDTO, Integer page, Integer limit);

    DocumentDTO.InfoVO getByDocumentId(String documentId, String datasetId);

    KnowledgeFilesDTO uploadDocument(String datasetId, MultipartFile file, String name,
            Map<String, Object> metaFields, String chunkMethod,
            Map<String, Object> parserConfig);

    void deleteDocuments(String datasetId, DocumentDTO.BatchIdReq req);

    Map<String, Object> getRAGConfig(String ragModelId);

    boolean parseDocuments(String datasetId, List<String> documentIds);

    ChunkDTO.ListVO listChunks(String datasetId, String documentId, ChunkDTO.ListReq req);

    RetrievalDTO.ResultVO retrievalTest(RetrievalDTO.TestReq req);

    void saveDocumentShadow(String datasetId, KnowledgeFilesDTO result, String originalName, String chunkMethod,
            Map<String, Object> parserConfig);

    void deleteDocumentShadows(List<String> documentIds, String datasetId, Long chunkDelta, Long tokenDelta);

    void deleteDocumentsByDatasetId(String datasetId);

    /** Used by {@link xiaozhi.modules.knowledge.task.DocumentStatusSyncTask}. */
    void syncRunningDocuments();
}
