package xiaozhi.modules.model.entity;

import java.util.Date;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableName;
import com.baomidou.mybatisplus.extension.handlers.JacksonTypeHandler;

import cn.hutool.json.JSONObject;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

@Data
@TableName(value = "ai_model_config", autoResultMap = true)
@Schema(description = "Model configuration")
public class ModelConfigEntity {

    @Schema(description = "Primary key")
    private String id;

    @Schema(description = "Model type (Memory/ASR/VAD/LLM/TTS)")
    private String modelType;

    @Schema(description = "Model code (e.g. AliLLM, DoubaoTTS)")
    private String modelCode;

    @Schema(description = "Display name")
    private String modelName;

    @Schema(description = "Default flag (0 no, 1 yes)")
    private Integer isDefault;

    @Schema(description = "Enabled flag")
    private Integer isEnabled;

    @TableField(typeHandler = JacksonTypeHandler.class)
    @Schema(description = "Config payload (JSON)")
    private JSONObject configJson;

    @Schema(description = "Official documentation URL")
    private String docLink;

    @Schema(description = "Remark")
    private String remark;

    @Schema(description = "Sort order")
    private Integer sort;

    @Schema(description = "Updater user id")
    @TableField(fill = FieldFill.UPDATE)
    private Long updater;

    @Schema(description = "Update time")
    @TableField(fill = FieldFill.UPDATE)
    private Date updateDate;

    @Schema(description = "Creator user id")
    @TableField(fill = FieldFill.INSERT)
    private Long creator;

    @Schema(description = "Create time")
    @TableField(fill = FieldFill.INSERT)
    private Date createDate;
}
