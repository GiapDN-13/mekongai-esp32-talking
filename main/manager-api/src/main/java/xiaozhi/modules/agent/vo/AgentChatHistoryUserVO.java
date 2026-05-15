package xiaozhi.modules.agent.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

/**
 * Recent user-side chat row (minimal fields).
 */
@Data
public class AgentChatHistoryUserVO {
    @Schema(description = "Message text")
    private String content;

    @Schema(description = "Audio id")
    private String audioId;
}
