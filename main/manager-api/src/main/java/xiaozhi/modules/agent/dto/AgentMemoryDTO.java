package xiaozhi.modules.agent.dto;

import java.io.Serializable;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

/**
 * Partial update for agent summary memory.
 */
@Data
@Schema(description = "Agent memory update")
public class AgentMemoryDTO implements Serializable {
    private static final long serialVersionUID = 1L;

    @Schema(description = "Summary memory text", example = "Key facts about the user from past conversations.", required = false)
    private String summaryMemory;
}