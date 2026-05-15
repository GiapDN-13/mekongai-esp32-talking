package xiaozhi.modules.knowledge.rag;

import java.util.List;
import java.util.Map;

import xiaozhi.modules.knowledge.dto.dataset.DatasetDTO;

import xiaozhi.common.page.PageData;
import xiaozhi.modules.knowledge.dto.KnowledgeFilesDTO;
import xiaozhi.modules.knowledge.dto.document.DocumentDTO;
import xiaozhi.modules.knowledge.dto.document.ChunkDTO;
import xiaozhi.modules.knowledge.dto.document.RetrievalDTO;
import java.util.function.Consumer;

/**
 * Pluggable backend for datasets and documents (RAGFlow, etc.).
 */
public abstract class KnowledgeBaseAdapter {

    /** Adapter key, e.g. {@code ragflow}. */
    public abstract String getAdapterType();

    /** Wire client from config map. */
    public abstract void initialize(Map<String, Object> config);

    /** Whether config is sufficient to call the backend. */
    public abstract boolean validateConfig(Map<String, Object> config);

    /** Paged documents in a dataset. */
    public abstract PageData<KnowledgeFilesDTO> getDocumentList(String datasetId,
            DocumentDTO.ListReq req);

    /** Single document metadata. */
    public abstract DocumentDTO.InfoVO getDocumentById(String datasetId, String documentId);

    /** Upload binary and return shadow-facing DTO. */
    public abstract KnowledgeFilesDTO uploadDocument(DocumentDTO.UploadReq req);

    /** Filter documents by parse status. */
    public abstract PageData<KnowledgeFilesDTO> getDocumentListByStatus(String datasetId,
            Integer status,
            Integer page,
            Integer limit);

    /** Remove documents on remote and (usually) locally. */
    public abstract void deleteDocument(String datasetId, DocumentDTO.BatchIdReq req);

    /** Trigger parse/chunk pipeline. */
    public abstract boolean parseDocuments(String datasetId, List<String> documentIds);

    /** Paged chunks for one document. */
    public abstract ChunkDTO.ListVO listChunks(String datasetId,
            String documentId,
            ChunkDTO.ListReq req);

    /** Retrieval / similarity smoke test. */
    public abstract RetrievalDTO.ResultVO retrievalTest(
            RetrievalDTO.TestReq req);

    /** Health check against configured base URL. */
    public abstract boolean testConnection();

    /** Adapter diagnostics for admin UI. */
    public abstract Map<String, Object> getStatus();

    /** Supported config keys and hints. */
    public abstract Map<String, Object> getSupportedConfig();

    /** Suggested defaults when creating a dataset. */
    public abstract Map<String, Object> getDefaultConfig();

    public abstract DatasetDTO.InfoVO createDataset(DatasetDTO.CreateReq req);

    public abstract DatasetDTO.InfoVO updateDataset(String datasetId, DatasetDTO.UpdateReq req);

    public abstract DatasetDTO.BatchOperationVO deleteDataset(DatasetDTO.BatchIdReq req);

    public abstract Integer getDocumentCount(String datasetId);

    /** Low-level SSE POST. */
    public abstract void postStream(String endpoint, Object body, Consumer<String> onData);

    public abstract Object postSearchBotAsk(Map<String, Object> config, Object body,
            Consumer<String> onData);

    public abstract void postAgentBotCompletion(Map<String, Object> config, String agentId, Object body,
            Consumer<String> onData);
}
