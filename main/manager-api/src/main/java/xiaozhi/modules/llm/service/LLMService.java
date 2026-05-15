package xiaozhi.modules.llm.service;

/**
 * LLM service for chat memory summarization and related calls.
 */
public interface LLMService {

    /**
     * Summarize a conversation using a custom prompt template.
     *
     * @param conversation   raw conversation text
     * @param promptTemplate prompt template (may contain {@code {conversation}})
     * @return summary text or an error message
     */
    String generateSummary(String conversation, String promptTemplate);

    /**
     * Summarize a conversation using the built-in default prompt.
     */
    String generateSummary(String conversation);

    /**
     * Summarize using a specific model configuration id.
     */
    String generateSummaryWithModel(String conversation, String modelId);

    /**
     * Summarize with explicit model id and prompt template.
     */
    String generateSummary(String conversation, String promptTemplate, String modelId);

    /**
     * Summarize and merge with prior memory (template may use {@code {history_memory}} and {@code {conversation}}).
     */
    String generateSummaryWithHistory(String conversation, String historyMemory, String promptTemplate, String modelId);

    /**
     * Whether the default LLM configuration looks usable (base URL and API key present).
     */
    boolean isAvailable();

    /**
     * Whether the given model id’s configuration looks usable.
     */
    boolean isAvailable(String modelId);
}
