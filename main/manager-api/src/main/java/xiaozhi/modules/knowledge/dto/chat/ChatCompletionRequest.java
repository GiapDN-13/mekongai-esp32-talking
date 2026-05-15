package xiaozhi.modules.knowledge.dto.chat;

import java.io.Serializable;
import java.util.List;
import java.util.Map;

import com.fasterxml.jackson.annotation.JsonProperty;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

/**
 * Chat completion request (OpenAI-compatible shape).
 */
@Data
@Schema(description = "Chat conversation request")
public class ChatCompletionRequest implements Serializable {

    @Schema(description = "Model ID (corresponding to agent_id or bot_id)", requiredMode = Schema.RequiredMode.REQUIRED)
    @JsonProperty("model")
    private String model;

    @Schema(description = "Conversation message list", requiredMode = Schema.RequiredMode.REQUIRED)
    @JsonProperty("messages")
    private List<Message> messages;

    @Schema(description = "Whether to stream the return", defaultValue = "false")
    @JsonProperty("stream")
    private Boolean stream = false;

    @Schema(description = "Temperature coefficient (0-1)", defaultValue = "0.7")
    @JsonProperty("temperature")
    private Double temperature;

    @Schema(description = "Session ID (optional, used to continue the session)")
    @JsonProperty("session_id")
    private String sessionId;

    @Schema(description = "Other RAGFlow specific parameters (optional)")
    private Map<String, Object> extra;

    @Data
    public static class Message implements Serializable {
        @Schema(description = "Role (system, user, assistant)", requiredMode = Schema.RequiredMode.REQUIRED)
        private String role;

        @Schema(description = "content", requiredMode = Schema.RequiredMode.REQUIRED)
        private String content;
    }
}
