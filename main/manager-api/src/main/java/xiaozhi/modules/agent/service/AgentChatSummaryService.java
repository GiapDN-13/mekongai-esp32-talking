package xiaozhi.modules.agent.service;

/**
 * Async chat summarization into agent memory.
 */
public interface AgentChatSummaryService {

    /**
     * Build a summary for the session and merge into the agent's memory field.
     *
     * @param sessionId session id
     * @return whether persistence succeeded
     */
    boolean generateAndSaveChatSummary(String sessionId);
}
