package xiaozhi.modules.model.entity;

import java.util.Date;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

@Data
@TableName("ai_model_provider")
@Schema(description = "Model provider")
public class ModelProviderEntity {

    @TableId(type = IdType.ASSIGN_UUID)
    @Schema(description = "Primary key")
    private String id;

    @Schema(description = "Model type (Memory/ASR/VAD/LLM/TTS)")
    private String modelType;

    @Schema(description = "Provider code, e.g. openai")
    private String providerCode;

    @Schema(description = "Display name")
    private String name;

    @Schema(description = "Provider fields (JSON)")
    private String fields;

    @Schema(description = "Sort order")
    private Integer sort;

    @Schema(description = "Creator user id")
    private Long creator;

    @Schema(description = "Create time")
    private Date createDate;

    @Schema(description = "Updater user id")
    private Long updater;

    @Schema(description = "Update time")
    private Date updateDate;
}
