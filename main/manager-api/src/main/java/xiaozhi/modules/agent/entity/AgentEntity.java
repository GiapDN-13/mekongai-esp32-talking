package xiaozhi.modules.agent.entity;

import java.util.Date;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

@Data
@TableName("ai_agent")
@Schema(description = "Agent")
public class AgentEntity {

    @TableId(type = IdType.ASSIGN_UUID)
    @Schema(description = "Agent id")
    private String id;

    @Schema(description = "Owner user id")
    private Long userId;

    @Schema(description = "Agent code")
    private String agentCode;

    @Schema(description = "Display name")
    private String agentName;

    @Schema(description = "ASR model id")
    private String asrModelId;

    @Schema(description = "VAD model id")
    private String vadModelId;

    @Schema(description = "LLM model id")
    private String llmModelId;

    @Schema(description = "VLM model id")
    private String vllmModelId;

    @Schema(description = "TTS model id")
    private String ttsModelId;

    @Schema(description = "TTS voice id")
    private String ttsVoiceId;

    @Schema(description = "TTS voice language")
    private String ttsLanguage;

    @Schema(description = "TTS volume")
    private Integer ttsVolume;

    @Schema(description = "TTS speech rate")
    private Integer ttsRate;

    @Schema(description = "TTS pitch")
    private Integer ttsPitch;

    @Schema(description = "Memory model id")
    private String memModelId;

    @Schema(description = "Intent model id")
    private String intentModelId;

    @Schema(description = "Chat history mode: 0 off, 1 text only, 2 text and audio")
    private Integer chatHistoryConf;

    @Schema(description = "System / role prompt")
    private String systemPrompt;

    @Schema(description = "Summary memory text", example = "Key facts about the user from past conversations.", required = false)
    private String summaryMemory;

    @Schema(description = "Locale code")
    private String langCode;

    @Schema(description = "Interaction language label")
    private String language;

    @Schema(description = "Sort order")
    private Integer sort;

    @Schema(description = "Creator user id")
    private Long creator;

    @Schema(description = "Created at")
    private Date createdAt;

    @Schema(description = "Last updater user id")
    private Long updater;

    @Schema(description = "Updated at")
    private Date updatedAt;
}