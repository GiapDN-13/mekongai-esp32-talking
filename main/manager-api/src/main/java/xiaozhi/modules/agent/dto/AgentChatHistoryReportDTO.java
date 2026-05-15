package xiaozhi.modules.agent.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

/**
 * Device-reported chat history row (may include Base64 Opus audio).
 *
 * @author Haotian
 * @version 1.0, 2025/5/8
 */
@Data
@Schema(description = "Device chat history report")
public class AgentChatHistoryReportDTO {
    @Schema(description = "Device MAC address", example = "00:11:22:33:44:55")
    @NotBlank
    private String macAddress;
    @Schema(description = "Session id", example = "79578c31-f1fb-426a-900e-1e934215f05a")
    @NotBlank
    private String sessionId;
    @Schema(description = "Role: 1 user, 2 agent", example = "1")
    @NotNull
    private Byte chatType;
    @Schema(description = "Message text", example = "Hello")
    @NotBlank
    private String content;
    @Schema(description = "Base64-encoded Opus audio payload", example = "")
    private String audioBase64;
    @Schema(description = "Report time as Unix seconds; defaults to now if omitted", example = "1745657732")
    private Long reportTime;
}
