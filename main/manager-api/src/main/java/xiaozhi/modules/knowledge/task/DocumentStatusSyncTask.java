package xiaozhi.modules.knowledge.task;

import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import lombok.AllArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import xiaozhi.modules.knowledge.service.KnowledgeFilesService;

/**
 * Scheduled job: sync knowledge-base document status with RAGFlow.
 *
 * <ul>
 * <li>Scans documents in RUNNING (parsing) state</li>
 * <li>Pulls latest status from RAGFlow</li>
 * <li>Persists SUCCESS/FAIL transitions to the shadow DB</li>
 * <li>On success, reconciles dataset token/chunk counters</li>
 * </ul>
 */
@Component
@AllArgsConstructor
@Slf4j
public class DocumentStatusSyncTask {

    private final KnowledgeFilesService knowledgeFilesService;

    /**
     * Runs every 30s after the previous run finishes ({@code fixedDelay}) to avoid backlog.
     */
    @Scheduled(fixedDelay = 30000)
    public void syncRunningDocuments() {
        try {
            knowledgeFilesService.syncRunningDocuments();
        } catch (Exception e) {
            log.error("Document status sync task failed", e);
        }
    }
}
