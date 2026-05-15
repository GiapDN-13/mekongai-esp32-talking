package xiaozhi.modules.voiceclone.entity;

import java.util.Date;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;
import lombok.EqualsAndHashCode;

@Data
@EqualsAndHashCode(callSuper = false)
@TableName("ai_voice_clone")
@Schema(description = "Voice clone")
public class VoiceCloneEntity {

    @TableId(type = IdType.ASSIGN_UUID)
    @Schema(description = "Unique ID")
    private String id;

    @Schema(description = "Voice display name")
    private String name;

    @Schema(description = "Model ID")
    private String modelId;

    @Schema(description = "Voice ID")
    private String voiceId;

    @Schema(description = "Languages")
    private String languages;

    @Schema(description = "User ID (references user table)")
    private Long userId;

    @Schema(description = "Audio payload")
    private byte[] voice;

    @Schema(description = "Training status: 0 pending, 1 in progress, 2 success, 3 failed")
    private Integer trainStatus;

    @Schema(description = "Training error message")
    private String trainError;

    @Schema(description = "Creator user ID")
    @TableField(fill = FieldFill.INSERT)
    private Long creator;

    @Schema(description = "Created at")
    @TableField(fill = FieldFill.INSERT)
    private Date createDate;
}
