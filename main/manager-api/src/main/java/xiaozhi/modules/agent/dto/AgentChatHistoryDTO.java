package xiaozhi.modules.agent.dto;

import java.util.Date;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

/**
 * One chat message in history.
 */
@Data
@Schema(description = "Chat history message")
public class AgentChatHistoryDTO {
    @Schema(description = "Created at")
    private Date createdAt;

    @Schema(description = "Role: 1 user, 2 agent")
    private Byte chatType;

    @Schema(description = "Text content")
    private String content;

    @Schema(description = "Audio id if any")
    private String audioId;

    @Schema(description = "Device MAC address")
    private String macAddress;
}