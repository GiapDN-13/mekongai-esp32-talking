package xiaozhi.modules.agent.dto;

import java.io.Serializable;
import java.math.BigDecimal;
import java.util.HashMap;
import java.util.List;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

/**
 * Agent update payload; only sent fields are applied (partial update).
 */
@Data
@Schema(description = "Agent update request")
public class AgentUpdateDTO implements Serializable {
    private static final long serialVersionUID = 1L;

    @Schema(description = "Agent code", example = "AGT_1234567890", nullable = true)
    private String agentCode;

    @Schema(description = "Display name", example = "Support assistant", nullable = true)
    private String agentName;

    @Schema(description = "ASR model id", example = "asr_model_02", nullable = true)
    private String asrModelId;

    @Schema(description = "VAD model id", example = "vad_model_02", nullable = true)
    private String vadModelId;

    @Schema(description = "LLM model id", example = "llm_model_02", nullable = true)
    private String llmModelId;

    @Schema(description = "VLM model id", example = "vllm_model_02", required = false)
    private String vllmModelId;

    @Schema(description = "TTS model id", example = "tts_model_02", required = false)
    private String ttsModelId;

    @Schema(description = "TTS voice id", example = "voice_02", nullable = true)
    private String ttsVoiceId;

    @Schema(description = "TTS voice language", example = "Mandarin", nullable = true)
    private String ttsLanguage;

    @Schema(description = "TTS volume", example = "50", nullable = true)
    private Integer ttsVolume;

    @Schema(description = "TTS speech rate", example = "50", nullable = true)
    private Integer ttsRate;

    @Schema(description = "TTS pitch", example = "50", nullable = true)
    private Integer ttsPitch;

    @Schema(description = "Memory model id", example = "mem_model_02", nullable = true)
    private String memModelId;

    @Schema(description = "Intent model id", example = "intent_model_02", nullable = true)
    private String intentModelId;

    @Schema(description = "Plugin function bindings", nullable = true)
    private List<FunctionInfo> functions;

    @Schema(description = "System / role prompt", example = "You are a helpful support assistant.", nullable = true)
    private String systemPrompt;

    @Schema(description = "Rolling summary memory text", example = "Key facts about the user learned from past chats.", nullable = true)
    private String summaryMemory;

    @Schema(description = "Chat history mode: 0 off, 1 text only, 2 text and audio", example = "2", nullable = true)
    private Integer chatHistoryConf;

    @Schema(description = "Locale code", example = "zh_CN", nullable = true)
    private String langCode;

    @Schema(description = "Interaction language label", example = "Chinese", nullable = true)
    private String language;

    @Schema(description = "Sort order", example = "1", nullable = true)
    private Integer sort;

    @Schema(description = "Context provider endpoints", nullable = true)
    private List<ContextProviderDTO> contextProviders;

    @Data
    @Schema(description = "Plugin function binding")
    public static class FunctionInfo implements Serializable {
        @Schema(description = "Plugin id", example = "plugin_01")
        private String pluginId;

        @Schema(description = "Function parameter map", nullable = true)
        private HashMap<String, Object> paramInfo;

        private static final long serialVersionUID = 1L;
    }
}