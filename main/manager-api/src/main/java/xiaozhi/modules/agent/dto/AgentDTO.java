package xiaozhi.modules.agent.dto;

import java.util.Date;
import java.util.List;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;
import xiaozhi.modules.agent.dto.AgentTagDTO;

/**
 * Agent summary for list/detail APIs.
 */
@Data
@Schema(description = "Agent")
public class AgentDTO {
    @Schema(description = "Agent id", example = "AGT_1234567890")
    private String id;

    @Schema(description = "Display name", example = "Support assistant")
    private String agentName;

    @Schema(description = "TTS model name", example = "tts_model_01")
    private String ttsModelName;

    @Schema(description = "Voice name", example = "voice_01")
    private String ttsVoiceName;

    @Schema(description = "LLM model name", example = "llm_model_01")
    private String llmModelName;

    @Schema(description = "VLM model name", example = "vllm_model_01")
    private String vllmModelName;

    @Schema(description = "Memory model id", example = "mem_model_01")
    private String memModelId;

    @Schema(description = "System / role prompt", example = "You are a helpful support assistant.")
    private String systemPrompt;

    @Schema(description = "Summary memory text", example = "Key facts about the user from past conversations.", required = false)
    private String summaryMemory;

    @Schema(description = "Last device connection time", example = "2024-03-20 10:00:00")
    private Date lastConnectedAt;

    @Schema(description = "Bound device count", example = "10")
    private Integer deviceCount;

    @Schema(description = "Tags")
    private List<AgentTagDTO> tags;
}