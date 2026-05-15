package xiaozhi.modules.agent.dto;

import java.io.Serializable;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import lombok.Data;

/**
 * Minimal payload to create an agent; id, code, and sort are assigned by the server.
 */
@Data
@Schema(description = "Agent create request")
public class AgentCreateDTO implements Serializable {
    private static final long serialVersionUID = 1L;

    @Schema(description = "Display name", example = "Support assistant")
    @NotBlank(message = "Agent name is required")
    private String agentName;
}