package xiaozhi.modules.timbre.entity;

import java.util.Date;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableName;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;
import lombok.EqualsAndHashCode;

/**
 * Timbre entity mapped to {@code ai_tts_voice}.
 *
 * @author zjy
 * @since 2025-3-21
 */
@Data
@EqualsAndHashCode(callSuper = false)
@TableName("ai_tts_voice")
@Schema(description = "Timbre")
public class TimbreEntity {

    @Schema(description = "ID")
    private String id;

    @Schema(description = "Language")
    private String languages;

    @Schema(description = "Timbre name")
    private String name;

    @Schema(description = "Remark")
    private String remark;

    @Schema(description = "Reference audio path")
    private String referenceAudio;

    @Schema(description = "Reference text")
    private String referenceText;

    @Schema(description = "Sort order")
    private long sort;

    @Schema(description = "TTS model primary key")
    private String ttsModelId;

    @Schema(description = "Voice code")
    private String ttsVoice;

    @Schema(description = "Audio demo URL")
    private String voiceDemo;

    @Schema(description = "Updated by")
    @TableField(fill = FieldFill.UPDATE)
    private Long updater;

    @Schema(description = "Updated at")
    @TableField(fill = FieldFill.UPDATE)
    private Date updateDate;

    @Schema(description = "Created by")
    @TableField(fill = FieldFill.INSERT)
    private Long creator;

    @Schema(description = "Created at")
    @TableField(fill = FieldFill.INSERT)
    private Date createDate;

}
