package xiaozhi.modules.model.dto;

import java.io.Serializable;
import java.util.Date;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.extension.handlers.JacksonTypeHandler;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;
import xiaozhi.common.validator.group.UpdateGroup;

@Data
@Schema(description = "Model provider definition")
public class ModelProviderDTO implements Serializable {
    @Schema(description = "Primary key")
    @NotBlank(message = "id is required", groups = UpdateGroup.class)
    private String id;

    @Schema(description = "Model type (Memory/ASR/VAD/LLM/TTS)")
    @NotBlank(message = "modelType is required")
    private String modelType;

    @Schema(description = "Provider code")
    @NotBlank(message = "providerCode is required")
    private String providerCode;

    @Schema(description = "Display name")
    @NotBlank(message = "name is required")
    private String name;

    @Schema(description = "Provider field schema (JSON)")
    @TableField(typeHandler = JacksonTypeHandler.class)
    @NotBlank(message = "fields (JSON) is required")
    private String fields;

    @Schema(description = "Sort order")
    @NotNull(message = "sort is required")
    private Integer sort;

    @Schema(description = "Last updater user id")
    @TableField(fill = FieldFill.UPDATE)
    private Long updater;

    @Schema(description = "Last update time")
    @TableField(fill = FieldFill.UPDATE)
    private Date updateDate;

    @Schema(description = "Creator user id")
    @TableField(fill = FieldFill.INSERT)
    private Long creator;

    @Schema(description = "Create time")
    @TableField(fill = FieldFill.INSERT)
    private Date createDate;
}
