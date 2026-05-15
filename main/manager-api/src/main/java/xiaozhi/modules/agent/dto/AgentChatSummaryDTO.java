package xiaozhi.modules.agent.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

/**
 * Result of generating a chat summary for a session.
 */
@Data
@Schema(description = "Chat summary result")
public class AgentChatSummaryDTO {

    @Schema(description = "Session id")
    private String sessionId;

    @Schema(description = "Agent id")
    private String agentId;

    @Schema(description = "Summary text")
    private String summary;

    @Schema(description = "Whether generation succeeded")
    private boolean success;

    @Schema(description = "Error message when success is false")
    private String errorMessage;

    public AgentChatSummaryDTO() {
        this.success = true;
    }

    public AgentChatSummaryDTO(String sessionId, String agentId, String summary) {
        this.sessionId = sessionId;
        this.agentId = agentId;
        this.summary = summary;
        this.success = true;
    }

    public AgentChatSummaryDTO(String sessionId, String errorMessage) {
        this.sessionId = sessionId;
        this.errorMessage = errorMessage;
        this.success = false;
    }

}