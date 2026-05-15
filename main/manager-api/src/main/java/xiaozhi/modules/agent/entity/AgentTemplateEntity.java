package xiaozhi.modules.agent.entity;

import java.io.Serializable;
import java.util.Date;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;

import lombok.Data;

/**
 * Row in {@code ai_agent_template} (default agent configuration template).
 *
 * @TableName ai_agent_template
 */
@TableName(value = "ai_agent_template")
@Data
public class AgentTemplateEntity implements Serializable {
    /**
     * Template id.
     */
    @TableId(type = IdType.ASSIGN_UUID)
    private String id;

    /**
     * Template code.
     */
    private String agentCode;

    /**
     * Display name.
     */
    private String agentName;

    /**
     * ASR model id.
     */
    private String asrModelId;

    /**
     * VAD model id.
     */
    private String vadModelId;

    /**
     * LLM model id.
     */
    private String llmModelId;

    /**
     * VLM model id.
     */
    private String vllmModelId;

    /**
     * TTS model id.
     */
    private String ttsModelId;

    /**
     * TTS voice id.
     */
    private String ttsVoiceId;

    /**
     * TTS voice language.
     */
    private String ttsLanguage;

    /**
     * TTS volume.
     */
    private Integer ttsVolume;

    /**
     * TTS speech rate.
     */
    private Integer ttsRate;

    /**
     * TTS pitch.
     */
    private Integer ttsPitch;

    /**
     * Memory model id.
     */
    private String memModelId;

    /**
     * Intent model id.
     */
    private String intentModelId;

    /**
     * Chat history mode: 0 off, 1 text only, 2 text and audio.
     */
    private Integer chatHistoryConf;

    /**
     * System / role prompt.
     */
    private String systemPrompt;

    /**
     * Summary memory text.
     */
    private String summaryMemory;
    /**
     * Locale code.
     */
    private String langCode;

    /**
     * Interaction language label.
     */
    private String language;

    /**
     * Sort weight.
     */
    private Integer sort;

    /**
     * Creator user id.
     */
    private Long creator;

    /**
     * Created at.
     */
    private Date createdAt;

    /**
     * Last updater user id.
     */
    private Long updater;

    /**
     * Updated at.
     */
    private Date updatedAt;

    @TableField(exist = false)
    private static final long serialVersionUID = 1L;
}
