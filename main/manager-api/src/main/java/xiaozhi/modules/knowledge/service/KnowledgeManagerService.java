package xiaozhi.modules.knowledge.service;

import java.util.List;

/**
 * Orchestrates cross-service flows for knowledge base + documents (avoids circular dependencies).
 */
public interface KnowledgeManagerService {

    /**
     * Deletes a dataset and all its documents (local DB + RAGFlow).
     */
    void deleteDatasetWithFiles(String datasetId);

    /**
     * Batch {@link #deleteDatasetWithFiles(String)}.
     */
    void batchDeleteDatasetsWithFiles(List<String> datasetIds);
}
