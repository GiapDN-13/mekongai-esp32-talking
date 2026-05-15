package xiaozhi.modules.agent.dto;

import java.time.LocalDateTime;

import lombok.Data;

/**
 * One row in the agent session list.
 */
@Data
public class AgentChatSessionDTO {
    /**
     * Session id.
     */
    private String sessionId;

    /**
     * Session start / created time.
     */
    private LocalDateTime createdAt;

    /**
     * Message count in the session.
     */
    private Integer chatCount;
}